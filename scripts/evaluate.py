# scripts/evaluate.py
"""
GraphRAG Evaluation Script — Three-Dimension Custom Metrics
Usage: python scripts/evaluate.py [--mode graphrag] [--output data/eval_results.csv]

Dimensions:
  AnsQ (40%): Answer Quality  — syntactic validity, schema compliance, faithfulness, answer relevance
  RetQ (35%): Retrieval Quality — precision@k, recall@k, F1@k, graph coverage
  ReaQ (25%): Reasoning Quality — hop accuracy, multi-hop success rate, scope accuracy, hallucination rate
"""
import sys
import os
import json
import csv
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


# ── Metric helpers ────────────────────────────────────────────────────────────

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


def compute_ansq(answer: str, ground_truth: dict, fixture_type: str) -> dict:
    """Answer Quality metrics."""
    scores = {}

    # Syntactic Validity (yaml_gen only)
    if fixture_type == "yaml_gen":
        try:
            import yaml
            yaml.safe_load(answer)
            scores["syntactic_validity"] = 1.0
        except Exception:
            scores["syntactic_validity"] = 0.0
    else:
        scores["syntactic_validity"] = None  # N/A

    # Schema Compliance (yaml_gen only) — requires kubernetes-validate
    if fixture_type == "yaml_gen":
        try:
            import yaml
            import kubernetes_validate
            data = yaml.safe_load(answer)
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

    # Answer Relevance — token F1 against ground truth answer
    gt_answer = ground_truth.get("answer", "")
    scores["answer_relevance"] = _token_f1(answer, gt_answer)

    # Faithfulness — simple heuristic: does answer reference known context nodes?
    gt_nodes = [n.split(".")[-1] for n in ground_truth.get("relevant_nodes", [])]
    hit = sum(1 for n in gt_nodes if n.lower() in answer.lower())
    scores["faithfulness"] = hit / len(gt_nodes) if gt_nodes else 1.0

    applicable = [v for v in scores.values() if v is not None]
    scores["ansq_score"] = sum(applicable) / len(applicable) if applicable else 0.0
    return scores


def compute_retq(reasoning_path: list, ground_truth: dict) -> dict:
    """Retrieval Quality metrics."""
    expected_nodes = set(n.split(".")[-1] for n in ground_truth.get("relevant_nodes", []))
    retrieved_nodes = set()
    for step in reasoning_path:
        parts = step.replace("->", " ").replace("-[", " ").replace("]", " ").split()
        retrieved_nodes.update(parts)

    intersection = retrieved_nodes & expected_nodes
    precision = len(intersection) / len(retrieved_nodes) if retrieved_nodes else 0.0
    recall    = len(intersection) / len(expected_nodes) if expected_nodes else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    expected_path = ground_truth.get("expected_path", [])
    graph_coverage = (
        len([p for p in expected_path if any(
            p.split(" -[")[0] in step for step in reasoning_path
        )]) / len(expected_path)
        if expected_path else 1.0
    )

    retq_score = (precision + recall + f1 + graph_coverage) / 4
    return {
        "precision_at_k": precision,
        "recall_at_k": recall,
        "f1_at_k": f1,
        "graph_coverage": graph_coverage,
        "retq_score": retq_score,
    }


def compute_reaq(reasoning_path: list, answer: str, ground_truth: dict, fixture_type: str) -> dict:
    """Reasoning Quality metrics."""
    expected_path = ground_truth.get("expected_path", [])
    multi_hop = ground_truth.get("multi_hop", False)

    # Hop Accuracy
    if expected_path and multi_hop:
        matched = sum(
            1 for ep in expected_path
            if any(ep.split(" -[")[0] in step for step in reasoning_path)
        )
        hop_accuracy = matched / len(expected_path)
    else:
        hop_accuracy = 1.0 if reasoning_path else 0.0

    # Multi-hop Success Rate: did answer contain relevant multi-hop info?
    multi_hop_success = 1.0 if (multi_hop and reasoning_path) or (not multi_hop) else 0.0

    # Scope Accuracy
    expected_scope = ground_truth.get("scope", "")
    scope_keywords = {
        "Cluster": ["cluster", "clusterrole", "clusterscoped", "node", "namespace-wide"],
        "Namespaced": ["namespaced", "namespace", "deployment", "pod", "service"]
    }
    if expected_scope:
        keywords = scope_keywords.get(expected_scope, [])
        scope_hit = any(kw in answer.lower() for kw in keywords)
        scope_accuracy = 1.0 if scope_hit else 0.5  # partial credit
    else:
        scope_accuracy = 1.0

    reaq_score = (hop_accuracy + multi_hop_success + scope_accuracy) / 3
    return {
        "hop_accuracy": hop_accuracy,
        "multi_hop_success": multi_hop_success,
        "scope_accuracy": scope_accuracy,
        "reaq_score": reaq_score,
    }


# ── Runner ────────────────────────────────────────────────────────────────────

def run_evaluation(mode: str = "graphrag", output_path: Path = DEFAULT_OUTPUT):
    from src.chatbot.graph_agent import create_agent_graph

    agent = create_agent_graph()
    fixtures = sorted(FIXTURES_DIR.rglob("*.json"))

    if not fixtures:
        logger.error(f"No fixtures found in {FIXTURES_DIR}")
        sys.exit(1)

    logger.info(f"Running evaluation: mode={mode}, fixtures={len(fixtures)}")

    rows = []
    summary = {"ansq": [], "retq": [], "reaq": [], "total": []}

    for fpath in fixtures:
        data = json.loads(fpath.read_text(encoding="utf-8"))
        question      = data["question"]
        fixture_type  = data["type"]
        ground_truth  = data["ground_truth"]

        logger.info(f"  [{fixture_type}] {data['id']}: {question[:60]}...")

        result = agent.invoke({
            "question": question,
            "session_id": f"eval_{data['id']}",
            "messages": [],
            "chat_history": "",
            "extracted_intent": {},
            "graph_context": "",
            "reasoning_path": [],
            "error": None,
        })

        answer         = result["messages"][-1].content if result.get("messages") else ""
        reasoning_path = result.get("reasoning_path") or []

        ansq = compute_ansq(answer, ground_truth, fixture_type)
        retq = compute_retq(reasoning_path, ground_truth)
        reaq = compute_reaq(reasoning_path, answer, ground_truth, fixture_type)

        total = ansq["ansq_score"] * ANSQ_WEIGHT + retq["retq_score"] * RETQ_WEIGHT + reaq["reaq_score"] * REAQ_WEIGHT

        row = {
            "id": data["id"],
            "type": fixture_type,
            "multi_hop": data.get("multi_hop", False),
            "mode": mode,
            "answer_preview": answer[:100].replace("\n", " "),
            "hops_retrieved": len(reasoning_path),
            **{f"ansq_{k}": v for k, v in ansq.items()},
            **{f"retq_{k}": v for k, v in retq.items()},
            **{f"reaq_{k}": v for k, v in reaq.items()},
            "total_score": round(total, 4),
        }
        rows.append(row)

        summary["ansq"].append(ansq["ansq_score"])
        summary["retq"].append(retq["retq_score"])
        summary["reaq"].append(reaq["reaq_score"])
        summary["total"].append(total)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Print summary ─────────────────────────────────────────────────────────
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    print("\n" + "=" * 60)
    print(f"  Evaluation Results — mode: {mode}  ({len(rows)} questions)")
    print("=" * 60)
    print(f"  AnsQ (Answer Quality)   : {avg(summary['ansq']):.4f}  [weight 40%]")
    print(f"  RetQ (Retrieval Quality): {avg(summary['retq']):.4f}  [weight 35%]")
    print(f"  ReaQ (Reasoning Quality): {avg(summary['reaq']):.4f}  [weight 25%]")
    print(f"  ─────────────────────────────────────────")
    print(f"  Weighted Total          : {avg(summary['total']):.4f}")
    print(f"\n  Results saved → {output_path}")

    # Per-type breakdown
    types = set(r["type"] for r in rows)
    print("\n  Per question-type breakdown:")
    for t in sorted(types):
        t_rows = [r for r in rows if r["type"] == t]
        t_avg  = avg([r["total_score"] for r in t_rows])
        print(f"    {t:20s}: {t_avg:.4f}  ({len(t_rows)} questions)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GraphRAG Evaluation")
    parser.add_argument("--mode",   default="graphrag", choices=["graphrag", "vector", "llm"])
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    run_evaluation(mode=args.mode, output_path=Path(args.output))
