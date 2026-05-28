# scripts/evaluate.py
"""
GraphRAG Evaluation Script — Three-Dimension Custom Metrics
Usage: python scripts/evaluate.py [--mode graphrag] [--output data/eval_results.csv]
       python scripts/evaluate.py --mode graphrag --ablation no_phase1 --output data/eval_results_ablation_A1.csv

Ablation modes (--ablation):
  no_phase1       A1: skip exact match, go straight to vector search
  no_multihop     A2: seed node only, no multi-hop traversal
  depth_1         override all intents to depth=1
  depth_2         A3: override all intents to depth=2
  depth_3         A4: override all intents to depth=3
  depth_4         override all intents to depth=4
  depth_5         override all intents to depth=5
  no_yaml_layer3  A5: skip Neo4j required-field check in Layer 3 of YAML validation
  no_multi_entity A6c: disable multi-entity retrieval for all intents

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

# Pipeline error strings emitted by graph_agent when OpenAI/retriever/speaker fails
_PIPELINE_ERROR_MSGS = (
    "Maaf, saya tidak dapat menarik konteks dari Knowledge Graph saat ini.",
    "Terjadi error saat membuat respons.",
)
# Backoff (seconds) between per-fixture retries: attempt 1→15s, 2→30s, 3→60s
_FIXTURE_RETRY_BACKOFF = [15, 30, 60]


# ── Scope question detection keywords ────────────────────────────────────────
# Evaluate scope_accuracy only when the question explicitly asks about scope
# OR the resource is Cluster-scoped (never silently penalise Namespaced defaults).
_SCOPE_Q_KEYWORDS = [
    "scope", "scoped", "namespaced", "cluster-scoped", "cluster-wide",
    "namespace-level", "cluster-level", "lingkup", "cakupan",
    "bisa diakses lintas", "seluruh cluster", "non-namespaced",
]

# ── K8s term regex — for grounding check ─────────────────────────────────────
# Only matches compound CamelCase K8s types (2+ PascalCase segments, e.g. DeploymentSpec)
# or well-known single-word K8s resources, to avoid matching Indonesian sentence starters.
_K8S_TERM_RE = re.compile(
    r'\b(?:'
    r'[A-Z][a-z]+(?:[A-Z][a-zA-Z]+)+'
    r'|Deployment|StatefulSet|DaemonSet|ReplicaSet|CronJob|Ingress'
    r'|ConfigMap|Secret|Namespace|ServiceAccount|Endpoints|Pod|Service'
    r'|Node|ResourceQuota|LimitRange|NetworkPolicy|StorageClass'
    r'|Role|ClusterRole|RoleBinding|ClusterRoleBinding'
    r'|HorizontalPodAutoscaler|PersistentVolume|PersistentVolumeClaim'
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
    ablation_mode: str | None = None,
) -> dict:
    """
    Answer Quality metrics.

    Sub-metrics:
      syntactic_validity  — (yaml_gen only) does extracted YAML parse cleanly?
      schema_compliance   — (yaml_gen only) does YAML pass kubernetes-validate?
      answer_relevance    — cosine similarity vs ground truth answer (fallback: token F1)
      faithfulness        — fraction of expected nodes referenced in the answer
      layer3_compliance   — (yaml_gen, ablation runs only) Neo4j required-field check;
                            None for production (ablation_mode=None) and for A5 ablation
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

    # Faithfulness — fraction of key nodes referenced in the answer.
    # Uses key_nodes (original hand-curated nodes) when available, else relevant_nodes.
    # This avoids faithfulness being diluted by the expanded retrieval_nodes list.
    # Handles plural forms (Pod → pods, Namespace → namespaces) common in Indonesian answers.
    def _node_matches(node: str, answer_lower: str) -> bool:
        nl = node.lower()
        return nl in answer_lower or nl + "s" in answer_lower or nl + "es" in answer_lower

    faith_source = ground_truth.get("key_nodes") or ground_truth.get("relevant_nodes", [])
    gt_nodes = [n.split(".")[-1] for n in faith_source]
    hit = sum(1 for n in gt_nodes if _node_matches(n, answer.lower()))
    scores["faithfulness"] = hit / len(gt_nodes) if gt_nodes else 1.0

    # Layer 3 compliance — Neo4j required-field check (ablation study only)
    # Included for all ablation modes EXCEPT no_yaml_layer3 (A5) and production (None).
    # This lets us measure how much L3 contributes to YAML answer quality.
    if fixture_type == "yaml_gen" and ablation_mode is not None and ablation_mode != "no_yaml_layer3":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml as _yaml
            _data = _yaml.safe_load(yaml_candidate)
            if isinstance(_data, dict):
                from src.validation.yaml_validator import YAMLValidator
                _kind = _data.get("kind", "")
                _vresult = YAMLValidator().validate(yaml_candidate, _kind)
                if _vresult["syntax_errors"]:
                    scores["layer3_compliance"] = None  # L1 failed, L3 never ran
                else:
                    scores["layer3_compliance"] = 1.0 if not _vresult["missing_fields"] else 0.0
            else:
                scores["layer3_compliance"] = None
        except Exception:
            scores["layer3_compliance"] = None
    else:
        scores["layer3_compliance"] = None  # N/A: production run, A5, or non-yaml_gen

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
    cgg_mode: bool = False,
) -> dict:
    """
    Reasoning Quality metrics.

    Sub-metrics:
      hop_accuracy         — how many expected path hops were actually traversed
      multi_hop_success    — did multi-hop questions produce a traversal?
      scope_accuracy       — conditional: only scored when question asks about scope
                             OR resource is Cluster-scoped
      grounding_score      — 1 - hallucination_rate.
                             Normal mode: checked against global K8s vocab from Neo4j.
                             CGG mode (cgg_mode=True): checked against this query's
                             graph_context only — stricter, penalises terms not retrieved.
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
    if cgg_mode:
        # CGG mode: check terms against this query's graph_context only.
        # Stricter — terms not present in retrieved context count as hallucinations.
        from src.validation.cgg_validator import cgg_grounding_score
        grounding_score, hallucination_rate = cgg_grounding_score(answer, graph_context)
    else:
        # Normal mode: check against canonical K8s vocab from Neo4j (global).
        answer_terms = set(t.lower() for t in _K8S_TERM_RE.findall(answer))
        if answer_terms:
            if k8s_vocabulary:
                grounded = sum(1 for t in answer_terms if t in k8s_vocabulary)
            else:
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


def _check_openai_health() -> None:
    """Ping OpenAI API before evaluation starts. Aborts if unreachable."""
    import os
    from openai import OpenAI, APIConnectionError, APIStatusError
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), timeout=10)
        client.models.list()
        logger.info("[HealthCheck] OpenAI API reachable ✓")
    except APIConnectionError as e:
        logger.error(f"[HealthCheck] OpenAI API tidak dapat dijangkau: {e}")
        sys.exit("[ERROR] Evaluasi dibatalkan — OpenAI API tidak tersedia. Coba lagi setelah koneksi pulih.")
    except APIStatusError as e:
        logger.error(f"[HealthCheck] OpenAI API error {e.status_code}: {e.message}")
        sys.exit(f"[ERROR] Evaluasi dibatalkan — OpenAI mengembalikan status {e.status_code}.")
    except Exception as e:
        logger.error(f"[HealthCheck] OpenAI health check gagal: {e}")
        sys.exit(f"[ERROR] Evaluasi dibatalkan — tidak dapat memverifikasi OpenAI API: {e}")


def run_evaluation(mode: str = "graphrag", output_path: Path = DEFAULT_OUTPUT, ablation_mode: str | None = None, cgg_mode: bool = False):
    from langchain_openai import OpenAIEmbeddings

    # ── Mode-specific invoker ─────────────────────────────────────────────────
    if mode == "graphrag":
        from src.chatbot.graph_agent import create_agent_graph
        _agent = create_agent_graph(ablation_mode=ablation_mode)
        def invoke_mode(question, session_id):
            result = _agent.invoke({
                "question": question, "session_id": session_id,
                "messages": [], "chat_history": "",
                "extracted_intent": {}, "graph_context": "",
                "reasoning_path": [], "intent_type": None, "error": None,
            })
            answer = result["messages"][-1].content if result.get("messages") else ""
            return answer, result.get("reasoning_path") or [], result.get("graph_context") or ""

    elif mode == "vector":
        from src.graph.neo4j_client import Neo4jClient
        from src.graph.vector_index import VectorIndexManager
        from src.graph.queries import SIMPLE_GRAPH_EXPAND_QUERY
        from src.chatbot.llm_factory import get_speaker_llm
        from langchain_core.messages import HumanMessage
        _db  = Neo4jClient()
        _vec = VectorIndexManager()
        _llm = get_speaker_llm()
        def invoke_mode(question, session_id):
            embedding = _vec.generate_embedding(question)
            results   = _db.execute_query(SIMPLE_GRAPH_EXPAND_QUERY, {"embedding": embedding, "top_k": 5})
            parts = []; node_names = []; seen = set()
            for r in results:
                fn      = r.get("node.fullName", "")
                desc    = r.get("node.description", "")
                related = r.get("related.fullName", "")
                short     = fn.split(".")[-1] if fn else ""
                rel_short = related.split(".")[-1] if related else ""
                if short and short not in seen:
                    seen.add(short); node_names.append(short)
                if rel_short and rel_short not in seen:
                    seen.add(rel_short); node_names.append(rel_short)
                snippet = f"Resource: {fn}\nDescription: {desc}\n"
                if related:
                    snippet += f"Related To: {related}\n"
                parts.append(snippet)
            context = "\n---\n".join(parts)
            prompt  = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            resp    = _llm.invoke([HumanMessage(content=prompt)])
            return resp.content, node_names, context

    elif mode == "llm":
        from src.chatbot.llm_factory import get_speaker_llm
        from langchain_core.messages import HumanMessage
        _llm = get_speaker_llm()
        def invoke_mode(question, session_id):
            resp = _llm.invoke([HumanMessage(content=question)])
            return resp.content, [], ""

    else:
        raise ValueError(f"Unknown mode: {mode}")

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

    logger.info(f"Running evaluation: mode={mode}, ablation={ablation_mode}, cgg={cgg_mode}, fixtures={len(fixtures)}")

    # ── Health check ─────────────────────────────────────────────────────────
    _check_openai_health()

    # Unique run ID prevents Zep memory contamination across evaluation runs.
    # Without this, re-runs pick up memory from prior runs → wrong intent → wrong retrieval.
    import uuid as _uuid
    _run_id = _uuid.uuid4().hex[:8]
    logger.info(f"[Eval] Evaluation run ID: {_run_id}")

    # ── Checkpoint / resume ───────────────────────────────────────────────────
    # If the output CSV already has rows, skip those fixtures and append new ones.
    # To start fresh, delete the output file before running.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_ids: set = set()
    is_resuming = output_path.exists() and output_path.stat().st_size > 0

    summary = {"ansq": [], "retq": [], "reaq": [], "total": []}
    ansq_subs = {"syntactic_validity": [], "schema_compliance": [], "answer_relevance": [], "faithfulness": [], "layer3_compliance": []}
    retq_subs = {"precision_at_k": [], "recall_at_k": [], "f1_at_k": [], "graph_coverage": [], "ndcg_at_k": [], "edge_coverage": []}
    reaq_subs = {"hop_accuracy": [], "multi_hop_success": [], "scope_accuracy": [], "hallucination_rate": [], "grounding_score": []}
    type_data: dict = {}

    if is_resuming:
        with open(output_path, newline="", encoding="utf-8") as _f:
            for _row in csv.DictReader(_f):
                _id = _row["id"]
                completed_ids.add(_id)
                def _fv(col, r=_row):
                    v = r.get(col, "")
                    return float(v) if v else None
                _a = _fv("ansq_ansq_score"); _r = _fv("retq_retq_score")
                _q = _fv("reaq_reaq_score"); _t = _fv("total_score")
                if _a is not None: summary["ansq"].append(_a)
                if _r is not None: summary["retq"].append(_r)
                if _q is not None: summary["reaq"].append(_q)
                if _t is not None: summary["total"].append(_t)
                for k in ansq_subs:
                    v = _fv(f"ansq_{k}")
                    if v is not None: ansq_subs[k].append(v)
                for k in retq_subs:
                    v = _fv(f"retq_{k}")
                    if v is not None: retq_subs[k].append(v)
                for k in reaq_subs:
                    v = _fv(f"reaq_{k}")
                    if v is not None: reaq_subs[k].append(v)
                _t2 = _row.get("type", "")
                if _t2:
                    if _t2 not in type_data:
                        type_data[_t2] = {"ansq": [], "retq": [], "reaq": [], "total": []}
                    if _a is not None: type_data[_t2]["ansq"].append(_a)
                    if _r is not None: type_data[_t2]["retq"].append(_r)
                    if _q is not None: type_data[_t2]["reaq"].append(_q)
                    if _t is not None: type_data[_t2]["total"].append(_t)
        logger.info(f"[Resume] {len(completed_ids)} fixtures already done — skipping them")

    # ─────────────────────────────────────────────────────────────────────────
    rows = []
    # Inter-fixture delay (seconds) to stay under Groq free-tier TPM (6,000/min)
    INTER_FIXTURE_DELAY = 3
    _invoked_at_least_once = False

    # CSV writer: append if resuming, write (with header) if fresh
    _csv_file = open(output_path, "a" if is_resuming else "w", newline="", encoding="utf-8")
    _fieldnames_written = is_resuming  # header already present when resuming

    for i, fpath in enumerate(fixtures):
        data = json.loads(fpath.read_text(encoding="utf-8"))

        if data["id"] in completed_ids:
            logger.info(f"  [SKIP {i+1}/{len(fixtures)}] {data['id']} (already completed)")
            continue

        if _invoked_at_least_once:
            time.sleep(INTER_FIXTURE_DELAY)

        fixture_type  = data["type"]
        ground_truth  = data["ground_truth"]
        question      = _strip_html(data["question"]) if fixture_type == "realworld" else data["question"]

        logger.info(f"  [{i+1}/{len(fixtures)}] [{fixture_type}] {data['id']}: {question[:60]}...")

        # For followup fixtures: pre-run context_question in same session to seed conversation memory
        _session_id = f"eval_{_run_id}_{data['id']}"
        context_question = data.get("context_question")
        if context_question:
            logger.info(f"    [context] pre-running: {context_question[:80]}...")
            try:
                invoke_mode(context_question, _session_id)
                time.sleep(1)
            except Exception as _ctx_err:
                logger.warning(f"    [context] pre-run failed (non-fatal): {_ctx_err}")

        # Per-fixture retry: if the pipeline returns an error message, wait and retry
        answer = reasoning_path = graph_context = None
        for _attempt in range(len(_FIXTURE_RETRY_BACKOFF) + 1):
            answer, reasoning_path, graph_context = invoke_mode(question, _session_id)
            _invoked_at_least_once = True
            if not any(m in answer for m in _PIPELINE_ERROR_MSGS):
                break
            if _attempt < len(_FIXTURE_RETRY_BACKOFF):
                _wait = _FIXTURE_RETRY_BACKOFF[_attempt]
                logger.warning(
                    f"  [RETRY {_attempt+1}/{len(_FIXTURE_RETRY_BACKOFF)}] {data['id']} returned pipeline error. "
                    f"Waiting {_wait}s before retry..."
                )
                time.sleep(_wait)
            else:
                _csv_file.close()
                sys.exit(
                    f"[ERROR] Evaluasi dihentikan — fixture '{data['id']}' mengembalikan pipeline error "
                    f"setelah {len(_FIXTURE_RETRY_BACKOFF)} retry. "
                    f"Periksa koneksi OpenAI, lalu jalankan ulang — progress tersimpan, evaluasi akan lanjut dari fixture ini."
                )

        fixture_scope  = data.get("scope", "")

        ansq = compute_ansq(answer, ground_truth, fixture_type, embedder=embedder, ablation_mode=ablation_mode)
        retq = compute_retq(reasoning_path, ground_truth)
        reaq = compute_reaq(
            reasoning_path, answer, ground_truth, fixture_type,
            graph_context=graph_context,
            fixture_scope=fixture_scope,
            question=question,
            k8s_vocabulary=k8s_vocabulary,
            cgg_mode=cgg_mode,
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

        # ── Checkpoint: write row immediately so progress survives interruption ──
        if not _fieldnames_written:
            _writer = csv.DictWriter(_csv_file, fieldnames=list(row.keys()))
            _writer.writeheader()
            _fieldnames_written = True
        else:
            _writer = csv.DictWriter(_csv_file, fieldnames=list(row.keys()))
        _writer.writerow(row)
        _csv_file.flush()

    _csv_file.close()

    # ── Print summary ─────────────────────────────────────────────────────────
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    W   = 60

    sys.stdout.reconfigure(encoding="utf-8")

    print()
    print("=" * W)
    _abl_label = f"  ablation: {ablation_mode}" if ablation_mode else ""
    _cgg_label = "  cgg: ON" if cgg_mode else ""
    print(f"  Evaluation Results  |  mode: {mode}{_abl_label}{_cgg_label}  |  {len(summary['total'])} questions")
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
    _ABLATION_CHOICES = [
        "no_phase1", "no_multihop",
        "depth_1", "depth_2", "depth_3", "depth_4", "depth_5",
        "no_yaml_layer3", "no_multi_entity",
    ]
    parser = argparse.ArgumentParser(description="GraphRAG Evaluation")
    parser.add_argument("--mode",     default="graphrag", choices=["graphrag", "vector", "llm"])
    parser.add_argument("--output",   default=str(DEFAULT_OUTPUT))
    parser.add_argument("--ablation", default=None, choices=_ABLATION_CHOICES,
                        help="Ablation mode for the graphrag pipeline. "
                             "depth_N overrides traversal depth for ALL intents. "
                             "Only meaningful with --mode graphrag.")
    parser.add_argument("--cgg", action="store_true", default=False,
                        help="Enable CGG mode: grounding_score checked against retrieved "
                             "graph_context (strict) instead of global K8s vocabulary.")
    args = parser.parse_args()
    run_evaluation(mode=args.mode, output_path=Path(args.output), ablation_mode=args.ablation, cgg_mode=args.cgg)
