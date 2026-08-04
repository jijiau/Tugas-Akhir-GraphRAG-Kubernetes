"""
Diagnose WHY faithfulness is low: decompose the answer into atomic claims,
verdict each against retrieved context, and classify unsupported claims as:

  - "absent"   : the fact/entity is genuinely NOT in the retrieved context
                 (true ungroundedness - fixable by a grounding instruction)
  - "modality" : the entity IS in the context, but the context gives only a
                 declarative description while the claim asserts a procedure
                 or relationship not literally stated (measurement artifact -
                 NOT fixable by grounding; needs richer context or metric reframe)
  - "partial"  : partially supported
  - "other"    : unknown label returned by judge (guard bucket)

Document vs Parametric mapping (agreed):
  DOCUMENT   = supported + modality  [+ partial in scenario A]
  PARAMETRIC = absent

Scenario A: partial in DOCUMENT
Scenario B: partial reported separately (excluded from both buckets)

Usage:
  python scripts/diagnose_faithfulness.py              # full 102-fixture run
  python scripts/diagnose_faithfulness.py --resume     # skip already-cached fixtures
  python scripts/diagnose_faithfulness.py --sample     # 3-fixture smoke test (original)
  python scripts/diagnose_faithfulness.py --limit 5    # first 5 only (dry-run)

Outputs:
  data/faithfulness_decomposition_raw.jsonl   -raw judge claims per fixture (cache/resume)
  data/faithfulness_decomposition.csv         -per-fixture decomposition table
  data/faithfulness_decomposition_summary.json -aggregate headline (whole + schema/freetext)

Cost estimate (full run): ~102 x gpt-4o calls ~ $1.50, ~8-15 min sequential.
"""
import sys, os, json, csv, argparse, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
SPEAKER_MAX_CONTEXT_CHARS = 12_000
RAW_CACHE_PATH  = DATA_DIR / "faithfulness_decomposition_raw.jsonl"
CSV_PATH        = DATA_DIR / "faithfulness_decomposition.csv"
SUMMARY_PATH    = DATA_DIR / "faithfulness_decomposition_summary.json"

KNOWN_CLASSES = {"supported", "modality", "partial", "absent"}

# 3-fixture sample for smoke test (original set)
SAMPLE_IDS = [
    "required_fields_container",  # faithfulness ~ 0.000
    "limit_range_concept",        # faithfulness ~ 0.375
    "namespace_quota",            # faithfulness ~ 0.857
]

CSV_FIELDNAMES = [
    "id", "type", "ctx_kind", "multi_hop",
    "n_claims", "supported", "modality", "partial", "absent", "other",
    "document_claims_A", "parametric_claims",
    "document_pct_A", "parametric_pct_A",
    "document_pct_B", "faithfulness_run",
]


# -- Context helpers ------------------------------------------------------------

def _ctx_kind(ctx_str: str) -> str:
    try:
        json.loads(ctx_str)
        return "schema"
    except (json.JSONDecodeError, TypeError):
        return "freetext"


def _graphrag_ctx_to_texts(ctx_str: str) -> list:
    if not ctx_str:
        return []
    try:
        ctx = json.loads(ctx_str)
    except json.JSONDecodeError:
        return [ctx_str[:SPEAKER_MAX_CONTEXT_CHARS]]
    texts = [
        (f"Resource: {ctx.get('RootKind', ctx.get('RootResource', 'Unknown'))}\n"
         f"Description: {ctx.get('RootDescription', '')}").strip()
    ]
    for dep in ctx.get("SchemaDependencies", []):
        texts.append(
            (f"Resource: {dep.get('child_resource', '')}\n"
             f"Relation: {dep.get('relation_type', '')} (yaml field: {dep.get('yaml_field', '')})\n"
             f"Description: {dep.get('child_description', '')}").strip()
        )
    result, cum = [], 0
    for t in texts:
        if not t:
            continue
        cum += len(t) + 5
        if cum > SPEAKER_MAX_CONTEXT_CHARS:
            break
        result.append(t)
    return result if result else texts[:1]


# -- Data loading --------------------------------------------------------------─

def load_all_cases(limit=None, sample_only=False) -> list:
    rows = []
    with open(DATA_DIR / "eval_cases_graphrag.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line.strip())
            if sample_only and row["id"] not in SAMPLE_IDS:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    if sample_only:
        id_order = {fid: i for i, fid in enumerate(SAMPLE_IDS)}
        rows.sort(key=lambda r: id_order.get(r["id"], 999))
    return rows


def load_cached_ids() -> set:
    done = set()
    if not RAW_CACHE_PATH.exists():
        return done
    with open(RAW_CACHE_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                if obj.get("id"):
                    done.add(obj["id"])
            except json.JSONDecodeError:
                pass
    return done


# -- Judge call ----------------------------------------------------------------

DIAGNOSE_PROMPT = """You are auditing a RAG system's faithfulness. You are given a QUESTION, \
the system's ANSWER, and the RETRIEVED CONTEXT (Kubernetes schema node descriptions).

Step 1: Decompose the ANSWER into atomic factual claims (one assertion each).
Step 2: For each claim, decide if it can be directly inferred from the RETRIEVED CONTEXT.
Step 3: For each UNSUPPORTED claim, classify the reason:
  - "absent": the entity/fact in the claim is genuinely NOT present anywhere in the context.
  - "modality": the entity IS named/described in the context, but the context only gives a \
declarative description (what it IS) while the claim asserts a procedure, step, or relationship \
not literally stated in the context text.
  - "partial": partially supported.

Return STRICT JSON:
{{"claims": [{{"claim": "...", "supported": true/false, "reason_class": "supported"|"absent"|"modality"|"partial"}}]}}

QUESTION:
{question}

ANSWER:
{answer}

RETRIEVED CONTEXT:
{context}
"""


def _call_with_retry(client, prompt, max_retries=3, backoff=5.0):
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                wait = backoff * (2 ** attempt)
                print(f"    [rate-limit] waiting {wait:.0f}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                print(f"    [retry {attempt+1}/{max_retries}] {e}")
                time.sleep(2)
            else:
                raise
    return None


def diagnose(case: dict, client) -> dict:
    contexts = _graphrag_ctx_to_texts(case.get("graph_context", ""))
    context_str = "\n\n".join(contexts)
    prompt = DIAGNOSE_PROMPT.format(
        question=case["question"],
        answer=case["answer_full"],
        context=context_str[:SPEAKER_MAX_CONTEXT_CHARS],
    )
    return _call_with_retry(client, prompt)


# -- Per-fixture row building --------------------------------------------------─

def build_row(case: dict, result: dict) -> dict:
    claims = result.get("claims", [])
    counts = {"supported": 0, "modality": 0, "partial": 0, "absent": 0, "other": 0}
    for c in claims:
        rc = c.get("reason_class", "supported")
        if c.get("supported"):
            rc = "supported"
        if rc not in KNOWN_CLASSES:
            rc = "other"
        counts[rc] += 1

    n = len(claims) or 1
    # Scenario A: partial in DOCUMENT
    doc_A = counts["supported"] + counts["modality"] + counts["partial"]
    par   = counts["absent"]
    # Scenario B: partial excluded from both (reported separately); DOCUMENT = supported+modality
    doc_B = counts["supported"] + counts["modality"]

    ctx_str = case.get("graph_context", "")

    return {
        "id":               case["id"],
        "type":             case.get("type", ""),
        "ctx_kind":         _ctx_kind(ctx_str),
        "multi_hop":        case.get("multi_hop", False),
        "n_claims":         len(claims),
        "supported":        counts["supported"],
        "modality":         counts["modality"],
        "partial":          counts["partial"],
        "absent":           counts["absent"],
        "other":            counts["other"],
        "document_claims_A": doc_A,
        "parametric_claims": par,
        "document_pct_A":   round(doc_A / n * 100, 1),
        "parametric_pct_A": round(par / n * 100, 1),
        "document_pct_B":   round(doc_B / n * 100, 1),
        "faithfulness_run": round(counts["supported"] / n, 4),
        "_claims_raw":      claims,
    }


# -- Aggregate computation ----------------------------------------------------─

def _agg_rows(rows: list) -> dict:
    totals = {"n_fixtures": 0, "n_claims": 0,
              "supported": 0, "modality": 0, "partial": 0, "absent": 0, "other": 0}
    for r in rows:
        totals["n_fixtures"] += 1
        totals["n_claims"]   += r["n_claims"]
        for k in ("supported", "modality", "partial", "absent", "other"):
            totals[k] += r[k]
    n = totals["n_claims"] or 1
    doc_A = totals["supported"] + totals["modality"] + totals["partial"]
    doc_B = totals["supported"] + totals["modality"]
    par   = totals["absent"]
    macro_doc_A = (sum(r["document_pct_A"] for r in rows) / len(rows)) if rows else 0
    macro_doc_B = (sum(r["document_pct_B"] for r in rows) / len(rows)) if rows else 0
    return {
        **totals,
        "document_pct_A_micro":  round(doc_A / n * 100, 1),
        "parametric_pct_A_micro": round(par / n * 100, 1),
        "document_pct_B_micro":  round(doc_B / n * 100, 1),
        "macro_document_pct_A":  round(macro_doc_A, 1),
        "macro_document_pct_B":  round(macro_doc_B, 1),
        "faithfulness_micro":    round(totals["supported"] / n, 4),
    }


def compute_summary(all_rows: list) -> dict:
    schema_rows   = [r for r in all_rows if r["ctx_kind"] == "schema"]
    freetext_rows = [r for r in all_rows if r["ctx_kind"] == "freetext"]
    return {
        "whole":    _agg_rows(all_rows),
        "schema":   _agg_rows(schema_rows),
        "freetext": _agg_rows(freetext_rows),
    }


# -- Print helpers ------------------------------------------------------------─

def _print_agg(label: str, agg: dict):
    n = agg["n_claims"] or 1
    print(f"\n  {label}  (n_fixtures={agg['n_fixtures']}, n_claims={agg['n_claims']})")
    for k in ("supported", "modality", "partial", "absent", "other"):
        pct = agg[k] / n * 100
        print(f"    {k:<12}: {agg[k]:>4}  ({pct:.1f}%)")
    print(f"  -- DOCUMENT vs PARAMETRIC --")
    print(f"    Scenario A (partial in DOC) : DOCUMENT {agg['document_pct_A_micro']:.1f}%"
          f"  PARAMETRIC {agg['parametric_pct_A_micro']:.1f}%"
          f"  (macro DOC {agg['macro_document_pct_A']:.1f}%)")
    print(f"    Scenario B (partial sep) : DOCUMENT {agg['document_pct_B_micro']:.1f}%"
          f"  PARTIAL {agg['partial']/n*100:.1f}%"
          f"  PARAMETRIC {agg['parametric_pct_A_micro']:.1f}%"
          f"  (macro DOC {agg['macro_document_pct_B']:.1f}%)")
    unsup = agg["absent"] + agg["modality"] + agg["partial"]
    if unsup:
        mod_share = agg["modality"] / unsup * 100
        abs_share = agg["absent"]   / unsup * 100
        print(f"  -- Of UNSUPPORTED claims --")
        print(f"    modality (artefak, not fixable): {mod_share:.0f}%")
        print(f"    absent   (genuine, fixable):     {abs_share:.0f}%")


# -- Main ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Full-corpus faithfulness decomposition")
    parser.add_argument("--resume", action="store_true",
                        help="Skip fixtures already cached in raw JSONL.")
    parser.add_argument("--sample", action="store_true",
                        help="Run original 3-fixture smoke test only.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N fixtures (dry-run).")
    args = parser.parse_args()

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    cases = load_all_cases(limit=args.limit, sample_only=args.sample)
    cached_ids = load_cached_ids() if args.resume else set()

    n_total = len(cases)
    n_skip  = sum(1 for c in cases if c["id"] in cached_ids)
    n_run   = n_total - n_skip

    mode_tag = "SAMPLE" if args.sample else (f"LIMIT={args.limit}" if args.limit else "FULL")
    print(f"\n{'='*70}")
    print(f"  diagnose_faithfulness.py  [{mode_tag}]")
    print(f"  fixtures: {n_total}  |  cached/skip: {n_skip}  |  to run: {n_run}")
    if not args.sample:
        print(f"  Estimated cost: ~${n_run * 0.015:.2f}  |  duration: ~{n_run*6//60}-{n_run*9//60} min")
    print(f"{'='*70}\n")

    # Open cache in append mode
    raw_f = open(RAW_CACHE_PATH, "a", encoding="utf-8") if args.resume else \
            open(RAW_CACHE_PATH, "w", encoding="utf-8")

    all_rows = []

    # Load already-cached rows if resuming (to include in final CSV/summary)
    if args.resume and cached_ids:
        with open(RAW_CACHE_PATH, encoding="utf-8") as cf:
            for line in cf:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("id") and "claims" in obj:
                        # Rebuild row from cache
                        # We need the case data too
                        pass
                except Exception:
                    pass
        # Reload cases without limit to get full data for cached rows
        full_cases = {c["id"]: c for c in load_all_cases()}
        cached_results_raw = {}
        with open(RAW_CACHE_PATH, encoding="utf-8") as cf:
            for line in cf:
                try:
                    obj = json.loads(line.strip())
                    fid = obj.get("id")
                    if fid and "claims" in obj:
                        cached_results_raw[fid] = {"claims": obj["claims"]}
                except Exception:
                    pass
        for fid, result in cached_results_raw.items():
            case = full_cases.get(fid)
            if case:
                all_rows.append(build_row(case, result))

    try:
        for i, case in enumerate(cases):
            fid = case["id"]
            if fid in cached_ids:
                print(f"  [{i+1:>3}/{n_total}] SKIP  {fid}")
                continue

            print(f"  [{i+1:>3}/{n_total}] calling gpt-4o ... {fid}", end="", flush=True)
            try:
                result = diagnose(case, client)
            except Exception as e:
                print(f"  [ERR] {e}")
                continue

            row = build_row(case, result)
            all_rows.append(row)

            # Print per-fixture summary (verbose in sample mode, terse in full)
            claims = result.get("claims", [])
            n_c = len(claims) or 1
            print(f"  -> {len(claims)} claims  "
                  f"sup={row['supported']} mod={row['modality']} "
                  f"abs={row['absent']} par={row['partial']}"
                  + (f" oth={row['other']}" if row['other'] else "")
                  + f"  faith={row['faithfulness_run']:.3f}")

            if args.sample:
                for c in claims:
                    rc = c.get("reason_class", "?")
                    if c.get("supported"):
                        rc = "supported"
                    mark = "OK " if c.get("supported") else f"NO [{rc}]"
                    print(f"      {mark:<14} {c.get('claim','')[:85]}")
                print()

            # Cache raw result immediately
            cache_entry = {"id": fid, "claims": result.get("claims", [])}
            raw_f.write(json.dumps(cache_entry, ensure_ascii=False) + "\n")
            raw_f.flush()

            # Polite inter-call pause
            if i < n_total - 1 and fid not in cached_ids:
                time.sleep(0.35)

    finally:
        raw_f.close()

    if not all_rows:
        print("\nNo results to aggregate.")
        return

    # Write per-fixture CSV (always full rebuild from all_rows)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for row in all_rows:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})
    print(f"\n  Saved per-fixture CSV -> {CSV_PATH.name}  ({len(all_rows)} rows)")

    # Compute and print aggregate summary
    summary = compute_summary(all_rows)
    print(f"\n{'='*70}")
    print("  AGGREGATE SUMMARY -Document vs Parametric Decomposition")
    print(f"{'='*70}")
    _print_agg("WHOLE CORPUS", summary["whole"])
    _print_agg("SCHEMA fixtures (ctx JSON)", summary["schema"])
    _print_agg("FREE-TEXT fixtures (realworld/planning)", summary["freetext"])

    # Persist summary JSON
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Saved summary -> {SUMMARY_PATH.name}")
    print(f"  Cache        -> {RAW_CACHE_PATH.name}")
    print()


if __name__ == "__main__":
    main()
