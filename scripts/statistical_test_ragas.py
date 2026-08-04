"""
scripts/statistical_test_ragas.py
Statistical significance testing untuk metrik RAGAS individual.

Metrik diuji (family per perbandingan):
  GraphRAG vs Vector  : faithfulness, answer_relevancy, context_precision, context_recall  (4 metrik)
  GraphRAG vs LLM     : answer_relevancy saja (FS/CP/CR = N/A utk LLM tanpa retrieval)

Test: Wilcoxon signed-rank (two-tailed) + paired bootstrap 95% CI + Holm-Bonferroni.
Two-tailed karena arah GraphRAG tidak seragam (AR lebih rendah, FS/CP/CR bervariasi).

Input : data/ragas_results_{graphrag,vector,llm}.csv
Output: data/statistical_test_ragas.csv

Usage:
  python scripts/statistical_test_ragas.py
  python scripts/statistical_test_ragas.py --bootstrap-iter 2000
"""
import sys
import csv
import math
import random
import argparse
import io
from pathlib import Path

try:
    from scipy import stats as scipy_stats
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False
    print("[WARN] scipy tidak terinstal — Wilcoxon test dilewati.")

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

RAGAS_METRICS = [
    ("ragas_faithfulness",        "Faithfulness (FS)"),
    ("ragas_answer_relevancy",    "Answer Relevancy (AR)"),
    ("ragas_context_precision",   "Context Precision (CP)"),
    ("ragas_context_recall",      "Context Recall (CR)"),
]

# ── I/O ───────────────────────────────────────────────────────────────────────

def _read_csv_safe(path: Path) -> dict:
    """Read RAGAS CSV → {id: {col: float|None}}. NUL-byte safe."""
    if not path.exists():
        return {}
    content = path.read_bytes().replace(b"\x00", b"")
    data = {}
    for row in csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))):
        fid = row.get("id", "").strip()
        if not fid:
            continue
        data[fid] = {}
        for col, val in row.items():
            v = (val or "").strip()
            try:
                data[fid][col] = float(v) if v else None
            except ValueError:
                data[fid][col] = None
    return data


def paired_scores(a: dict, b: dict, col: str):
    """Return aligned float lists for fixtures non-null in both."""
    common = [fid for fid in a if fid in b
              and a[fid].get(col) is not None
              and b[fid].get(col) is not None]
    return [a[fid][col] for fid in common], [b[fid][col] for fid in common], len(common)


# ── Tests ─────────────────────────────────────────────────────────────────────

def wilcoxon_test(sa: list, sb: list):
    if not _SCIPY_OK or not sa:
        return float("nan"), float("nan")
    diffs = [x - y for x, y in zip(sa, sb)]
    if all(d == 0 for d in diffs):
        return float("nan"), 1.0
    stat, p = scipy_stats.wilcoxon(sa, sb, alternative="two-sided")
    return stat, p


def bootstrap_ci(sa: list, sb: list, n_iter: int = 1000, alpha: float = 0.05,
                 seed: int = 42):
    if not sa:
        return float("nan"), float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(sa)
    obs = sum(sa) / n - sum(sb) / n
    diffs = []
    for _ in range(n_iter):
        idx = [rng.randint(0, n - 1) for _ in range(n)]
        diffs.append(sum(sa[i] for i in idx) / n - sum(sb[i] for i in idx) / n)
    diffs.sort()
    lo = diffs[max(0, int(math.floor(alpha / 2 * n_iter)))]
    hi = diffs[min(n_iter - 1, int(math.ceil((1 - alpha / 2) * n_iter)) - 1)]
    # two-tailed p: fraction where bootstrap diff has opposite sign from observed
    p = sum(1 for d in diffs if (obs >= 0 and d <= 0) or (obs < 0 and d >= 0)) / n_iter
    return obs, lo, hi, p


def holm_bonferroni(pvals: list):
    k = len(pvals)
    indexed = [(p, i) for i, p in enumerate(pvals) if not math.isnan(p)]
    indexed.sort(key=lambda x: x[0])
    corrected = [float("nan")] * k
    running_max = 0.0
    for rank, (p, orig) in enumerate(indexed):
        adj = min(1.0, p * (k - rank))
        running_max = max(running_max, adj)
        corrected[orig] = running_max
    return corrected


# ── Formatting ────────────────────────────────────────────────────────────────

def _fp(p):
    if math.isnan(p): return "   n/a  "
    if p < 0.001:     return "  <0.001"
    return f"  {p:.3f} "


def _stars(p):
    if math.isnan(p): return "   "
    if p < 0.001: return "***"
    if p < 0.01:  return " **"
    if p < 0.05:  return "  *"
    return " n.s"


# ── Comparison block ──────────────────────────────────────────────────────────

def run_comparison(label: str, data_a: dict, data_b: dict,
                   metrics: list, n_iter: int, alpha: float):
    W = 108
    print()
    print("=" * W)
    print(f"  {label}")
    print("=" * W)
    hdr = (f"  {'Metrik':<26}  {'Mean A':>7}  {'Mean B':>7}  {'Δ(A−B)':>8}"
           f"  {'Wilcoxon p':>10}  {'Bootstrap p':>11}  {'95% CI':>22}  {'p-Holm':>8}  Sig  n")
    print(hdr)
    print("  " + "-" * (W - 2))

    raw = []
    raw_p = []
    for col, lbl in metrics:
        sa, sb, n = paired_scores(data_a, data_b, col)
        if not sa:
            raw.append((lbl, col, [], [], float("nan"), float("nan"), float("nan"),
                        float("nan"), float("nan"), 0))
            raw_p.append(float("nan"))
            continue
        ma, mb = sum(sa) / len(sa), sum(sb) / len(sb)
        _, wp = wilcoxon_test(sa, sb)
        obs, lo, hi, bp = bootstrap_ci(sa, sb, n_iter=n_iter, alpha=alpha)
        p_min = min(p for p in [wp, bp] if not math.isnan(p)) \
                if not (math.isnan(wp) and math.isnan(bp)) else float("nan")
        raw.append((lbl, col, sa, sb, ma, mb, wp, bp, lo, hi, n))
        raw_p.append(p_min)

    holm = holm_bonferroni(raw_p)

    results = []
    for i, entry in enumerate(raw):
        lbl, col = entry[0], entry[1]
        sa = entry[2]
        if not sa:
            print(f"  {lbl:<26}  {'n/a':>7}  {'n/a':>7}  {'n/a':>8}  {'n/a':>10}  {'n/a':>11}  {'n/a':>22}  {'n/a':>8}")
            continue
        ma, mb, wp, bp, lo, hi, n = entry[4], entry[5], entry[6], entry[7], entry[8], entry[9], entry[10]
        diff = ma - mb
        ph = holm[i]
        ci_str = f"[{lo:+.4f}, {hi:+.4f}]"
        print(f"  {lbl:<26}  {ma:>7.4f}  {mb:>7.4f}  {diff:>+8.4f}"
              f"  {_fp(wp):>10}  {_fp(bp):>11}  {ci_str:>22}  {_fp(ph):>8}  {_stars(ph)}  {n}")
        results.append((lbl, col, ma, mb, diff, wp, bp, lo, hi, ph, n))

    print()
    print(f"  Two-tailed Wilcoxon + paired bootstrap {n_iter} iter. "
          f"Holm-Bonferroni keluarga {len([m for m in metrics])} metrik.")
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-iter", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    graphrag = _read_csv_safe(DATA / "ragas_results_graphrag.csv")
    vector   = _read_csv_safe(DATA / "ragas_results_vector.csv")
    llm      = _read_csv_safe(DATA / "ragas_results_llm.csv")

    if not graphrag:
        sys.exit("[ERROR] ragas_results_graphrag.csv tidak ditemukan / kosong.")

    print()
    print("=" * 108)
    print("  STATISTICAL SIGNIFICANCE — RAGAS Metrics (GraphRAG Kubernetes)")
    print(f"  Bootstrap: {args.bootstrap_iter} iter  |  Alpha: {args.alpha}  |  Two-tailed")
    print("=" * 108)

    # Comparison 1: GraphRAG vs Vector — semua 4 metrik RAGAS
    r1 = run_comparison(
        "Perbandingan 1: GraphRAG vs Vector RAG  (4 metrik, family Holm)",
        graphrag, vector, RAGAS_METRICS, args.bootstrap_iter, args.alpha,
    )

    # Comparison 2: GraphRAG vs LLM — hanya AR (FS/CP/CR = N/A)
    ar_only = [m for m in RAGAS_METRICS if m[0] == "ragas_answer_relevancy"]
    r2 = run_comparison(
        "Perbandingan 2: GraphRAG vs Vanilla LLM  (AR saja — FS/CP/CR N/A utk LLM)",
        graphrag, llm, ar_only, args.bootstrap_iter, args.alpha,
    )

    # ── Save CSV ──────────────────────────────────────────────────────────────
    out = DATA / "statistical_test_ragas.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["comparison", "metric", "mean_graphrag", "mean_baseline",
                    "delta", "wilcoxon_p", "bootstrap_p", "ci_low", "ci_high",
                    "p_holm", "sig_holm_0.05", "n_pairs"])
        for comp_lbl, results in [("GraphRAG_vs_VectorRAG", r1), ("GraphRAG_vs_VanillaLLM", r2)]:
            if not results:
                continue
            for lbl, col, ma, mb, diff, wp, bp, lo, hi, ph, n in results:
                w.writerow([
                    comp_lbl, lbl,
                    round(ma, 4), round(mb, 4), round(diff, 4),
                    "" if math.isnan(wp) else round(wp, 4),
                    "" if math.isnan(bp) else round(bp, 4),
                    round(lo, 4), round(hi, 4),
                    "" if math.isnan(ph) else round(ph, 4),
                    "yes" if (not math.isnan(ph) and ph < 0.05) else "no",
                    n,
                ])
    print(f"\n  Saved → {out}")
    print("=" * 108)


if __name__ == "__main__":
    main()
