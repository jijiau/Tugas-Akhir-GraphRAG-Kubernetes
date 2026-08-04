"""
scripts/aggregate_ragas.py — Agregasi hasil ragas_results_{mode}.csv ke bentuk yang siap analisis.

Membuat:
  data/ragas_results_all.csv        — semua mode digabung
  data/ragas_summary_by_mode.csv    — mean per mode
  data/ragas_summary_by_type.csv    — mean per mode × type
  data/ragas_summary_by_multihop.csv — mean per mode × multi_hop

Usage:
  python scripts/aggregate_ragas.py
"""
import sys
import csv
import io
import math
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

MODES = ["graphrag", "vector", "llm"]
METRIC_COLS = [
    "ragas_faithfulness",
    "ragas_answer_relevancy",
    "ragas_context_precision",
    "ragas_context_recall",
    "reaq_hop_accuracy_corrected",
]
FIELDNAMES_ALL = [
    "id", "type", "multi_hop", "mode",
    *METRIC_COLS,
]


def _read_csv_safe(path: Path) -> list:
    """Read CSV with NUL byte filtering."""
    if not path.exists():
        return []
    with open(path, "rb") as f:
        content = f.read().replace(b"\x00", b"")
    try:
        return list(csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))))
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return []


def _safe_float(val):
    if val in (None, ""):
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


def _avg(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def _count_valid(values):
    return sum(1 for v in values if v is not None)


def main():
    all_rows = []

    for mode in MODES:
        path = DATA_DIR / f"ragas_results_{mode}.csv"
        rows = _read_csv_safe(path)
        print(f"[{mode}] {len(rows)} rows loaded from {path.name}")
        all_rows.extend(rows)

    if not all_rows:
        print("No data found.")
        return

    # Write merged CSV
    merged_path = DATA_DIR / "ragas_results_all.csv"
    with open(merged_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES_ALL, extrasaction="ignore")
        w.writeheader()
        for row in all_rows:
            out = {k: row.get(k, "") for k in FIELDNAMES_ALL}
            w.writerow(out)
    print(f"Merged: {merged_path} ({len(all_rows)} rows)")

    # ── Summary by mode ───────────────────────────────────────────────────────
    summary_mode = []
    for mode in MODES:
        mode_rows = [r for r in all_rows if r.get("mode") == mode]
        if not mode_rows:
            continue
        row = {"mode": mode, "n": len(mode_rows)}
        for col in METRIC_COLS:
            vals = [_safe_float(r.get(col)) for r in mode_rows]
            row[col + "_mean"] = _avg(vals)
            row[col + "_n"] = _count_valid(vals)
        summary_mode.append(row)

    mode_cols = ["mode", "n"] + [c + "_mean" for c in METRIC_COLS] + [c + "_n" for c in METRIC_COLS]
    sm_path = DATA_DIR / "ragas_summary_by_mode.csv"
    with open(sm_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=mode_cols, extrasaction="ignore")
        w.writeheader()
        for row in summary_mode:
            w.writerow({k: ("" if row.get(k) is None else row.get(k, "")) for k in mode_cols})
    print(f"Summary by mode: {sm_path}")

    # ── Summary by mode × type ────────────────────────────────────────────────
    types = sorted(set(r.get("type", "") for r in all_rows if r.get("type")))
    summary_type = []
    for mode in MODES:
        for qtype in types:
            subset = [r for r in all_rows if r.get("mode") == mode and r.get("type") == qtype]
            if not subset:
                continue
            row = {"mode": mode, "type": qtype, "n": len(subset)}
            for col in METRIC_COLS:
                vals = [_safe_float(r.get(col)) for r in subset]
                row[col + "_mean"] = _avg(vals)
            summary_type.append(row)

    type_cols = ["mode", "type", "n"] + [c + "_mean" for c in METRIC_COLS]
    st_path = DATA_DIR / "ragas_summary_by_type.csv"
    with open(st_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=type_cols, extrasaction="ignore")
        w.writeheader()
        for row in summary_type:
            w.writerow({k: ("" if row.get(k) is None else row.get(k, "")) for k in type_cols})
    print(f"Summary by type: {st_path}")

    # ── Summary by mode × multi_hop ───────────────────────────────────────────
    summary_hop = []
    for mode in MODES:
        for mh in [True, False]:
            mh_str = str(mh)
            subset = [r for r in all_rows if r.get("mode") == mode and r.get("multi_hop") == mh_str]
            if not subset:
                continue
            row = {"mode": mode, "multi_hop": mh_str, "n": len(subset)}
            for col in METRIC_COLS:
                vals = [_safe_float(r.get(col)) for r in subset]
                row[col + "_mean"] = _avg(vals)
            summary_hop.append(row)

    hop_cols = ["mode", "multi_hop", "n"] + [c + "_mean" for c in METRIC_COLS]
    sh_path = DATA_DIR / "ragas_summary_by_multihop.csv"
    with open(sh_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=hop_cols, extrasaction="ignore")
        w.writeheader()
        for row in summary_hop:
            w.writerow({k: ("" if row.get(k) is None else row.get(k, "")) for k in hop_cols})
    print(f"Summary by multi_hop: {sh_path}")

    # ── Print summary table ───────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RAGAS RESULTS SUMMARY (mean per mode)")
    print("=" * 70)
    header = f"{'Mode':<12} {'Faithfulness':>13} {'Ans.Relev':>10} {'Ctx.Prec':>9} {'Ctx.Rec':>8} {'Hop-Acc':>8}"
    print(header)
    print("-" * 70)
    for row in summary_mode:
        def fmt(key):
            v = row.get(key + "_mean")
            n_v = row.get(key + "_n", 0)
            if v is None:
                return "N/A      "
            return f"{v:.4f}({n_v:2d})"
        print(f"{row['mode']:<12} {fmt('ragas_faithfulness'):>13} {fmt('ragas_answer_relevancy'):>10} "
              f"{fmt('ragas_context_precision'):>9} {fmt('ragas_context_recall'):>8} "
              f"{fmt('reaq_hop_accuracy_corrected'):>8}")


if __name__ == "__main__":
    main()
