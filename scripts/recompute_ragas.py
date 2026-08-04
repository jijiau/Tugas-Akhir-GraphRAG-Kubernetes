"""
scripts/recompute_ragas.py — ReaQ: compute RAGAS Faithfulness offline dari cached JSONL.

ReaQ = RAGAS Faithfulness (claim-level, es_ragas_2023):
  1. LLM decomposes answer into atomic claims
  2. Each claim is verified (entailment) against retrieved_contexts
  Faithfulness = (supported claims) / (total claims)

Applicable: Vector RAG + GraphRAG (has retrieved context). Vanilla LLM = N/A.
Citation: Es et al. 2023 (RAGAS); Ji et al. 2023 (hallucination survey).

Also computes: hop_accuracy (GraphRAG-only diagnostic, Manning et al. 2008 recall on edges).

Dropped: answer_relevancy, context_precision, context_recall — redundant with AnsQ semantic
similarity and RetQ P/R/F1 respectively. Dropping reduces LLM API cost and eliminates
metric overlap.

Output (incremental, resumable):
  data/ragas_results_{mode}.csv  — faithfulness per fixture + hop_accuracy
  Also joins faithfulness back into data/eval_results_{mode}.csv as reaq_reaq_score.

Usage:
  python scripts/recompute_ragas.py [--mode graphrag|vector|llm|all] [--resume]
"""
import sys
import os
import json
import csv
import math
import time
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DATA_DIR = Path(__file__).parent.parent / "data"

# Match the generator's context window (SPEAKER_MAX_CONTEXT_CHARS in src/chatbot/graph_agent.py).
# The speaker LLM truncates graph_context at 12_000 chars; RAGAS must see the same slice.
SPEAKER_MAX_CONTEXT_CHARS = 12_000
# Legacy chunk cap (kept for vector mode and as a safety ceiling)
MAX_CTX_CHUNKS = 10

FIELDNAMES = [
    "id", "type", "multi_hop", "mode",
    "ragas_faithfulness",         # ReaQ composite (es_ragas_2023)
    "reaq_hop_accuracy_corrected", # GraphRAG-only diagnostic (Manning 2008)
]


# ── Context conversion ─────────────────────────────────────────────────────────

def _graphrag_ctx_to_texts(ctx_str: str) -> list:
    if not ctx_str:
        return []
    try:
        ctx = json.loads(ctx_str)
    except json.JSONDecodeError:
        # Non-JSON context (e.g. realworld): treat whole string as one chunk,
        # truncated to same char limit the speaker saw.
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
    # Include chunks until cumulative char count reaches the speaker's window,
    # mirroring SPEAKER_MAX_CONTEXT_CHARS in src/chatbot/graph_agent.py.
    result = []
    cum_chars = 0
    for t in texts:
        if not t:
            continue
        cum_chars += len(t) + 5  # +5 for separator overhead
        if cum_chars > SPEAKER_MAX_CONTEXT_CHARS:
            break
        result.append(t)
    return result if result else texts[:1]


def _vector_ctx_to_texts(ctx_str: str) -> list:
    if not ctx_str:
        return []
    return [c.strip() for c in ctx_str.split("\n---\n") if c.strip()][:MAX_CTX_CHUNKS]


def _ctx_to_texts(mode: str, ctx_str: str) -> list:
    if mode == "graphrag":
        return _graphrag_ctx_to_texts(ctx_str)
    elif mode == "vector":
        return _vector_ctx_to_texts(ctx_str)
    return []


# ── Fixture loader ─────────────────────────────────────────────────────────────

_fixture_cache = {}


def _load_fixture(fixture_id: str, q_type: str) -> dict:
    key = (fixture_id, q_type)
    if key in _fixture_cache:
        return _fixture_cache[key]
    path = FIXTURES_DIR / q_type / f"{fixture_id}.json"
    if not path.exists():
        for p in FIXTURES_DIR.rglob(f"{fixture_id}.json"):
            path = p
            break
    if path.exists():
        d = json.loads(path.read_text(encoding="utf-8"))
        _fixture_cache[key] = d
        return d
    _fixture_cache[key] = {}
    return {}


# ── Hop-Accuracy ───────────────────────────────────────────────────────────────

def compute_hop_accuracy(predicted_path: list, expected_path: list):
    """Hop-Acc = |predicted ∩ expected| / |expected| — edge recall."""
    if not expected_path:
        return None
    exp = set(e.strip().lower() for e in expected_path)
    pred = set(e.strip().lower() for e in predicted_path)
    return len(exp & pred) / len(exp)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) else round(f, 6)
    except (TypeError, ValueError):
        return None


def _get_score(metric_result):
    if metric_result is None:
        return None
    return _safe_float(getattr(metric_result, "value", metric_result))


def _call_with_retry(fn, max_retries=3, backoff=5.0, **kwargs):
    """Call fn(**kwargs) with simple retry on exception (handles rate limits)."""
    for attempt in range(max_retries):
        try:
            return fn(**kwargs)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                wait = backoff * (2 ** attempt)
                logger.warning(f"  Rate limit hit, waiting {wait:.0f}s…")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                logger.warning(f"  Retry {attempt+1}/{max_retries}: {e}")
                time.sleep(2)
            else:
                raise
    return None


# ── RAGAS metric init (Faithfulness only, ragas 0.4.x, AsyncOpenAI) ──────────

def _build_ragas_metrics():
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import Faithfulness
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    c = AsyncOpenAI(api_key=api_key)
    llm = llm_factory("gpt-4o-mini", provider="openai", client=c)
    return {
        "fs": Faithfulness(llm=llm),
    }


# ── Per-fixture scoring ────────────────────────────────────────────────────────

def _score_fixture(row: dict, mode: str, metrics: dict) -> dict:
    fixture_id = row["id"]
    q_type = row.get("type", "concept")
    multi_hop = row.get("multi_hop", False)

    fixture = _load_fixture(fixture_id, q_type)
    gt = fixture.get("ground_truth", {})
    gt_answer = gt.get("answer", "")
    expected_path = gt.get("expected_path", [])

    question = row.get("question", fixture.get("question", ""))
    answer = row.get("answer_full", "")
    ctx_str = row.get("graph_context", "")
    retrieved_contexts = _ctx_to_texts(mode, ctx_str)
    predicted_path = row.get("reasoning_path", [])

    hop_acc = None
    if mode == "graphrag" and expected_path:
        hop_acc = compute_hop_accuracy(predicted_path, expected_path)

    has_retrieval = mode in ("graphrag", "vector") and bool(retrieved_contexts)

    out = {
        "id": fixture_id,
        "type": q_type,
        "multi_hop": multi_hop,
        "mode": mode,
        "ragas_faithfulness": None,
        "reaq_hop_accuracy_corrected": hop_acc,
    }

    # Faithfulness (ReaQ) — Vector + GraphRAG only (requires retrieved context)
    if has_retrieval:
        try:
            r = _call_with_retry(
                metrics["fs"].score,
                user_input=question,
                response=answer,
                retrieved_contexts=retrieved_contexts,
            )
            out["ragas_faithfulness"] = _get_score(r)
        except Exception as e:
            logger.warning(f"  FS failed: {e}")
    # else: Vanilla LLM = N/A (no retrieved context to verify claims against)

    skip_reasons = {}
    if out["ragas_faithfulness"] is None:
        skip_reasons["ragas_faithfulness"] = "no_retrieval" if not has_retrieval else "api_error_or_nan"
    out["_skip_reasons"] = skip_reasons
    return out


# ── Incremental CSV ────────────────────────────────────────────────────────────

def _load_done(path: Path) -> set:
    """Return set of IDs already computed."""
    done = set()
    if not path.exists():
        return done
    try:
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("id"):
                    done.add(row["id"])
    except Exception:
        pass
    return done


def _open_writer(path: Path, append: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    f = open(path, mode, newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
    if not append:
        w.writeheader()
    return f, w


def _write_row(writer, row: dict):
    writer.writerow({k: ("" if row.get(k) is None else row.get(k, ""))
                     for k in FIELDNAMES})


# ── Main per-mode processing ───────────────────────────────────────────────────

def _process_mode(rows: list, mode: str, metrics: dict, resume: bool) -> list:
    out_path = DATA_DIR / f"ragas_results_{mode}.csv"
    done_ids = _load_done(out_path) if resume else set()

    append_mode = resume and bool(done_ids)
    f, writer = _open_writer(out_path, append=append_mode)

    all_results = []
    n = len(rows)
    skipped = 0
    skip_tally = {}   # F5: metric -> {reason -> count}

    try:
        for i, row in enumerate(rows):
            fixture_id = row["id"]
            if fixture_id in done_ids:
                skipped += 1
                logger.info(f"[{i+1}/{n}] SKIP {fixture_id}")
                continue

            logger.info(f"[{i+1}/{n}] {mode}/{fixture_id} (n_done={len(all_results)+skipped})")
            result = _score_fixture(row, mode, metrics)

            _write_row(writer, result)
            f.flush()
            for _metric, _reason in (result.pop("_skip_reasons", {}) or {}).items():
                skip_tally.setdefault(_metric, {})
                skip_tally[_metric][_reason] = skip_tally[_metric].get(_reason, 0) + 1
            all_results.append(result)

            parts = []
            for k, lbl in [
                ("ragas_faithfulness",          "FS (ReaQ)"),
                ("reaq_hop_accuracy_corrected", "HA"),
            ]:
                v = result.get(k)
                parts.append(f"{lbl}={v:.4f}" if v is not None else f"{lbl}=N/A")
            logger.info("  " + "  ".join(parts))
    finally:
        f.close()

    logger.info(f"Mode {mode}: {len(all_results)} new, {skipped} skipped → {out_path}")
    if skip_tally:
        logger.info(f"[{mode}] Missing breakdown:")
        _reasons = skip_tally.get("ragas_faithfulness")
        if _reasons:
            _total = sum(_reasons.values())
            _detail = ", ".join(f"{r}={c}" for r, c in sorted(_reasons.items()))
            logger.info(f"    ragas_faithfulness: {_total} missing ({_detail})")
    return all_results


# ── Summary ───────────────────────────────────────────────────────────────────

def _print_summary(all_results: list, modes: list):
    print("\n" + "=" * 65)
    print("SUMMARY — RAGAS Faithfulness (ReaQ) recompute")
    print("=" * 65)
    for mode in modes:
        mode_rows = [r for r in all_results if r.get("mode") == mode]
        if not mode_rows:
            continue

        def _avg(key):
            vals = []
            for r in mode_rows:
                v = r.get(key)
                if v not in (None, ""):
                    try:
                        vals.append(float(v))
                    except ValueError:
                        pass
            return sum(vals) / len(vals) if vals else None

        def _count(key):
            return sum(1 for r in mode_rows if r.get(key) not in (None, ""))

        total = len(mode_rows)
        print(f"\n{mode.upper()} (n={total})")
        for key, label in [
            ("ragas_faithfulness",          "faithfulness  [ReaQ, es_ragas_2023]"),
            ("reaq_hop_accuracy_corrected", "hop_acc       [GraphRAG diagnostic, Manning 2008]"),
        ]:
            v = _avg(key)
            n_v = _count(key)
            val_str = f"{v:.4f}  (n={n_v}/{total})" if v is not None else "N/A"
            print(f"  {label:<46} = {val_str}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="all",
                        choices=["graphrag", "vector", "llm", "all"])
    parser.add_argument("--resume", action="store_true",
                        help="Skip fixtures already written to output CSV.")
    args = parser.parse_args()

    modes = ["graphrag", "vector", "llm"] if args.mode == "all" else [args.mode]

    logger.info("Initialising RAGAS (gpt-4o-mini + text-embedding-3-small)…")
    metrics = _build_ragas_metrics()

    all_results = []

    for mode in modes:
        jsonl_path = DATA_DIR / f"eval_cases_{mode}.jsonl"
        if not jsonl_path.exists():
            logger.error(f"Missing: {jsonl_path}")
            continue

        rows = [
            json.loads(line)
            for line in jsonl_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        logger.info(f"\n{'='*50}\nMode: {mode} ({len(rows)} fixtures)\n{'='*50}")
        mode_results = _process_mode(rows, mode, metrics, resume=args.resume)
        all_results.extend(mode_results)

    if len(modes) > 1 and all_results:
        merged_path = DATA_DIR / "ragas_results_all.csv"
        with open(merged_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            w.writeheader()
            for row in all_results:
                _write_row(w, row)
        logger.info(f"Merged: {merged_path} ({len(all_results)} rows)")

    _print_summary(all_results, modes)

    # ── Join faithfulness back into eval_results CSV as reaq_reaq_score ───────
    # This makes statistical_test.py work without a separate join step.
    _join_faithfulness_to_eval(all_results, modes)


def _join_faithfulness_to_eval(all_results: list, modes: list):
    """
    For each mode, update data/eval_results_{mode}.csv:
    set reaq_reaq_score = ragas_faithfulness (the ReaQ composite).
    Creates a lookup from fixture id → faithfulness, then rewrites the CSV.
    Skips silently if the eval CSV doesn't exist yet.
    """
    for mode in modes:
        eval_path = DATA_DIR / f"eval_results_{mode}.csv"
        if not eval_path.exists():
            # Try default name for graphrag mode
            if mode == "graphrag":
                eval_path = DATA_DIR / "eval_results.csv"
            if not eval_path.exists():
                logger.info(f"[Join] No eval CSV for mode={mode}, skipping join")
                continue

        # Build id → faithfulness map
        faith_map = {}
        for r in all_results:
            if r.get("mode") == mode and r.get("ragas_faithfulness") is not None:
                faith_map[r["id"]] = r["ragas_faithfulness"]

        if not faith_map:
            logger.info(f"[Join] No faithfulness values for mode={mode}, skipping join")
            continue

        try:
            import io
            with open(eval_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames or []

            if not rows:
                continue

            # Ensure reaq_reaq_score column exists
            if "reaq_reaq_score" not in fieldnames:
                fieldnames = list(fieldnames) + ["reaq_reaq_score"]

            updated = 0
            for row in rows:
                fid = row.get("id", "")
                if fid in faith_map:
                    row["reaq_reaq_score"] = str(round(faith_map[fid], 6))
                    updated += 1

            with open(eval_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"[Join] Updated {updated}/{len(rows)} rows in {eval_path} with ReaQ faithfulness")
        except Exception as e:
            logger.warning(f"[Join] Could not update {eval_path}: {e}")


if __name__ == "__main__":
    main()
