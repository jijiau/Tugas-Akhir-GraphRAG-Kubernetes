"""
scripts/statistical_test.py
Statistical significance testing for GraphRAG vs Vector RAG vs Vanilla LLM.

Tests:
  1. Wilcoxon signed-rank test (scipy) — non-parametric paired test, no normality assumption
  2. Paired bootstrap (1000 iterations) — resamples 97 fixture pairs, builds CI + p-value

Comparisons:
  - GraphRAG vs Vector RAG  (primary — thesis main claim)
  - GraphRAG vs Vanilla LLM (secondary)
  - Each ablation vs GraphRAG baseline (tertiary — validates ablation contribution)

Metrics tested: precision@k, recall@k, ndcg@k, retq_score, ansq_score, reaq_score, total_score

Usage:
  python scripts/statistical_test.py
  python scripts/statistical_test.py --bootstrap-iter 2000  # more iterations
  python scripts/statistical_test.py --alpha 0.05           # significance level (default 0.05)
"""
import sys
import csv
import math
import random
import argparse
from pathlib import Path

try:
    from scipy import stats as scipy_stats
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False
    print("[WARN] scipy tidak terinstal — Wilcoxon test dilewati. Jalankan: pip install scipy")

ROOT = Path(__file__).parent.parent

# ── File paths ────────────────────────────────────────────────────────────────
GRAPHRAG_CSV  = ROOT / "data" / "eval_results_v12.csv"
VECTOR_CSV    = ROOT / "data" / "eval_results_vector_v2.csv"
LLM_CSV       = ROOT / "data" / "eval_results_llm_v2.csv"

ABLATION_CSVS = {
    "A1 (no_phase1)":       ROOT / "data" / "eval_results_ablation_A1.csv",
    "A2 (no_multihop)":     ROOT / "data" / "eval_results_ablation_A2.csv",
    "A3 (depth=2 fixed)":   ROOT / "data" / "eval_results_ablation_A3.csv",
    "A4 (depth=3 fixed)":   ROOT / "data" / "eval_results_ablation_A4.csv",
    "A5 (no_yaml_layer3)":  ROOT / "data" / "eval_results_ablation_A5.csv",
    "A6c (no_multi_entity)":ROOT / "data" / "eval_results_ablation_A6c.csv",
}

METRICS = [
    ("retq_precision_at_k", "Precision@k"),
    ("retq_recall_at_k",    "Recall@k"),
    ("retq_ndcg_at_k",      "NDCG@k"),
    ("retq_retq_score",     "RetQ"),
    ("ansq_ansq_score",     "AnsQ"),
    ("reaq_reaq_score",     "ReaQ"),
    ("total_score",         "Total"),
]


# ── I/O helpers ───────────────────────────────────────────────────────────────

def load_scores(path: Path, id_order: list | None = None) -> dict[str, dict]:
    """
    Load CSV → {fixture_id: {col: float}} dict.
    If id_order is given, returns only those IDs in that order.
    """
    data = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                fid = row["id"]
                data[fid] = {}
                for col, _ in METRICS:
                    v = row.get(col, "").strip()
                    data[fid][col] = float(v) if v else None
    except FileNotFoundError:
        return {}

    if id_order is not None:
        return {fid: data[fid] for fid in id_order if fid in data}
    return data


def paired_scores(data_a: dict, data_b: dict, col: str) -> tuple[list, list]:
    """
    Return two aligned lists of scores for fixtures present in both datasets.
    """
    common = [fid for fid in data_a if fid in data_b
              and data_a[fid].get(col) is not None
              and data_b[fid].get(col) is not None]
    a = [data_a[fid][col] for fid in common]
    b = [data_b[fid][col] for fid in common]
    return a, b


# ── Statistical tests ─────────────────────────────────────────────────────────

def wilcoxon_test(a: list, b: list) -> tuple[float, float]:
    """
    Wilcoxon signed-rank test on paired samples a and b.
    Returns (statistic, p_value). Requires scipy.
    """
    if not _SCIPY_OK:
        return float("nan"), float("nan")
    diffs = [x - y for x, y in zip(a, b)]
    if all(d == 0 for d in diffs):
        return float("nan"), 1.0
    stat, p = scipy_stats.wilcoxon(a, b, alternative="greater")
    return stat, p


def bootstrap_ci(a: list, b: list, n_iter: int = 1000, alpha: float = 0.05,
                 rng_seed: int = 42) -> tuple[float, float, float, float]:
    """
    Paired bootstrap: resample n_iter times with replacement.
    Returns (mean_diff, ci_low, ci_high, p_value).
    p_value = fraction of bootstrap samples where diff ≤ 0 (one-tailed: a > b).
    """
    rng = random.Random(rng_seed)
    n = len(a)
    observed_diff = sum(a) / n - sum(b) / n

    diffs = []
    for _ in range(n_iter):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        sample_a = [a[i] for i in indices]
        sample_b = [b[i] for i in indices]
        diffs.append(sum(sample_a) / n - sum(sample_b) / n)

    diffs_sorted = sorted(diffs)
    lo_idx = int(math.floor(alpha / 2 * n_iter))
    hi_idx = int(math.ceil((1 - alpha / 2) * n_iter)) - 1
    ci_low  = diffs_sorted[max(0, lo_idx)]
    ci_high = diffs_sorted[min(n_iter - 1, hi_idx)]

    # p-value: proportion of bootstrap samples where A is NOT better than B
    p_value = sum(1 for d in diffs if d <= 0) / n_iter

    return observed_diff, ci_low, ci_high, p_value


# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_p(p: float) -> str:
    if math.isnan(p): return "  n/a  "
    if p < 0.001:     return " <0.001"
    return f" {p:.3f} "


def sig_stars(p: float) -> str:
    if math.isnan(p): return "   "
    if p < 0.001: return "***"
    if p < 0.01:  return " **"
    if p < 0.05:  return "  *"
    return "   "


# ── Main ──────────────────────────────────────────────────────────────────────

def run_comparison(label: str, data_a: dict, data_b: dict, n_iter: int, alpha: float):
    """Print a full comparison table for one pair of systems."""
    W = 100
    print()
    print("=" * W)
    print(f"  {label}")
    print("=" * W)
    print(
        f"  {'Metric':<16}  {'Mean A':>7}  {'Mean B':>7}  {'d(A-B)':>8}"
        f"  {'Wilcoxon p':>11}  {'Bootstrap p':>12}  {'95% CI':>20}  Sig"
    )
    print("  " + "-" * (W - 2))

    results = []
    for col, label_m in METRICS:
        a, b = paired_scores(data_a, data_b, col)
        if not a:
            continue
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        diff   = mean_a - mean_b

        w_stat, w_p = wilcoxon_test(a, b)
        obs_diff, ci_lo, ci_hi, bs_p = bootstrap_ci(a, b, n_iter=n_iter, alpha=alpha)

        stars = sig_stars(min(w_p, bs_p))
        ci_str = f"[{ci_lo:+.4f}, {ci_hi:+.4f}]"

        print(
            f"  {label_m:<16}  {mean_a:>7.4f}  {mean_b:>7.4f}  {diff:>+8.4f}"
            f"  {fmt_p(w_p):>11}  {fmt_p(bs_p):>12}  {ci_str:>20}  {stars}"
        )
        results.append((label_m, diff, w_p, bs_p, ci_lo, ci_hi))

    print()
    print(f"  Significance: *** p<0.001  ** p<0.01  * p<0.05  (n={len(a)}, bootstrap {n_iter} iter)")
    print(f"  One-tailed test: H1 = System A scores higher than System B")
    return results


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Statistical significance testing")
    parser.add_argument("--bootstrap-iter", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    n_iter = args.bootstrap_iter
    alpha  = args.alpha

    # ── Load baseline systems ─────────────────────────────────────────────────
    graphrag = load_scores(GRAPHRAG_CSV)
    vector   = load_scores(VECTOR_CSV)
    llm      = load_scores(LLM_CSV)

    if not graphrag:
        sys.exit(f"[ERROR] Tidak dapat membaca {GRAPHRAG_CSV}")
    if not vector:
        sys.exit(f"[ERROR] Tidak dapat membaca {VECTOR_CSV}")

    id_order = list(graphrag.keys())

    W = 100
    print()
    print("=" * W)
    print("  STATISTICAL SIGNIFICANCE TESTING — GraphRAG Kubernetes")
    print(f"  Bootstrap iterations: {n_iter}  |  Alpha: {alpha}  |  n fixtures: {len(id_order)}")
    print("=" * W)

    # ── Primary comparison: GraphRAG vs Vector RAG ────────────────────────────
    r1 = run_comparison(
        "Comparison 1: GraphRAG (v12) vs Vector RAG (v2)",
        graphrag, vector, n_iter, alpha,
    )

    # ── Secondary comparison: GraphRAG vs Vanilla LLM ────────────────────────
    if llm:
        r2 = run_comparison(
            "Comparison 2: GraphRAG (v12) vs Vanilla LLM (v2)",
            graphrag, llm, n_iter, alpha,
        )

    # ── Ablation comparisons: baseline vs each ablation ───────────────────────
    print()
    print("=" * W)
    print("  Ablation Study — Wilcoxon p-values (GraphRAG baseline vs ablated variant)")
    print("  H₁: baseline scores higher than ablation (removing component degrades performance)")
    print("=" * W)

    metric_cols = ["retq_retq_score", "ansq_ansq_score", "reaq_reaq_score", "total_score"]
    metric_names = ["RetQ", "AnsQ", "ReaQ", "Total"]

    header = f"  {'Ablation':<26}" + "".join(f"  {n:>10}" for n in metric_names)
    print(header)
    print("  " + "-" * (26 + 13 * len(metric_cols)))

    for abl_label, abl_path in ABLATION_CSVS.items():
        abl_data = load_scores(abl_path)
        if not abl_data:
            print(f"  {abl_label:<26}  [file tidak ditemukan]")
            continue

        row_str = f"  {abl_label:<26}"
        for col in metric_cols:
            a, b = paired_scores(graphrag, abl_data, col)
            if not a:
                row_str += f"  {'n/a':>10}"
                continue
            _, w_p = wilcoxon_test(a, b)
            _, _, _, bs_p = bootstrap_ci(a, b, n_iter=n_iter, alpha=alpha)
            p_display = min(w_p, bs_p)
            stars = sig_stars(p_display)
            row_str += f"  {fmt_p(p_display).strip():>7}{stars}"
        print(row_str)

    print()
    print(f"  Significance: *** p<0.001  ** p<0.01  * p<0.05  (n=97, bootstrap {n_iter} iter)")
    print()

    # ── Save summary CSV ──────────────────────────────────────────────────────
    out_path = ROOT / "data" / "statistical_test_results.csv"
    col_map = {label_m: col for col, label_m in METRICS}
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "comparison", "metric", "mean_graphrag", "mean_baseline", "delta",
            "wilcoxon_p", "bootstrap_p", "ci_low", "ci_high", "significant_0.05"
        ])
        for label_m, diff, w_p, bs_p, ci_lo, ci_hi in r1:
            col = col_map.get(label_m, "total_score")
            a_vals, b_vals = paired_scores(graphrag, vector, col)
            mean_a = round(sum(a_vals) / len(a_vals), 4) if a_vals else ""
            mean_b = round(sum(b_vals) / len(b_vals), 4) if b_vals else ""
            p_min  = min(w_p if not math.isnan(w_p) else 1.0, bs_p)
            writer.writerow([
                "GraphRAG_vs_VectorRAG", label_m, mean_a, mean_b,
                round(diff, 4),
                round(w_p, 4) if not math.isnan(w_p) else "",
                round(bs_p, 4),
                round(ci_lo, 4), round(ci_hi, 4),
                "yes" if p_min < 0.05 else "no",
            ])
    print(f"  Summary saved -> {out_path}")
    print("=" * W)


if __name__ == "__main__":
    main()
