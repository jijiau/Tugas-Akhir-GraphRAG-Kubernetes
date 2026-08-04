"""
scripts/statistical_test.py
Statistical significance testing for GraphRAG vs Vector RAG vs Vanilla LLM.

Tests:
  1. Wilcoxon signed-rank test (scipy) — non-parametric paired test, no normality assumption
  2. Paired bootstrap (1000 iterations) — resamples fixture pairs, builds CI + p-value

Comparisons:
  - GraphRAG vs Vector RAG  (primary — thesis main claim)
  - GraphRAG vs Vanilla LLM (secondary)
  - Each ablation vs GraphRAG baseline (tertiary — validates ablation contribution)

Metrics tested (shared-target, head-to-head):
  ansq_score, retq_score, reaq_score (= RAGAS Faithfulness after join), syntactic_validity

Diagnostics (mean only, not significance-tested):
  precision, recall, f1 (RetQ components), hop_accuracy (GraphRAG-only)

N/A handling: paired_scores() already drops fixture pairs where either system has None.
This correctly excludes: ReaQ for Vanilla LLM, HopAcc for path-empty fixtures.

Usage:
  python scripts/statistical_test.py
  python scripts/statistical_test.py --bootstrap-iter 2000
  python scripts/statistical_test.py --alpha 0.05
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

# ── File paths (output dari re-run final) ─────────────────────────────────────
GRAPHRAG_CSV  = ROOT / "data" / "eval_results_graphrag_final.csv"
VECTOR_CSV    = ROOT / "data" / "eval_results_vector_final.csv"
LLM_CSV       = ROOT / "data" / "eval_results_llm_final.csv"

ABLATION_CSVS = {
    "A1 (no_phase1)":        ROOT / "data" / "eval_results_ablation_A1.csv",
    "A2 (no_multihop)":      ROOT / "data" / "eval_results_ablation_A2.csv",
    "A3 (depth=2 fixed)":    ROOT / "data" / "eval_results_ablation_A3.csv",
    "A4 (depth=3 fixed)":    ROOT / "data" / "eval_results_ablation_A4.csv",
    "A5 (no_yaml_layer3)":   ROOT / "data" / "eval_results_ablation_A5.csv",
    "A6c (no_multi_entity)": ROOT / "data" / "eval_results_ablation_A6c.csv",
    "A7 (has_property_only)": ROOT / "data" / "eval_results_ablation_A7.csv",  # F14: 18-edge vs HAS_PROPERTY (T1)
}

# ── Inferential metrics (Wilcoxon + bootstrap + Holm) ─────────────────────────
# Shared-target metrics — meaningful for all three systems (LLM, Vector, GraphRAG).
# reaq_reaq_score = RAGAS Faithfulness (joined from recompute_ragas.py; N/A for LLM).
# Hop Accuracy excluded: graph-intrinsic, only meaningful for systems with explicit traversal.
# RGA dropped: arbitrary 0.5 threshold composite with no literature citation for threshold.
METRICS = [
    ("ansq_ansq_score",          "AnsQ"),
    ("retq_retq_score",          "RetQ"),
    ("reaq_reaq_score",          "ReaQ (Faithful.)"),
    ("ansq_syntactic_validity",  "Syntactic Valid."),
]

# ── Diagnostic metrics (reported mean only, NOT significance-tested) ──────────
# Paired N/A drop applies: pairs where either system has None are excluded per metric.
DIAGNOSTICS = [
    ("retq_precision",         "Precision"),
    ("retq_recall",            "Recall"),
    ("retq_f1",                "F1"),
    ("reaq_hop_accuracy",      "Hop Acc (GraphRAG-only)"),
]


# ── I/O helpers ───────────────────────────────────────────────────────────────

def load_scores(path: Path, id_order: list | None = None) -> dict[str, dict]:
    """
    Load CSV → {fixture_id: {col: float}} dict.
    Memuat seluruh kolom numerik agar ablation (PathCov/HopAcc) dan
    diagnostik tetap tersedia meski tidak ada di METRICS.
    If id_order is given, returns only those IDs in that order.
    """
    data = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                fid = row["id"]
                data[fid] = {}
                for col, val in row.items():
                    v = val.strip() if val else ""
                    try:
                        data[fid][col] = float(v) if v else None
                    except ValueError:
                        data[fid][col] = None
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


# ── Holm-Bonferroni correction ────────────────────────────────────────────────

def holm_bonferroni(p_values: list[float]) -> list[float]:
    """
    Apply Holm-Bonferroni step-down correction to a family of p-values.
    Returns corrected p-values in the SAME order as input.
    NaN p-values (missing data) are passed through unchanged.
    """
    k = len(p_values)
    # pair each p with its original index, filter out nan
    indexed = [(p, i) for i, p in enumerate(p_values) if not math.isnan(p)]
    indexed.sort(key=lambda x: x[0])  # sort ascending by p

    corrected = [float("nan")] * k
    running_max = 0.0
    for rank, (p, orig_idx) in enumerate(indexed):
        adjusted = p * (k - rank)
        running_max = max(running_max, adjusted)
        corrected[orig_idx] = min(1.0, running_max)

    return corrected


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
    """
    Print a full comparison table for one pair of systems.
    Includes Holm-Bonferroni correction across the 7 inferential metrics.
    """
    W = 110
    print()
    print("=" * W)
    print(f"  {label}")
    print("=" * W)
    print(
        f"  {'Metric':<18}  {'Mean A':>7}  {'Mean B':>7}  {'d(A-B)':>8}"
        f"  {'Wilcoxon p':>11}  {'Bootstrap p':>12}  {'95% CI':>22}  {'p-Holm':>8}  Sig"
    )
    print("  " + "-" * (W - 2))

    # First pass: collect raw p-values for Holm correction
    raw_results = []
    raw_p_min   = []
    for col, label_m in METRICS:
        a, b = paired_scores(data_a, data_b, col)
        if not a:
            raw_results.append((label_m, col, [], [], float("nan"), float("nan"), float("nan"), float("nan"), float("nan")))
            raw_p_min.append(float("nan"))
            continue
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        diff   = mean_a - mean_b
        w_stat, w_p = wilcoxon_test(a, b)
        obs_diff, ci_lo, ci_hi, bs_p = bootstrap_ci(a, b, n_iter=n_iter, alpha=alpha)
        p_min = min(p for p in [w_p, bs_p] if not math.isnan(p)) if not (math.isnan(w_p) and math.isnan(bs_p)) else float("nan")
        raw_results.append((label_m, col, a, b, mean_a - mean_b, w_p, bs_p, ci_lo, ci_hi))
        raw_p_min.append(p_min)

    holm_ps = holm_bonferroni(raw_p_min)

    results = []
    n_samples = 0  # updated to max n across metrics (retq/ansq/reaq always 97)
    for i, (label_m, col, a, b, diff, w_p, bs_p, ci_lo, ci_hi) in enumerate(raw_results):
        if not a:
            print(f"  {label_m:<18}  {'n/a':>7}  {'n/a':>7}  {'n/a':>8}  {'n/a':>11}  {'n/a':>12}  {'n/a':>22}  {'n/a':>8}")
            continue
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        n_samples = max(n_samples, len(a))  # keep max (YAML-only metrics have smaller n)
        ci_str  = f"[{ci_lo:+.4f}, {ci_hi:+.4f}]"
        p_holm  = holm_ps[i]
        stars   = sig_stars(p_holm)
        p_holm_str = f" <0.001" if p_holm < 0.001 else f" {p_holm:.3f} " if not math.isnan(p_holm) else "  n/a  "
        print(
            f"  {label_m:<18}  {mean_a:>7.4f}  {mean_b:>7.4f}  {diff:>+8.4f}"
            f"  {fmt_p(w_p):>11}  {fmt_p(bs_p):>12}  {ci_str:>22}  {p_holm_str:>8}  {stars}"
        )
        results.append((label_m, col, diff, w_p, bs_p, ci_lo, ci_hi, p_holm))

    print()
    print(f"  Significance: *** p<0.001  ** p<0.01  * p<0.05  (Holm-Bonferroni corrected, keluarga 4 faktor, n={n_samples}, bootstrap {n_iter} iter)")
    print(f"  One-tailed test: H₁ = System A scores higher than System B")

    # ── Diagnostic metrics (no significance test) ─────────────────────────────
    print()
    print(f"  Diagnostics (mean only — not significance-tested):")
    for col, label_m in DIAGNOSTICS:
        a, b = paired_scores(data_a, data_b, col)
        if not a:
            continue
        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        print(f"    {label_m:<18}  A={mean_a:.4f}  B={mean_b:.4f}  d={mean_a-mean_b:+.4f}")

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
        "Comparison 1: GraphRAG (final) vs Vector RAG (final)",
        graphrag, vector, n_iter, alpha,
    )

    # ── Secondary comparison: GraphRAG vs Vanilla LLM ────────────────────────
    r2 = None
    if llm:
        r2 = run_comparison(
            "Comparison 2: GraphRAG (final) vs Vanilla LLM (final)",
            graphrag, llm, n_iter, alpha,
        )

    # ── Ablation comparisons: baseline vs each ablation ───────────────────────
    print()
    print("=" * W)
    print("  Ablation Study — p-value per faktor (GraphRAG baseline vs ablated variant)")
    print("  H₁: baseline scores higher than ablation (removing component degrades performance)")
    print("=" * W)

    # Ablation cols: Hop Accuracy included (GraphRAG-baseline vs GraphRAG-ablated — both
    # have graph traversal, so hop_accuracy is valid for both). path_coverage and rga dropped.
    abl_cols  = ["ansq_ansq_score", "retq_retq_score", "reaq_reaq_score", "reaq_hop_accuracy"]
    abl_names = ["AnsQ", "RetQ", "ReaQ", "HopAcc"]

    header = f"  {'Ablation':<28}" + "".join(f"  {n:>9}" for n in abl_names)
    print(header)
    print("  " + "-" * (28 + 11 * len(abl_names)))

    for abl_label, abl_path in ABLATION_CSVS.items():
        abl_data = load_scores(abl_path)
        if not abl_data:
            print(f"  {abl_label:<28}  [file tidak ditemukan]")
            continue

        row_str = f"  {abl_label:<28}"
        for col in abl_cols:
            a, b = paired_scores(graphrag, abl_data, col)
            if not a:
                row_str += f"  {'n/a':>9}"
                continue
            _, w_p = wilcoxon_test(a, b)
            _, _, _, bs_p = bootstrap_ci(a, b, n_iter=n_iter, alpha=alpha)
            p_display = min(p for p in [w_p, bs_p] if not math.isnan(p)) if not (math.isnan(w_p) and math.isnan(bs_p)) else float("nan")
            stars = sig_stars(p_display)
            row_str += f"  {fmt_p(p_display).strip():>6}{stars}"
        print(row_str)

    print()
    n_fixtures = len(id_order)
    print(f"  Significance: *** p<0.001  ** p<0.01  * p<0.05  (n={n_fixtures}, bootstrap {n_iter} iter)")
    print()

    # ── Save summary CSV ──────────────────────────────────────────────────────
    out_path = ROOT / "data" / "statistical_test_results.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "comparison", "metric", "mean_graphrag", "mean_baseline", "delta",
            "wilcoxon_p", "bootstrap_p", "ci_low", "ci_high", "p_holm", "sig_holm_0.05"
        ])
        for comp_label, results in [("GraphRAG_vs_VectorRAG", r1), ("GraphRAG_vs_VanillaLLM", r2)]:
            if not results:
                continue
            for label_m, col, diff, w_p, bs_p, ci_lo, ci_hi, p_holm in results:
                a_vals, b_vals = paired_scores(graphrag, vector if "Vector" in comp_label else llm, col)
                mean_a = round(sum(a_vals) / len(a_vals), 4) if a_vals else ""
                mean_b = round(sum(b_vals) / len(b_vals), 4) if b_vals else ""
                writer.writerow([
                    comp_label, label_m, mean_a, mean_b,
                    round(diff, 4),
                    round(w_p, 4) if not math.isnan(w_p) else "",
                    round(bs_p, 4),
                    round(ci_lo, 4), round(ci_hi, 4),
                    round(p_holm, 4) if not math.isnan(p_holm) else "",
                    "yes" if (not math.isnan(p_holm) and p_holm < 0.05) else "no",
                ])
    print(f"  Summary saved -> {out_path}")
    print("=" * W)


if __name__ == "__main__":
    main()
