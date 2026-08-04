"""
Judge-quality sensitivity test: compare RAGAS Faithfulness scores
between gpt-4o-mini (current) and gpt-4o (higher-quality judge)
on a stratified sample of 12 graphrag fixtures.

Usage:
    python scripts/sample_judge_gpt4o.py

Output: prints comparison table + aggregate delta.
"""
import sys, os, json, csv, math, asyncio, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING)

DATA_DIR     = Path(__file__).parent.parent / "data"
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"

# ── Stratified sample (4 zeros, 4 low, 2 mid, 2 high) ───────────────────────
SAMPLE_IDS = [
    # zeros (faithfulness = 0.0)
    "kubectl_force_delete_pod",
    "node_affinity_concept",
    "required_fields_container",
    "add_pvc_to_statefulset",
    # low (0 < f <= 0.35)
    "add_liveness_probe",
    "add_readiness_probe",
    "add_resource_limits_deployment",
    "deployment_liveness_probe",
    # mid (0.35 < f <= 0.7)
    "limit_range_concept",
    "oneof_volume_source",
    # high (f > 0.7)
    "anyof_intorstring",
    "namespace_quota",
]

SPEAKER_MAX_CONTEXT_CHARS = 12_000


# ── Context conversion (same as recompute_ragas.py) ─────────────────────────

def _graphrag_ctx_to_texts(ctx_str: str) -> list:
    if not ctx_str:
        return []
    try:
        ctx = json.loads(ctx_str)
    except json.JSONDecodeError:
        return [ctx_str[:SPEAKER_MAX_CONTEXT_CHARS]]
    texts = []
    root_text = (
        f"Resource: {ctx.get('RootKind', ctx.get('RootResource', 'Unknown'))}\n"
        f"Description: {ctx.get('RootDescription', '')}"
    )
    texts.append(root_text.strip())
    for dep in ctx.get("SchemaDependencies", []):
        dep_text = (
            f"Resource: {dep.get('child_resource', '')}\n"
            f"Relation: {dep.get('relation_type', '')} (yaml field: {dep.get('yaml_field', '')})\n"
            f"Description: {dep.get('child_description', '')}"
        )
        texts.append(dep_text.strip())
    result, cum = [], 0
    for t in texts:
        if not t:
            continue
        cum += len(t) + 5
        if cum > SPEAKER_MAX_CONTEXT_CHARS:
            break
        result.append(t)
    return result if result else texts[:1]


# ── Load existing mini scores ────────────────────────────────────────────────

def load_mini_scores() -> dict:
    scores = {}
    with open(DATA_DIR / "eval_results_graphrag_final.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] in SAMPLE_IDS and row.get("reaq_reaq_score"):
                scores[row["id"]] = float(row["reaq_reaq_score"])
    return scores


# ── Load JSONL cases ─────────────────────────────────────────────────────────

def load_cases() -> dict:
    cases = {}
    with open(DATA_DIR / "eval_cases_graphrag.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line.strip())
            if row["id"] in SAMPLE_IDS:
                cases[row["id"]] = row
    return cases


# ── RAGAS with gpt-4o judge ──────────────────────────────────────────────────

def _call_with_retry(fn, max_retries=3, backoff=5.0, **kwargs):
    import time
    for attempt in range(max_retries):
        try:
            return fn(**kwargs)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                wait = backoff * (2 ** attempt)
                print(f"    Rate limit, waiting {wait:.0f}s…")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise
    return None


def _get_score(result):
    try:
        return float(getattr(result, "value", result))
    except (TypeError, ValueError):
        return None


def run_gpt4o_faithfulness(cases: dict) -> dict:
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import Faithfulness

    api_key = os.environ.get("OPENAI_API_KEY")
    client  = AsyncOpenAI(api_key=api_key)
    llm     = llm_factory("gpt-4o", provider="openai", client=client)
    metric  = Faithfulness(llm=llm)

    scores = {}
    for fid, row in cases.items():
        contexts = _graphrag_ctx_to_texts(row.get("graph_context", ""))
        if not contexts:
            scores[fid] = None
            print(f"  [SKIP] {fid}: no context")
            continue
        try:
            result = _call_with_retry(
                metric.score,
                user_input=row["question"],
                response=row["answer_full"],
                retrieved_contexts=contexts,
            )
            val = _get_score(result)
            scores[fid] = val
            print(f"  [OK] {fid}: {val:.3f}" if val is not None else f"  [NONE] {fid}")
        except Exception as e:
            print(f"  [ERR] {fid}: {e}")
            scores[fid] = None
    return scores


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading existing gpt-4o-mini scores …")
    mini_scores = load_mini_scores()
    print(f"  {len(mini_scores)} scores loaded\n")

    print("Loading JSONL cases …")
    cases = load_cases()
    print(f"  {len(cases)} cases loaded\n")

    missing = set(SAMPLE_IDS) - set(cases)
    if missing:
        print(f"[WARN] Missing from JSONL: {missing}\n")

    print("Running RAGAS Faithfulness with gpt-4o judge …")
    gpt4o_scores = run_gpt4o_faithfulness(cases)

    # ── Print comparison table ────────────────────────────────────────────────
    print()
    print(f"{'Fixture':<45} {'Type':<8} {'mini':>6} {'4o':>6} {'delta':>7}")
    print("-" * 80)

    deltas = []
    for fid in SAMPLE_IDS:
        mini = mini_scores.get(fid)
        gpt4 = gpt4o_scores.get(fid)

        # fixture type from CSV
        ftype = ""
        with open(DATA_DIR / "eval_results_graphrag_final.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["id"] == fid:
                    ftype = row.get("type", "")
                    break

        mini_s = f"{mini:.3f}" if mini is not None else "  N/A"
        gpt4_s = f"{gpt4:.3f}" if gpt4 is not None else "  N/A"
        if mini is not None and gpt4 is not None:
            d = gpt4 - mini
            deltas.append(d)
            delta_s = f"{d:+.3f}"
        else:
            delta_s = "    —"
        print(f"  {fid:<43} {ftype:<8} {mini_s:>6} {gpt4_s:>6} {delta_s:>7}")

    print("-" * 80)
    if deltas:
        mean_d = sum(deltas) / len(deltas)
        pos = sum(1 for d in deltas if d > 0.02)
        neg = sum(1 for d in deltas if d < -0.02)
        eql = len(deltas) - pos - neg
        print(f"  Mean delta (4o - mini): {mean_d:+.4f}")
        print(f"  Direction: {pos} higher, {eql} similar, {neg} lower  (threshold |d|>0.02)")
        print()
        if mean_d > 0.05:
            print("  Kesimpulan: gpt-4o menilai LEBIH TINGGI secara material.")
            print("  -> Pertimbangkan upgrade judge untuk full re-run (semua 3 sistem).")
        elif mean_d < -0.05:
            print("  Kesimpulan: gpt-4o menilai LEBIH RENDAH — mini lebih permisif.")
            print("  -> faithfulness rendah bukan artefak judge; genuinely low.")
        else:
            print("  Kesimpulan: delta tidak material (< 0.05).")
            print("  -> faithfulness rendah adalah karakteristik genuine sistem, bukan noise judge.")


if __name__ == "__main__":
    main()
