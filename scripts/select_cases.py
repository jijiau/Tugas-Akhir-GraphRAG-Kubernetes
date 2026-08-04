"""
scripts/select_cases.py
Tag & kurasi case study dari eval_cases JSONL untuk analisis Bab VI.

Input:
  data/eval_results_graphrag_final.csv  — skor per fixture (graphrag)
  data/eval_results_vector_final.csv    — skor per fixture (vector)
  data/eval_cases_graphrag.jsonl        — full-text (graphrag)
  data/eval_cases_vector.jsonl          — full-text (vector)

Output:
  data/eval_case_index.csv              — tag per fixture:
    type_median  : fixture RetQ terdekat ke median per tipe (perilaku tipikal)
    type_worst   : fixture RetQ terendah per tipe (mode gagal tipikal)
    gain_best    : top-3 fixture dengan RetQ-gain GraphRAG−Vector tertinggi (showcase)
    gain_worst   : top-3 fixture dengan RetQ-gain terendah (batas keunggulan)
    fail_yaml_schema / depth_mismatch / high_hallucination : flag mode-gagal

Usage:
  python scripts/select_cases.py
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

GRAPHRAG_CSV  = DATA / "eval_results_graphrag_final.csv"
VECTOR_CSV    = DATA / "eval_results_vector_final.csv"
GRAPHRAG_JSONL = DATA / "eval_cases_graphrag.jsonl"
VECTOR_JSONL   = DATA / "eval_cases_vector.jsonl"
OUT_INDEX      = DATA / "eval_case_index.csv"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> dict:
    """Return {fixture_id: row_dict}."""
    rows = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[row["id"]] = row
    except FileNotFoundError:
        pass
    return rows


def fv(row: dict, col: str) -> float | None:
    v = row.get(col, "").strip()
    try:
        return float(v)
    except (ValueError, AttributeError):
        return None


def load_jsonl(path: Path) -> dict:
    """Return {fixture_id: record_dict}."""
    records = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    records[rec["id"]] = rec
    except FileNotFoundError:
        pass
    return records


def median(vals: list[float]) -> float:
    if not vals:
        return float("nan")
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    graphrag = load_csv(GRAPHRAG_CSV)
    vector   = load_csv(VECTOR_CSV)

    if not graphrag:
        print(f"[ERROR] Cannot read {GRAPHRAG_CSV} — run evaluation first.")
        return
    if not vector:
        print(f"[ERROR] Cannot read {VECTOR_CSV} — run vector evaluation first.")
        return

    # ── Compute RetQ-gain per fixture ─────────────────────────────────────────
    gain_rows = []
    for fid, g_row in graphrag.items():
        v_row = vector.get(fid)
        if v_row is None:
            continue
        retq_g = fv(g_row, "retq_retq_score")
        retq_v = fv(v_row, "retq_retq_score")
        if retq_g is None or retq_v is None:
            continue
        gain_rows.append({
            "id":         fid,
            "type":       g_row.get("type", ""),
            "multi_hop":  g_row.get("multi_hop", ""),
            "retq_graphrag": retq_g,
            "retq_vector":   retq_v,
            "retq_gain":     retq_g - retq_v,
            "yaml_fail_layer": g_row.get("ansq_yaml_fail_layer", ""),
            "depth_delta":   fv(g_row, "depth_delta"),
            "reaq_hallucination_rate": fv(g_row, "reaq_hallucination_rate"),
        })

    if not gain_rows:
        print("[ERROR] No matched fixtures between graphrag and vector CSVs.")
        return

    # ── Per-type: median & worst ──────────────────────────────────────────────
    by_type: dict[str, list] = {}
    for r in gain_rows:
        t = r["type"]
        by_type.setdefault(t, []).append(r)

    tagged: dict[str, dict] = {r["id"]: {"id": r["id"], "type": r["type"]} for r in gain_rows}

    for t, rows in by_type.items():
        retq_vals = [r["retq_graphrag"] for r in rows]
        med = median(retq_vals)
        # type_median: fixture closest to median RetQ for this type
        median_row = min(rows, key=lambda r: abs(r["retq_graphrag"] - med))
        tagged[median_row["id"]]["type_median"] = True
        # type_worst: fixture with lowest absolute RetQ for this type
        worst_row = min(rows, key=lambda r: r["retq_graphrag"])
        tagged[worst_row["id"]]["type_worst"] = True

    # ── Global: gain_best & gain_worst ────────────────────────────────────────
    sorted_by_gain = sorted(gain_rows, key=lambda r: r["retq_gain"], reverse=True)
    for r in sorted_by_gain[:3]:
        tagged[r["id"]]["gain_best"] = True
    for r in sorted_by_gain[-3:]:
        tagged[r["id"]]["gain_worst"] = True

    # ── Mode-gagal flags ──────────────────────────────────────────────────────
    for r in gain_rows:
        tid = r["id"]
        fail = r.get("yaml_fail_layer", "")
        if fail in ("schema", "syntactic", "layer3"):
            tagged[tid]["fail_yaml_schema"] = True

        ddelta = r.get("depth_delta")
        if ddelta is not None and abs(ddelta) >= 2:
            tagged[tid]["depth_mismatch"] = True

        hal = r.get("reaq_hallucination_rate")
        if hal is not None and hal >= 0.5:
            tagged[tid]["high_hallucination"] = True

    # ── Write index CSV ───────────────────────────────────────────────────────
    fieldnames = [
        "id", "type", "retq_graphrag", "retq_vector", "retq_gain",
        "type_median", "type_worst", "gain_best", "gain_worst",
        "fail_yaml_schema", "depth_mismatch", "high_hallucination",
    ]
    n_tagged = sum(1 for v in tagged.values() if len(v) > 2)  # has at least one tag

    with open(OUT_INDEX, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in gain_rows:
            t = tagged.get(r["id"], {})
            writer.writerow({
                "id":            r["id"],
                "type":          r["type"],
                "retq_graphrag": round(r["retq_graphrag"], 4),
                "retq_vector":   round(r["retq_vector"], 4),
                "retq_gain":     round(r["retq_gain"], 4),
                "type_median":       1 if t.get("type_median") else 0,
                "type_worst":        1 if t.get("type_worst") else 0,
                "gain_best":         1 if t.get("gain_best") else 0,
                "gain_worst":        1 if t.get("gain_worst") else 0,
                "fail_yaml_schema":  1 if t.get("fail_yaml_schema") else 0,
                "depth_mismatch":    1 if t.get("depth_mismatch") else 0,
                "high_hallucination":1 if t.get("high_hallucination") else 0,
            })

    print(f"[select_cases] {len(gain_rows)} fixtures processed, {n_tagged} tagged.")
    print(f"  type_median    : {sum(1 for v in tagged.values() if v.get('type_median'))}")
    print(f"  type_worst     : {sum(1 for v in tagged.values() if v.get('type_worst'))}")
    print(f"  gain_best      : {sum(1 for v in tagged.values() if v.get('gain_best'))}")
    print(f"  gain_worst     : {sum(1 for v in tagged.values() if v.get('gain_worst'))}")
    print(f"  fail_yaml_schema   : {sum(1 for v in tagged.values() if v.get('fail_yaml_schema'))}")
    print(f"  depth_mismatch     : {sum(1 for v in tagged.values() if v.get('depth_mismatch'))}")
    print(f"  high_hallucination : {sum(1 for v in tagged.values() if v.get('high_hallucination'))}")
    print(f"  Index saved -> {OUT_INDEX}")


if __name__ == "__main__":
    main()
