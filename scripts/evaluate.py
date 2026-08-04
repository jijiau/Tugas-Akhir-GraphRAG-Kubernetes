# scripts/evaluate.py
"""
GraphRAG Evaluation Script — Three-Dimension Metrics (per-faktor, NO weighted total)
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
  has_property_only A7: restrict context+path traversal to HAS_PROPERTY only (isolate
                    the 18-edge semantic contribution — thesis T1, F14)

Dimensions (per-faktor, NO weighted total) — citations from literature, no invented formulas:
  AnsQ: Answer Quality    — answer_relevance (cosine similarity, es_ragas_2023),
                            syntactic_validity, schema_compliance (yaml_gen only)
  RetQ: Retrieval Quality — Precision/Recall/F1 set-based (Manning et al. 2008);
                            R = nodes on reasoning_path; applicable to Vector + GraphRAG
  ReaQ: Reasoning Quality — RAGAS Faithfulness (claim-level, es_ragas_2023);
                            computed by recompute_ragas.py and joined here; Vanilla LLM = N/A

GraphRAG-only (analisis mekanisme, BUKAN head-to-head):
  hop_accuracy     — edge-level recall: |reasoning_path ∩ expected_path| / |expected_path|
                     (Manning et al. 2008); N/A (None) for fixtures with empty expected_path
  syntactic_validity, schema_compliance — YAML quality (yaml_gen fixtures only)

Dropped metrics (documented):
  faithfulness (AnsQ node-mention fraction) — completeness, not answer quality; no citation
  path_coverage    — redundant with hop_accuracy (same GT-path recall, lenient vs strict)
  grounding_score / hallucination_rate — dropped; ReaQ = RAGAS Faithfulness (claim-level)
  rga              — arbitrary threshold 0.5 composite; no citation for threshold
  NDCG             — requires relevance ranking; GraphRAG uses depth-order only

Diagnostics (reported, NOT in any composite):
  precision, recall, f1 (RetQ components), yaml_fail_layer, intent_detected,
  n_retrieved_nodes, n_relevant_nodes, n_node_intersection, seed_node_degree, error_flag

Sidecar output:
  data/eval_cases_<mode>.jsonl  — full-text per fixture (answer, reasoning_path, graph_context,
                                   missed_edges, missed_nodes, yaml_errors)
  data/eval_run_meta_<mode>.json — run provenance (model, run_id, timestamp, git commit)
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

# Pipeline error strings emitted by graph_agent when OpenAI/retriever/speaker fails
_PIPELINE_ERROR_MSGS = (
    "Maaf, saya tidak dapat menarik konteks dari Knowledge Graph saat ini.",
    "Terjadi error saat membuat respons.",
)
# Backoff (seconds) between per-fixture retries: attempt 1→15s, 2→30s, 3→60s
_FIXTURE_RETRY_BACKOFF = [15, 30, 60]



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
    Answer Quality metrics (es_ragas_2023 for semantic similarity; OpenAPI K8s 1.30 for YAML).

    Sub-metrics:
      answer_relevance    — cosine similarity vs ground truth answer (es_ragas_2023);
                            fallback: token F1 when embedder unavailable
      syntactic_validity  — (yaml_gen only) does extracted YAML parse cleanly?
      schema_compliance   — (yaml_gen only) does YAML pass kubernetes-validate v1.30?
      layer3_compliance   — (yaml_gen, ablation runs only) Neo4j required-field check;
                            None for production (ablation_mode=None) and for A5 ablation

    Dropped: faithfulness (node-mention fraction) — measures completeness, not answer quality;
    no literature citation. Claim-level faithfulness = ReaQ (RAGAS, recompute_ragas.py).
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
                # F12: validate against K8s 1.30 — the version of the swagger
                # definitions the KG is built from (data scope). kubernetes_validate
                # bundles v1.30.0-local schemas.
                kubernetes_validate.validate(data, "1.30", strict=False)
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
    # Citation: es_ragas_2023 (Answer Semantic Similarity = cosine between embeddings)
    gt_answer = ground_truth.get("answer", "")
    if embedder is not None and gt_answer:
        scores["answer_relevance"] = _cosine_similarity(embedder, answer, gt_answer)
    else:
        scores["answer_relevance"] = _token_f1(answer, gt_answer)

    # Layer 3 compliance — Neo4j required-field check (ablation study only)
    # Included for all ablation modes EXCEPT no_yaml_layer3 (A5) and production (None).
    # This lets us measure how much L3 contributes to YAML answer quality.
    # F10 note: production AnsQ (ablation_mode=None) does NOT include L3 — the T2
    # Layer-3 claim is evidenced by the ablation runs only (disclose in thesis Bab VI).
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

    # yaml_fail_layer — which validation layer failed first (yaml_gen fixtures only).
    # Values: None (non-yaml), "none" (all passed), "syntactic", "schema", "layer3".
    if fixture_type == "yaml_gen":
        if scores.get("syntactic_validity") == 0.0:
            scores["yaml_fail_layer"] = "syntactic"
        elif scores.get("schema_compliance") == 0.0:
            scores["yaml_fail_layer"] = "schema"
        elif scores.get("layer3_compliance") == 0.0:
            scores["yaml_fail_layer"] = "layer3"
        else:
            scores["yaml_fail_layer"] = "none"
    else:
        scores["yaml_fail_layer"] = None

    return scores


def compute_retq(reasoning_path: list, ground_truth: dict, root_resource: str = "") -> dict:
    """
    Retrieval Quality metrics — set-based Precision/Recall/F1 (Manning et al. 2008).

    R = set of nodes on reasoning_path (nodes actually traversed and used).
    G = set of relevant_nodes from ground truth (curated, Fase 2).

    Formulas (Manning et al. 2008, Ch. 8):
      Precision = |R ∩ G| / |R|
      Recall    = |R ∩ G| / |G|
      F1        = 2·Precision·Recall / (Precision + Recall)

    Composite: retq_score = F1 (order-independent; same formula for Vector and GraphRAG).
    Precision and Recall are reported as components (diagnostic).
    Applicable to: Vector RAG + GraphRAG. Vanilla LLM = N/A (no retrieval).

    root_resource: canonical root node name from graph_context["RootResource"].
    Leaf resources (Secret, ConfigMap, Toleration) have no child Definition nodes →
    PATH_EDGES_QUERY returns no edges → reasoning_path=[] → R=∅ → RetQ=0 spuriously.
    Including the matched root node in R corrects this measurement bug: the root IS
    a retrieved node (it was matched and used as the basis of the answer).
    For non-empty paths the root already appears as the first parent token → no-op.

    Dropped: path_coverage (redundant with hop_accuracy — same GT-path recall objective,
    lenient vs strict); NDCG (requires relevance ranking, GraphRAG has depth ordering only).
    """
    _RELATION_RE = re.compile(r"-\[([^\]]+)\]->?")

    def _node_tokens(step: str) -> list:
        cleaned = _RELATION_RE.sub(" ", step)
        return [t for t in cleaned.split() if t]

    expected_nodes = set(n.split(".")[-1] for n in ground_truth.get("relevant_nodes", []))
    retrieved_nodes = []
    seen_nodes = set()
    # Include matched root node in R even when reasoning_path is empty (leaf resources).
    # root_resource is the node the system actually retrieved and based its answer on.
    if root_resource:
        _rs = root_resource.split(".")[-1]
        seen_nodes.add(_rs)
        retrieved_nodes.append(_rs)
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

    retq_score = f1  # set-based F1 (Manning 2008); order-independent composite

    return {
        "precision":           precision,           # component (Manning 2008)
        "recall":              recall,              # component (Manning 2008)
        "f1":                  f1,
        "retq_score":          retq_score,
        # count diagnostics
        "n_retrieved_nodes":   len(retrieved_nodes),
        "n_relevant_nodes":    len(expected_nodes),
        "n_node_intersection": len(intersection),
    }


def compute_reaq(
    reasoning_path: list,
    answer: str,
    ground_truth: dict,
    fixture_type: str,
) -> dict:
    """
    Reasoning Quality — GraphRAG-only diagnostic + ReaQ placeholder.

    hop_accuracy (GraphRAG-only diagnostic):
      edge-level recall: |reasoning_path ∩ expected_path| / |expected_path|
      Citation: recall formula (Manning et al. 2008) applied to edge sets (strict
      triplet-match). Measures whether the RIGHT edges were traversed, not a hop count.
      N/A (None) for fixtures with empty expected_path (conceptual, yaml_gen) —
      these types have no traversal path to evaluate.

    reaq_score (ReaQ composite):
      RAGAS Faithfulness (claim-level, es_ragas_2023) — computed by recompute_ragas.py
      and joined into eval_results CSV. Set to None here as placeholder.
      Vanilla LLM = N/A (no retrieved context to verify claims against).

    Dropped: grounding_score / hallucination_rate (K8s vocab fraction) — dropped because
    entity-level grounding is redundant with claim-level RAGAS Faithfulness (same objective,
    strictly weaker). Path to: recompute_ragas.py for the actual ReaQ composite.
    """
    expected_path = ground_truth.get("expected_path", [])

    # ── Hop Accuracy — edge-level recall (Manning et al. 2008) ───────────────
    # hop_accuracy = |reasoning_path ∩ expected_path| / |expected_path|
    # N/A (None) when expected_path is empty — fixture type has no GT traversal path.
    _exp_edges  = set(e.strip().lower() for e in expected_path)
    _pred_edges = set(e.strip().lower() for e in reasoning_path)
    if _exp_edges:
        hop_accuracy = len(_exp_edges & _pred_edges) / len(_exp_edges)
    else:
        hop_accuracy = None  # N/A: no GT edges (conceptual/yaml_gen) — not averaged as 1.0

    # Depth diagnostics (reported, NOT scored). gt_depth/n_roots from Fase 2 GT fixtures.
    d_gt     = len(expected_path)
    d_pred   = len(reasoning_path)
    gt_depth = ground_truth.get("gt_depth")
    n_roots  = ground_truth.get("n_roots", 1)

    return {
        "hop_accuracy":  hop_accuracy,   # GraphRAG-only diagnostic; None for path-empty
        "reaq_score":    None,           # placeholder; filled by RAGAS join (recompute_ragas.py)
        # depth diagnostics
        "depth_gt":      d_gt,
        "depth_pred":    d_pred,
        "gt_depth":      gt_depth,
        "n_roots":       n_roots,
    }



# ── Runner ────────────────────────────────────────────────────────────────────


def _get_node_degree(resource_id: str) -> int | None:
    """
    Return total degree (in+out edges) of a Definition node from Neo4j.
    Used for boundary condition analysis. Returns None if Neo4j unreachable.
    resource_id: full K8s resource ID, e.g. 'io.k8s.api.apps.v1.Deployment'
    """
    try:
        from src.graph.neo4j_client import Neo4jClient
        db  = Neo4jClient()
        res = db.execute_query(
            "MATCH (d:Definition {fullName: $name}) "
            "RETURN size([(d)-[]-() | 1]) AS degree",
            {"name": resource_id}
        )
        if res:
            return int(res[0].get("degree", 0))
        # Fallback: try by short name
        short = resource_id.split(".")[-1]
        res2 = db.execute_query(
            "MATCH (d:Definition) WHERE d.name = $short OR d.fullName ENDS WITH $short "
            "RETURN size([(d)-[]-() | 1]) AS degree LIMIT 1",
            {"short": short}
        )
        return int(res2[0].get("degree", 0)) if res2 else None
    except Exception:
        return None


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


def run_evaluation(mode: str = "graphrag", output_path: Path = DEFAULT_OUTPUT, ablation_mode: str | None = None):
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
            intent = result.get("extracted_intent") or {}
            intent_type = intent.get("intent_type") or intent.get("type") or ""
            return answer, result.get("reasoning_path") or [], result.get("graph_context") or "", intent_type

    elif mode == "vector":
        from src.graph.neo4j_client import Neo4jClient
        from src.graph.vector_index import VectorIndexManager
        from src.graph.queries import SIMPLE_VECTOR_QUERY  # F1: pure dense, no graph expansion
        from src.chatbot.llm_factory import get_speaker_llm
        from langchain_core.messages import HumanMessage
        _db  = Neo4jClient()
        _vec = VectorIndexManager()
        _llm = get_speaker_llm()
        def invoke_mode(question, session_id):
            # F1: pure dense top-k (NO 1-hop graph expansion) so the Vector baseline
            # is a fair contrast — any graph contribution is GraphRAG's alone. The old
            # SIMPLE_GRAPH_EXPAND_QUERY augmented the baseline with HAS_PROPERTY/EXTENDS/
            # CONTAINS_POD_TEMPLATE 1-hop neighbours, invalidating the comparison.
            embedding = _vec.generate_embedding(question)
            results   = _db.execute_query(SIMPLE_VECTOR_QUERY, {"embedding": embedding, "top_k": 5})
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
            return resp.content, node_names, context, ""

    elif mode == "llm":
        from src.chatbot.llm_factory import get_speaker_llm
        from langchain_core.messages import HumanMessage
        _llm = get_speaker_llm()
        def invoke_mode(question, session_id):
            resp = _llm.invoke([HumanMessage(content=question)])
            return resp.content, [], "", ""

    else:
        raise ValueError(f"Unknown mode: {mode}")

    # ── One-time initialization ───────────────────────────────────────────────
    # Embedder for AnsQ cosine similarity (es_ragas_2023)
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        logger.info("[Eval] OpenAI embedder initialized for cosine similarity")
    except Exception as e:
        embedder = None
        logger.warning(f"[Eval] Could not initialize embedder, falling back to token F1: {e}")

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

    logger.info(f"Running evaluation: mode={mode}, ablation={ablation_mode}, fixtures={len(fixtures)}")

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

    summary = {"ansq": [], "retq": []}
    ansq_subs = {"syntactic_validity": [], "schema_compliance": [], "answer_relevance": [], "layer3_compliance": []}
    retq_subs = {"precision": [], "recall": [], "f1": []}
    reaq_subs = {"hop_accuracy": []}  # diagnostic only; reaq_score comes from RAGAS join
    type_data: dict = {}
    # JSONL sidecar buffer: full-text per fixture (3 main modes only)
    _cases_buffer: list = []

    if is_resuming:
        with open(output_path, newline="", encoding="utf-8") as _f:
            for _row in csv.DictReader(_f):
                _id = _row["id"]
                completed_ids.add(_id)
                def _fv(col, r=_row):
                    v = r.get(col, "")
                    return float(v) if v else None
                _a = _fv("ansq_ansq_score")
                _r = _fv("retq_retq_score")
                if _a is not None: summary["ansq"].append(_a)
                if _r is not None: summary["retq"].append(_r)
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
                        type_data[_t2] = {"ansq": [], "retq": []}
                    if _a is not None: type_data[_t2]["ansq"].append(_a)
                    if _r is not None: type_data[_t2]["retq"].append(_r)
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
        answer = reasoning_path = graph_context = intent_detected = None
        _error_flag = 0
        for _attempt in range(len(_FIXTURE_RETRY_BACKOFF) + 1):
            answer, reasoning_path, graph_context, intent_detected = invoke_mode(question, _session_id)
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
                _error_flag = 1
                _csv_file.close()
                sys.exit(
                    f"[ERROR] Evaluasi dihentikan — fixture '{data['id']}' mengembalikan pipeline error "
                    f"setelah {len(_FIXTURE_RETRY_BACKOFF)} retry. "
                    f"Periksa koneksi OpenAI, lalu jalankan ulang — progress tersimpan, evaluasi akan lanjut dari fixture ini."
                )

        ansq = compute_ansq(answer, ground_truth, fixture_type, embedder=embedder, ablation_mode=ablation_mode)
        # Extract matched root node from graph_context for RetQ bug fix (leaf resources).
        # Single-entity: graph_context is valid JSON with "RootResource" key.
        # Multi-entity or error strings: json.loads fails → _root_resource="" → no-op.
        _root_resource = ""
        try:
            _gc = json.loads(graph_context) if graph_context else {}
            if isinstance(_gc, dict):
                _root_resource = _gc.get("RootResource", "")
        except Exception:
            _root_resource = ""
        retq = compute_retq(reasoning_path, ground_truth, root_resource=_root_resource)
        reaq = compute_reaq(reasoning_path, answer, ground_truth, fixture_type)

        # ── Diagnostic fields ─────────────────────────────────────────────────
        primary_resource = (ground_truth.get("relevant_nodes") or [""])[0]
        seed_degree = _get_node_degree(primary_resource) if primary_resource else None

        # missed edges / nodes for JSONL sidecar
        expected_path  = ground_truth.get("expected_path", [])
        expected_nodes = set(n.split(".")[-1] for n in ground_truth.get("relevant_nodes", []))
        import re as _re
        _rel_re = _re.compile(r"-\[([^\]]+)\]->?")
        retrieved_toks = set()
        for step in reasoning_path:
            for tok in [t for t in _rel_re.sub(" ", step).split() if t]:
                retrieved_toks.add(tok)
        missed_nodes = list(expected_nodes - retrieved_toks)
        missed_edges = [ep for ep in expected_path
                        if not any(ep in step or ep.split(" -[")[0] in step for step in reasoning_path)]

        yaml_errors: list = []
        if _effective_type(fixture_type, ground_truth) == "yaml_gen" and ansq.get("yaml_fail_layer") not in (None, "none"):
            import yaml as _yaml
            yc = _extract_yaml_block(answer)
            try:
                _yaml.safe_load(yc)
            except Exception as _ye:
                yaml_errors.append(f"syntactic: {_ye}")
            try:
                import kubernetes_validate as _kv
                _kv.validate(_yaml.safe_load(yc), "1.30", strict=False)
            except Exception as _ke:
                yaml_errors.append(f"schema: {_ke}")

        row = {
            "id":                  data["id"],
            "type":                fixture_type,
            "multi_hop":           data.get("multi_hop", False),
            "mode":                mode,
            "answer_preview":      answer[:200].replace("\n", " "),
            "hops_retrieved":      len(reasoning_path),
            "intent_detected":     intent_detected or "",
            "depth_gt":            reaq.pop("depth_gt"),
            "depth_pred":          reaq.pop("depth_pred"),
            "depth_delta":         len(reasoning_path) - len(expected_path),
            "gt_depth":            reaq.pop("gt_depth"),
            "n_roots":             reaq.pop("n_roots"),
            "n_retrieved_nodes":   retq.pop("n_retrieved_nodes"),
            "n_relevant_nodes":    retq.pop("n_relevant_nodes"),
            "n_node_intersection": retq.pop("n_node_intersection"),
            "seed_node_degree":    seed_degree,
            "error_flag":          _error_flag,
            **{f"ansq_{k}": v for k, v in ansq.items()},
            **{f"retq_{k}": v for k, v in retq.items()},
            **{f"reaq_{k}": v for k, v in reaq.items()},
        }
        rows.append(row)

        # JSONL sidecar (full text — only for 3 main modes, not ablation)
        if ablation_mode is None:
            _cases_buffer.append({
                "id":                  data["id"],
                "type":                fixture_type,
                "multi_hop":           data.get("multi_hop", False),
                "mode":                mode,
                "question":            data["question"],
                "answer_full":         answer,
                "reasoning_path":      reasoning_path,
                "graph_context":       graph_context,
                "missed_edges":        missed_edges,
                "missed_nodes":        missed_nodes,
                "yaml_validation_errors": yaml_errors,
                "retq_score":          retq["retq_score"],
                "ansq_score":          ansq["ansq_score"],
            })

        summary["ansq"].append(ansq["ansq_score"])
        summary["retq"].append(retq["retq_score"])

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
            type_data[t] = {"ansq": [], "retq": []}
        type_data[t]["ansq"].append(ansq["ansq_score"])
        type_data[t]["retq"].append(retq["retq_score"])

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

    # ── JSONL sidecar (full-text, main modes only) ────────────────────────────
    if _cases_buffer and ablation_mode is None:
        import datetime
        _cases_path = output_path.parent / f"eval_cases_{mode}.jsonl"
        with open(_cases_path, "w", encoding="utf-8") as _jf:
            for rec in _cases_buffer:
                _jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info(f"[Cases] {len(_cases_buffer)} full-text records → {_cases_path}")

    # ── Run meta (provenance) ─────────────────────────────────────────────────
    if ablation_mode is None:
        import subprocess, datetime
        _git_commit = ""
        try:
            _git_commit = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent.parent,
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass
        _meta_path = output_path.parent / f"eval_run_meta_{mode}.json"
        with open(_meta_path, "w", encoding="utf-8") as _mf:
            json.dump({
                "mode":        mode,
                "ablation":    ablation_mode,
                "run_id":      _run_id,
                "n_fixtures":  len(summary["ansq"]),
                "output_csv":  str(output_path),
                "git_commit":  _git_commit,
                "timestamp":   datetime.datetime.now().isoformat(),
            }, _mf, indent=2)
        logger.info(f"[Meta] Run provenance → {_meta_path}")

    # ── Print summary ─────────────────────────────────────────────────────────
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    W   = 64

    sys.stdout.reconfigure(encoding="utf-8")

    print()
    print("=" * W)
    _abl_label = f"  ablation: {ablation_mode}" if ablation_mode else ""
    print(f"  Evaluation Results  |  mode: {mode}{_abl_label}  |  {len(summary['ansq'])} questions")
    print("=" * W)
    print(f"  AnsQ (Answer Quality)    : {avg(summary['ansq']):.4f}")
    print(f"  RetQ (Retrieval Quality) : {avg(summary['retq']):.4f}")
    print(f"  ReaQ (Reasoning/Faithful): see ragas_results_{mode}.csv  [run recompute_ragas.py]")
    print(f"  Hop Accuracy [GraphRAG]  : {avg(reaq_subs['hop_accuracy']):.4f}  (n={len(reaq_subs['hop_accuracy'])} path-non-empty)")

    # ── Sub-metric breakdown ──────────────────────────────────────────────────
    print()
    print("  AnsQ sub-metrics:")
    for k, vals in ansq_subs.items():
        label = f"    {k:<26}"
        print(f"{label}: {avg(vals):.4f}  (n={len(vals)})")

    print()
    print("  RetQ sub-metrics (Manning 2008):")
    for k, vals in retq_subs.items():
        label = f"    {k:<26}"
        print(f"{label}: {avg(vals):.4f}  (n={len(vals)})")

    # ── Per question-type breakdown ───────────────────────────────────────────
    print()
    print("  Per question-type breakdown:")
    print(f"  {'Type':<22}  {'AnsQ':>7}  {'RetQ':>7}  {'N':>4}")
    print(f"  {'-'*44}")
    for t in sorted(type_data):
        td = type_data[t]
        print(
            f"  {t:<22}"
            f"  {avg(td['ansq']):>7.4f}"
            f"  {avg(td['retq']):>7.4f}"
            f"  {len(td['ansq']):>4}"
        )

    print()
    print(f"  Results saved -> {output_path}")
    print("=" * W)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _ABLATION_CHOICES = [
        "no_phase1", "no_multihop",
        "depth_1", "depth_2", "depth_3", "depth_4", "depth_5",
        "no_yaml_layer3", "no_multi_entity", "has_property_only",
    ]
    parser = argparse.ArgumentParser(description="GraphRAG Evaluation")
    parser.add_argument("--mode",     default="graphrag", choices=["graphrag", "vector", "llm"])
    parser.add_argument("--output",   default=str(DEFAULT_OUTPUT))
    parser.add_argument("--ablation", default=None, choices=_ABLATION_CHOICES,
                        help="Ablation mode for the graphrag pipeline. "
                             "depth_N overrides traversal depth for ALL intents. "
                             "Only meaningful with --mode graphrag.")
    args = parser.parse_args()
    run_evaluation(mode=args.mode, output_path=Path(args.output), ablation_mode=args.ablation)
