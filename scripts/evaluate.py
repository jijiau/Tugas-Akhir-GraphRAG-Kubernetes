# scripts/evaluate.py
"""
GraphRAG Evaluation Script — Three-Dimension Custom Metrics
Usage: python scripts/evaluate.py [--mode graphrag] [--output data/eval_results.csv]

Dimensions:
  AnsQ (40%): Answer Quality  — syntactic validity, schema compliance, faithfulness, answer relevance
  RetQ (35%): Retrieval Quality — precision@k, recall@k, F1@k, graph coverage, NDCG@k, edge_coverage
  ReaQ (25%): Reasoning Quality — hop accuracy, multi-hop success rate, scope accuracy, grounding score
"""
import sys
import os
import re
import time
import json
import csv
import math
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "data" / "eval_results.csv"

ANSQ_WEIGHT = 0.40
RETQ_WEIGHT = 0.35
REAQ_WEIGHT = 0.25


# ── Scope question detection keywords ────────────────────────────────────────
# Evaluate scope_accuracy only when the question explicitly asks about scope
# OR the resource is Cluster-scoped (never silently penalise Namespaced defaults).
_SCOPE_Q_KEYWORDS = [
    "scope", "scoped", "namespaced", "cluster-scoped", "cluster-wide",
    "namespace-level", "cluster-level", "lingkup", "cakupan",
    "bisa diakses lintas", "seluruh cluster", "non-namespaced",
]

# ── K8s term regex — for grounding check ─────────────────────────────────────
_K8S_TERM_RE = re.compile(
    r'\b(?:'
    r'[A-Z][a-zA-Z]+(?:Spec|List|Status|Config|Policy|Rule|Set|Map|Ref|Claim)?'
    r'|apiVersion|kubectl|namespace[sd]?|pod[sd]?|deployment[sd]?|service[sd]?'
    r'|configmap[sd]?|secret[sd]?|ingress(?:es)?|statefulset[sd]?|daemonset[sd]?'
    r'|replicaset[sd]?|cronjob[sd]?|job[sd]?|persistentvolume(?:claim)?[sd]?'
    r'|clusterrole(?:binding)?[sd]?|rolebinding[sd]?|serviceaccount[sd]?'
    r'|networkpolicy|hpa|pvc|pv|rbac'
    r')\b'
)


# ── Metric helpers ────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags from realworld SO questions so the LLM sees clean text."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _token_f1(pred: str, gold: str) -> float:
    pred_tokens = set(pred.lower().split())
    gold_tokens = set(gold.lower().split())
    if not pred_tokens or not gold_tokens:
        return 0.0
    intersection = pred_tokens & gold_tokens
    precision = len(intersection) / len(pred_tokens)
    recall    = len(intersection) / len(gold_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _cosine_similarity(embedder, text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts using the provided embedder."""
    try:
        emb_a = embedder.embed_query(text_a)
        emb_b = embedder.embed_query(text_b)
        dot       = sum(a * b for a, b in zip(emb_a, emb_b))
        norm_a    = sum(a ** 2 for a in emb_a) ** 0.5
        norm_b    = sum(b ** 2 for b in emb_b) ** 0.5
        return dot / (norm_a * norm_b) if norm_a * norm_b > 0 else 0.0
    except Exception as e:
        logger.warning(f"Cosine similarity failed, falling back to token F1: {e}")
        return _token_f1(text_a, text_b)


def _effective_type(fixture_type: str, ground_truth: dict) -> str:
    """
    Map the 'realworld' meta-type to a concrete sub-type for metric purposes.
    """
    if fixture_type != "realworld":
        return fixture_type
    answer_text = ground_truth.get("answer", "")
    if "apiVersion:" in answer_text or "expected_yaml_keys" in ground_truth and ground_truth["expected_yaml_keys"]:
        return "yaml_gen"
    return "conceptual"


def _extract_yaml_block(text: str) -> str:
    """
    Extract YAML content from an LLM response.

    Strategy (in order):
      1. Fenced code block with yaml/yml/YML/YAML label or no label
      2. Inline YAML: first occurrence of a line starting with 'apiVersion:'
    """
    match = re.search(r"```(?:ya?ml?|YA?ML?)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    inline = re.search(r"(apiVersion:.*)", text, re.DOTALL)
    if inline:
        candidate = inline.group(1)
        yaml_lines = []
        for line in candidate.splitlines():
            if yaml_lines and line and not line[0].isspace() and ":" not in line and not line.startswith("-"):
                break
            yaml_lines.append(line)
        return "\n".join(yaml_lines).strip()

    return text.strip()


def compute_ansq(
    answer: str,
    ground_truth: dict,
    fixture_type: str,
    embedder=None,
) -> dict:
    """
    Answer Quality metrics.

    Sub-metrics:
      syntactic_validity  — (yaml_gen only) does extracted YAML parse cleanly?
      schema_compliance   — (yaml_gen only) does YAML pass kubernetes-validate?
      answer_relevance    — cosine similarity vs ground truth answer (fallback: token F1)
      faithfulness        — fraction of expected nodes referenced in the answer
    """
    scores = {}

    # Resolve realworld -> concrete sub-type
    fixture_type = _effective_type(fixture_type, ground_truth)

    # Syntactic Validity (yaml_gen only)
    if fixture_type == "yaml_gen":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml
            yaml.safe_load(yaml_candidate)
            scores["syntactic_validity"] = 1.0
        except Exception:
            scores["syntactic_validity"] = 0.0
    else:
        scores["syntactic_validity"] = None  # N/A

    # Schema Compliance (yaml_gen only) — requires kubernetes-validate
    if fixture_type == "yaml_gen":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml
            import kubernetes_validate
            data = yaml.safe_load(yaml_candidate)
            if isinstance(data, dict):
                kubernetes_validate.validate(data, "1.29", strict=False)
                scores["schema_compliance"] = 1.0
            else:
                scores["schema_compliance"] = 0.0
        except ImportError:
            scores["schema_compliance"] = None
        except Exception:
            scores["schema_compliance"] = 0.0
    else:
        scores["schema_compliance"] = None

    # Answer Relevance — cosine similarity (preferred) or token F1 fallback
    gt_answer = ground_truth.get("answer", "")
    if embedder is not None and gt_answer:
        scores["answer_relevance"] = _cosine_similarity(embedder, answer, gt_answer)
    else:
        scores["answer_relevance"] = _token_f1(answer, gt_answer)

    # Faithfulness — fraction of expected nodes referenced in the answer
    gt_nodes = [n.split(".")[-1] for n in ground_truth.get("relevant_nodes", [])]
    hit = sum(1 for n in gt_nodes if n.lower() in answer.lower())
    scores["faithfulness"] = hit / len(gt_nodes) if gt_nodes else 1.0

    applicable = [v for v in scores.values() if v is not None]
    scores["ansq_score"] = sum(applicable) / len(applicable) if applicable else 0.0
    return scores


def compute_retq(reasoning_path: list, ground_truth: dict) -> dict:
    """
    Retrieval Quality metrics.

    Sub-metrics (all contribute equally to retq_score):
      precision_at_k  — fraction of retrieved nodes that are relevant
      recall_at_k     — fraction of relevant nodes that were retrieved
      f1_at_k         — harmonic mean of precision and recall
      graph_coverage  — fraction of expected path SOURCE-nodes matched
      ndcg_at_k       — ranking quality: relevant nodes retrieved earlier = better
      edge_coverage   — fraction of expected edges present in reasoning_path
    """
    _RELATION_RE = re.compile(r"-\[([^\]]+)\]->?")

    def _node_tokens(step: str) -> list:
        cleaned = _RELATION_RE.sub(" ", step)
        return [t for t in cleaned.split() if t]

    expected_nodes = set(n.split(".")[-1] for n in ground_truth.get("relevant_nodes", []))
    retrieved_nodes = []
    seen_nodes = set()
    for step in reasoning_path:
        for tok in _node_tokens(step):
            if tok not in seen_nodes:
                seen_nodes.add(tok)
                retrieved_nodes.append(tok)
    retrieved_set = set(retrieved_nodes)

    intersection = retrieved_set & expected_nodes
    precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
    recall    = len(intersection) / len(expected_nodes) if expected_nodes else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Graph coverage (source-node matching on expected path)
    expected_path = ground_truth.get("expected_path", [])
    graph_coverage = (
        len([p for p in expected_path
             if any(p.split(" -[")[0] in step for step in reasoning_path)])
        / len(expected_path)
        if expected_path else 1.0
    )

    # NDCG@k
    k = len(retrieved_nodes)
    dcg = sum(
        (1.0 / math.log2(i + 2))
        for i, node in enumerate(retrieved_nodes)
        if node in expected_nodes
    )
    ideal_hits = min(len(expected_nodes), k) if k > 0 else 0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    ndcg_at_k = dcg / idcg if idcg > 0 else (1.0 if not expected_nodes else 0.0)

    # Edge coverage
    if expected_path:
        matched_edges = sum(
            1 for ep in expected_path
            if any(ep in step or step in ep for step in reasoning_path)
        )
        edge_coverage = matched_edges / len(expected_path)
    else:
        edge_coverage = 1.0

    retq_score = (precision + recall + f1 + graph_coverage + ndcg_at_k + edge_coverage) / 6

    return {
        "precision_at_k": precision,
        "recall_at_k": recall,
        "f1_at_k": f1,
        "graph_coverage": graph_coverage,
        "ndcg_at_k": ndcg_at_k,
        "edge_coverage": edge_coverage,
        "retq_score": retq_score,
    }


def compute_reaq(
    reasoning_path: list,
    answer: str,
    ground_truth: dict,
    fixture_type: str,
    graph_context: str = "",
    fixture_scope: str = "",
    question: str = "",
    k8s_vocabulary: set = None,
) -> dict:
    """
    Reasoning Quality metrics.

    Sub-metrics:
      hop_accuracy         — how many expected path hops were actually traversed
      multi_hop_success    — did multi-hop questions produce a traversal?
      scope_accuracy       — conditional: only scored when question asks about scope
                             OR resource is Cluster-scoped
      grounding_score      — 1 - hallucination_rate; uses canonical K8s vocab from
                             Neo4j (not raw graph_context JSON) for better calibration
    """
    fixture_type  = _effective_type(fixture_type, ground_truth)
    expected_path = ground_truth.get("expected_path", [])
    multi_hop     = ground_truth.get("multi_hop", False)

    # ── Hop Accuracy ──────────────────────────────────────────────────────────
    if expected_path and multi_hop:
        matched = sum(
            1 for ep in expected_path
            if any(ep.split(" -[")[0] in step for step in reasoning_path)
        )
        hop_accuracy = matched / len(expected_path)
    else:
        hop_accuracy = 1.0 if reasoning_path else 0.0

    # ── Multi-hop Success ─────────────────────────────────────────────────────
    multi_hop_success = 1.0 if (multi_hop and reasoning_path) or (not multi_hop) else 0.0

    # ── Scope Accuracy — Conditional ──────────────────────────────────────────
    # Only evaluate scope when:
    #   a) the question explicitly asks about resource scope, OR
    #   b) the resource is Cluster-scoped (non-default; more likely to be tested)
    # For Namespaced resources where scope is not asked, score = 1.0 (not penalised).
    question_lower = question.lower()
    scope_relevant = (
        any(kw in question_lower for kw in _SCOPE_Q_KEYWORDS)
        or fixture_scope == "Cluster"
    )

    if not scope_relevant:
        scope_accuracy = 1.0  # conditional skip — not evaluated
    else:
        _NAMESPACED_POSITIVE = ["namespaced", "dalam namespace", "di namespace",
                                 "namespace-scoped", "namespace tertentu"]
        _NAMESPACED_NEGATIVE = ["cluster-scoped", "cluster-wide", "seluruh cluster",
                                 "tidak terikat namespace", "non-namespaced"]
        _CLUSTER_POSITIVE    = ["cluster-scoped", "cluster-wide", "seluruh cluster",
                                 "tidak terikat namespace", "non-namespaced",
                                 "lintas namespace"]
        _CLUSTER_NEGATIVE    = ["namespaced", "dalam namespace", "namespace-scoped"]

        answer_lower = answer.lower()

        if fixture_scope == "Namespaced":
            correct_hit = any(kw in answer_lower for kw in _NAMESPACED_POSITIVE)
            wrong_hit   = any(kw in answer_lower for kw in _NAMESPACED_NEGATIVE)
            if correct_hit and not wrong_hit:
                scope_accuracy = 1.0
            elif wrong_hit:
                scope_accuracy = 0.0
            else:
                scope_accuracy = 0.5   # silent on scope
        elif fixture_scope == "Cluster":
            correct_hit = any(kw in answer_lower for kw in _CLUSTER_POSITIVE)
            wrong_hit   = any(kw in answer_lower for kw in _CLUSTER_NEGATIVE)
            if correct_hit and not wrong_hit:
                scope_accuracy = 1.0
            elif wrong_hit:
                scope_accuracy = 0.0
            else:
                scope_accuracy = 0.5
        else:
            scope_accuracy = 1.0  # no scope expectation

    # ── Hallucination Rate — K8s Vocabulary Grounding ─────────────────────────
    # Extract K8s API terms from the answer, then check how many appear in the
    # canonical vocabulary loaded from Neo4j (all Definition node names).
    # This avoids false positives from matching against graph_context JSON structure.
    answer_terms = set(t.lower() for t in _K8S_TERM_RE.findall(answer))

    if answer_terms:
        if k8s_vocabulary:
            grounded = sum(1 for t in answer_terms if t in k8s_vocabulary)
        else:
            # Fallback: match against graph_context text
            ctx_lower = graph_context.lower()
            grounded  = sum(1 for t in answer_terms if t in ctx_lower)
        hallucination_rate = 1.0 - grounded / len(answer_terms)
    else:
        hallucination_rate = 0.0

    grounding_score = 1.0 - hallucination_rate
    reaq_score = (hop_accuracy + multi_hop_success + scope_accuracy + grounding_score) / 4

    return {
        "hop_accuracy":       hop_accuracy,
        "multi_hop_success":  multi_hop_success,
        "scope_accuracy":     scope_accuracy,
        "hallucination_rate": hallucination_rate,
        "grounding_score":    grounding_score,
        "reaq_score":         reaq_score,
    }


# ── Runner ────────────────────────────────────────────────────────────────────

def _load_k8s_vocabulary() -> set:
    """
    Load all canonical K8s Definition node names from Neo4j.
    Returns a lowercase set used for hallucination grounding checks.
    Falls back to empty set if Neo4j is unreachable.
    """
    try:
        from src.graph.neo4j_client import Neo4jClient
        db   = Neo4jClient()
        rows = db.execute_query("MATCH (d:Definition) RETURN d.name AS name", {})
        vocab = set()
        for row in rows:
            name = row.get("name", "")
            if name:
                vocab.add(name.lower())
                # Also add just the last segment (e.g. "io.k8s.api.apps.v1.Deployment" -> "deployment")
                vocab.add(name.split(".")[-1].lower())
        logger.info(f"[Vocab] Loaded {len(vocab)} canonical K8s terms from Neo4j")
        return vocab
    except Exception as e:
        logger.warning(f"[Vocab] Could not load K8s vocabulary from Neo4j: {e}")
        return set()


def run_evaluation(mode: str = "graphrag", output_path: Path = DEFAULT_OUTPUT):
    from src.chatbot.graph_agent import create_agent_graph
    from langchain_openai import OpenAIEmbeddings

    agent = create_agent_graph()

    # ── One-time initialization ───────────────────────────────────────────────
    # Embedder for AnsQ cosine similarity
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        logger.info("[Eval] OpenAI embedder initialized for cosine similarity")
    except Exception as e:
        embedder = None
        logger.warning(f"[Eval] Could not initialize embedder, falling back to token F1: {e}")

    # K8s vocabulary for hallucination grounding
    k8s_vocabulary = _load_k8s_vocabulary()

    # Load fixtures; for realworld type apply same scoring gate as conftest.py
    _all = sorted(FIXTURES_DIR.rglob("*.json"))
    fixtures = []
    for p in _all:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("type") == "realworld":
            if not ("selection_scores_breakdown" in d and d.get("selection_score", 0) >= 2.0):
                continue
        fixtures.append(p)

    if not fixtures:
        logger.error(f"No fixtures found in {FIXTURES_DIR}")
        sys.exit(1)

    logger.info(f"Running evaluation: mode={mode}, fixtures={len(fixtures)}")

    rows = []
    summary = {"ansq": [], "retq": [], "reaq": [], "total": []}

    # Sub-metric accumulators for detailed CLI output
    ansq_subs = {"syntactic_validity": [], "schema_compliance": [], "answer_relevance": [], "faithfulness": []}
    retq_subs = {"precision_at_k": [], "recall_at_k": [], "f1_at_k": [], "graph_coverage": [], "ndcg_at_k": [], "edge_coverage": []}
    reaq_subs = {"hop_accuracy": [], "multi_hop_success": [], "scope_accuracy": [], "hallucination_rate": [], "grounding_score": []}

    # Per-type sub-metric accumulators
    type_data: dict = {}   # type -> {ansq_score: [], retq_score: [], reaq_score: [], total: []}

    # Inter-fixture delay (seconds) to stay under Groq free-tier TPM (6,000/min)
    INTER_FIXTURE_DELAY = 3

    for i, fpath in enumerate(fixtures):
        if i > 0:
            time.sleep(INTER_FIXTURE_DELAY)

        data          = json.loads(fpath.read_text(encoding="utf-8"))
        fixture_type  = data["type"]
        ground_truth  = data["ground_truth"]
        question      = _strip_html(data["question"]) if fixture_type == "realworld" else data["question"]

        logger.info(f"  [{i+1}/{len(fixtures)}] [{fixture_type}] {data['id']}: {question[:60]}...")

        result = agent.invoke({
            "question":        question,
            "session_id":      f"eval_{data['id']}",
            "messages":        [],
            "chat_history":    "",
            "extracted_intent": {},
            "graph_context":   "",
            "reasoning_path":  [],
            "intent_type":     None,
            "error":           None,
        })

        answer         = result["messages"][-1].content if result.get("messages") else ""
        reasoning_path = result.get("reasoning_path") or []
        graph_context  = result.get("graph_context") or ""
        fixture_scope  = data.get("scope", "")

        ansq = compute_ansq(answer, ground_truth, fixture_type, embedder=embedder)
        retq = compute_retq(reasoning_path, ground_truth)
        reaq = compute_reaq(
            reasoning_path, answer, ground_truth, fixture_type,
            graph_context=graph_context,
            fixture_scope=fixture_scope,
            question=question,
            k8s_vocabulary=k8s_vocabulary,
        )

        total = (
            ansq["ansq_score"] * ANSQ_WEIGHT
            + retq["retq_score"] * RETQ_WEIGHT
            + reaq["reaq_score"] * REAQ_WEIGHT
        )

        row = {
            "id":             data["id"],
            "type":           fixture_type,
            "multi_hop":      data.get("multi_hop", False),
            "mode":           mode,
            "answer_preview": answer[:100].replace("\n", " "),
            "hops_retrieved": len(reasoning_path),
            **{f"ansq_{k}": v for k, v in ansq.items()},
            **{f"retq_{k}": v for k, v in retq.items()},
            **{f"reaq_{k}": v for k, v in reaq.items()},
            "total_score":    round(total, 4),
        }
        rows.append(row)

        summary["ansq"].append(ansq["ansq_score"])
        summary["retq"].append(retq["retq_score"])
        summary["reaq"].append(reaq["reaq_score"])
        summary["total"].append(total)

        # Accumulate sub-metrics (skip None values)
        for k in ansq_subs:
            v = ansq.get(k)
            if v is not None:
                ansq_subs[k].append(v)
        for k in retq_subs:
            v = retq.get(k)
            if v is not None:
                retq_subs[k].append(v)
        for k in reaq_subs:
            v = reaq.get(k)
            if v is not None:
                reaq_subs[k].append(v)

        # Per-type accumulation
        t = fixture_type
        if t not in type_data:
            type_data[t] = {"ansq": [], "retq": [], "reaq": [], "total": []}
        type_data[t]["ansq"].append(ansq["ansq_score"])
        type_data[t]["retq"].append(retq["retq_score"])
        type_data[t]["reaq"].append(reaq["reaq_score"])
        type_data[t]["total"].append(total)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Print summary ─────────────────────────────────────────────────────────
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    W   = 60

    sys.stdout.reconfigure(encoding="utf-8")

    print()
    print("=" * W)
    print(f"  Evaluation Results  |  mode: {mode}  |  {len(rows)} questions")
    print("=" * W)
    print(f"  AnsQ (Answer Quality)    : {avg(summary['ansq']):.4f}  [weight 40%]")
    print(f"  RetQ (Retrieval Quality) : {avg(summary['retq']):.4f}  [weight 35%]")
    print(f"  ReaQ (Reasoning Quality) : {avg(summary['reaq']):.4f}  [weight 25%]")
    print(f"  {'-'*44}")
    print(f"  Weighted Total           : {avg(summary['total']):.4f}")

    # ── Sub-metric breakdown ──────────────────────────────────────────────────
    print()
    print("  AnsQ sub-metrics:")
    for k, vals in ansq_subs.items():
        label = f"    {k:<26}"
        print(f"{label}: {avg(vals):.4f}  (n={len(vals)})")

    print()
    print("  RetQ sub-metrics:")
    for k, vals in retq_subs.items():
        label = f"    {k:<26}"
        print(f"{label}: {avg(vals):.4f}  (n={len(vals)})")

    print()
    print("  ReaQ sub-metrics:")
    for k, vals in reaq_subs.items():
        label = f"    {k:<26}"
        print(f"{label}: {avg(vals):.4f}  (n={len(vals)})")

    # ── Per question-type breakdown ───────────────────────────────────────────
    print()
    print("  Per question-type breakdown:")
    print(f"  {'Type':<22} {'Total':>7}  {'AnsQ':>7}  {'RetQ':>7}  {'ReaQ':>7}  {'N':>4}")
    print(f"  {'-'*58}")
    for t in sorted(type_data):
        td = type_data[t]
        print(
            f"  {t:<22} {avg(td['total']):>7.4f}"
            f"  {avg(td['ansq']):>7.4f}"
            f"  {avg(td['retq']):>7.4f}"
            f"  {avg(td['reaq']):>7.4f}"
            f"  {len(td['total']):>4}"
        )

    print()
    print(f"  Results saved -> {output_path}")
    print("=" * W)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GraphRAG Evaluation")
    parser.add_argument("--mode",   default="graphrag", choices=["graphrag", "vector", "llm"])
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    run_evaluation(mode=args.mode, output_path=Path(args.output))
