"""
scripts/analyze_ragas.py — Langkah 3: Analisis deskriptif hasil RAGAS.

Prints:
  1. Per-mode summary (GraphRAG vs Vector vs LLM)
  2. Per-type breakdown (graphrag + vector)
  3. Per-multihop breakdown
  4. Triangulation: RAGAS vs node-based RetQ per type

Usage:
  python scripts/analyze_ragas.py
"""
import csv, io, math
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

RAGAS_COLS = [
    ("ragas_faithfulness",      "Faithfulness"),
    ("ragas_answer_relevancy",  "Ans.Relevancy"),
    ("ragas_context_precision", "Ctx.Precision"),
    ("ragas_context_recall",    "Ctx.Recall"),
    ("reaq_hop_accuracy_corrected", "Hop-Acc"),
]


def _read(path):
    if not path.exists():
        return []
    content = path.read_bytes().replace(b"\x00", b"")
    return list(csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))))


def _f(val):
    if val in (None, ""):
        return None
    try:
        v = float(val)
        return None if math.isnan(v) else v
    except (ValueError, TypeError):
        return None


def _avg(vals):
    v = [x for x in vals if x is not None]
    return sum(v) / len(v) if v else None


def _fmt(v, n=None):
    if v is None:
        return "  N/A   "
    s = f"{v:.4f}"
    if n is not None:
        s += f"({n:2d})"
    return s


def _section(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def main():
    all_rows = _read(DATA / "ragas_results_all.csv")
    if not all_rows:
        print("[ERROR] ragas_results_all.csv tidak ditemukan. Jalankan aggregate_ragas.py dulu.")
        return

    modes = ["graphrag", "vector", "llm"]

    # ── 1. Per-mode ───────────────────────────────────────────────────────────
    _section("1. PER-MODE SUMMARY")
    hdr = f"  {'Mode':<12}" + "".join(f"  {lbl:>16}" for _, lbl in RAGAS_COLS)
    print(hdr)
    print("  " + "-" * (12 + 18 * len(RAGAS_COLS)))
    for mode in modes:
        rows = [r for r in all_rows if r.get("mode") == mode]
        line = f"  {mode:<12}"
        for col, _ in RAGAS_COLS:
            vals = [_f(r.get(col)) for r in rows]
            v = _avg(vals)
            n = sum(1 for x in vals if x is not None)
            line += f"  {_fmt(v, n):>16}"
        print(line)

    # ── 2. Per-type (graphrag vs vector) ──────────────────────────────────────
    _section("2. PER-TYPE: GraphRAG vs Vector  (metrik utama: AR, CP, CR, Hop-Acc)")
    types = sorted(set(r.get("type","") for r in all_rows if r.get("type")))
    key_cols = [("ragas_answer_relevancy","AR"), ("ragas_context_precision","CP"),
                ("ragas_context_recall","CR"), ("reaq_hop_accuracy_corrected","Hop-Acc")]
    hdr2 = f"  {'Type':<16}" + "".join(
        f"  {'GR-'+lbl:>9}  {'V-'+lbl:>9}" for _, lbl in key_cols)
    print(hdr2)
    print("  " + "-" * 70)
    for qtype in types:
        line = f"  {qtype:<16}"
        for col, _ in key_cols:
            gr = [_f(r.get(col)) for r in all_rows if r.get("mode")=="graphrag" and r.get("type")==qtype]
            vc = [_f(r.get(col)) for r in all_rows if r.get("mode")=="vector"   and r.get("type")==qtype]
            vgr = _avg(gr); vvc = _avg(vc)
            line += f"  {_fmt(vgr):>9}  {_fmt(vvc):>9}"
        print(line)

    # ── 3. Per-multihop ───────────────────────────────────────────────────────
    _section("3. PER-MULTI_HOP: GraphRAG vs Vector")
    hdr3 = f"  {'Mode':<12}  {'multi_hop':<10}" + "".join(
        f"  {lbl:>14}" for _, lbl in RAGAS_COLS[:4])
    print(hdr3)
    print("  " + "-" * 70)
    for mode in ["graphrag", "vector", "llm"]:
        for mh in ["True", "False"]:
            rows = [r for r in all_rows if r.get("mode")==mode and r.get("multi_hop")==mh]
            if not rows:
                continue
            line = f"  {mode:<12}  {mh:<10}"
            for col, _ in RAGAS_COLS[:4]:
                vals = [_f(r.get(col)) for r in rows]
                line += f"  {_fmt(_avg(vals)):>14}"
            print(line)

    # ── 4. Triangulasi RAGAS vs node-based per type (graphrag only) ───────────
    _section("4. TRIANGULASI: RAGAS Context Precision vs Node-based RetQ  (graphrag, per type)")
    nb_files = {
        "graphrag": DATA / "eval_results_graphrag_final.csv",
        "vector":   DATA / "eval_results_vector_final.csv",
    }
    nb = {}
    for mode, fp in nb_files.items():
        if fp.exists():
            content = fp.read_bytes().replace(b"\x00", b"")
            for row in csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))):
                nb[(mode, row["id"])] = row

    print(f"  {'Type':<16}  {'RAGAS-CP':>9}  {'RAGAS-CR':>9}  {'NodeF1@k':>9}  {'NDCG@k':>9}  {'PathCov':>9}")
    print("  " + "-" * 65)
    for qtype in types:
        ragas_cp, ragas_cr, f1s, ndcgs, pcovs = [], [], [], [], []
        for r in all_rows:
            if r.get("mode") != "graphrag" or r.get("type") != qtype:
                continue
            ragas_cp.append(_f(r.get("ragas_context_precision")))
            ragas_cr.append(_f(r.get("ragas_context_recall")))
            nb_row = nb.get(("graphrag", r["id"]), {})
            f1s.append(_f(nb_row.get("retq_f1_at_k")))
            ndcgs.append(_f(nb_row.get("retq_ndcg_at_k")))
            pcovs.append(_f(nb_row.get("retq_path_coverage")))
        print(f"  {qtype:<16}  {_fmt(_avg(ragas_cp)):>9}  {_fmt(_avg(ragas_cr)):>9}"
              f"  {_fmt(_avg(f1s)):>9}  {_fmt(_avg(ndcgs)):>9}  {_fmt(_avg(pcovs)):>9}")

    print("\n  Catatan: RAGAS CP/CR = penilaian semantik LLM-judge (gpt-4o-mini).")
    print("           Node-based F1/NDCG = overlap node KG vs expected path (struktural).")
    print("           Divergensi realworld: RAGAS CP~0 tapi node-based F1 juga rendah -> konsisten.")
    print("           Divergensi relationship/conceptual: RAGAS CP rendah meski F1 tinggi -> domain-mismatch.")


if __name__ == "__main__":
    main()
