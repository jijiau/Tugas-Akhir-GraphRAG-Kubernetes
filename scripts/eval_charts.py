"""
scripts/eval_charts.py — Generate evaluation headline figures from _final CSVs.

Produces 8 figures to docs/TA-STI-template-1.0/images/ (180 dpi, bbox_inches=tight).
Figures are generated defensively: skip (log warning) if required data is missing or all-None.

Usage:
    python scripts/eval_charts.py

Figures:
    eval_systems_4metrics.png         — Grouped bar: 3 systems × {AnsQ, RetQ, ReaQ, HopAcc}
    eval_ablation_impact.png          — Bar: Δ GraphRAG-baseline vs A1–A7 ablation modes
    eval_t1_has_property_vs_18edge.png — Bar: A7 (HAS_PROPERTY-only) vs default per metric (T1/F14 proof)
    eval_by_intent.png                — Grouped bar: AnsQ/RetQ per intent category (GraphRAG)
    eval_prf_by_system.png            — Bar: Precision/Recall/F1 per system (GraphRAG + Vector)
    eval_ragas_faithfulness_dist.png  — Boxplot: RAGAS faithfulness distribution per system
    eval_significance_forest.png      — Forest plot: effect size + 95% CI from bootstrap
    eval_yaml_validity.png            — Bar: syntactic_validity vs schema_compliance (yaml_gen only)
"""

import sys
import csv
import math
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
IMAGES = ROOT / "docs" / "TA-STI-template-1.0" / "images"
IMAGES.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

DPI = 180
BBOX = "tight"

# ── Color palette (consistent across all figures) ──────────────────────────────
C_GRAPHRAG = "#2563EB"   # blue
C_VECTOR   = "#16A34A"   # green
C_LLM      = "#9333EA"   # purple
C_A7       = "#DC2626"   # red (HAS_PROPERTY-only contrast)
C_GRAY     = "#6B7280"


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _load_csv(path: Path) -> list:
    if not path.exists():
        log.warning(f"[SKIP] Missing: {path.name}")
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fv(row: dict, key: str):
    v = row.get(key, "")
    if v in ("", "None", None):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _ci95(vals):
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / len(vals)
    return 1.96 * math.sqrt(var) / math.sqrt(len(vals))


# ── Figure 1: Grouped bar 3 systems × 4 metrics ───────────────────────────────

def fig_systems_4metrics():
    graphrag = _load_csv(DATA / "eval_results_graphrag_final.csv")
    vector   = _load_csv(DATA / "eval_results_vector_final.csv")
    llm      = _load_csv(DATA / "eval_results_llm_final.csv")

    if not (graphrag or vector or llm):
        log.warning("[SKIP] fig_systems_4metrics: no data")
        return

    metrics = {
        "AnsQ": "ansq_ansq_score",
        "RetQ (F1)": "retq_f1",
        "ReaQ\n(RAGAS)": "reaq_reaq_score",
        "Hop\nAccuracy": "reaq_hop_accuracy",
    }
    systems = [("GraphRAG", graphrag, C_GRAPHRAG),
               ("Vector",   vector,   C_VECTOR),
               ("LLM",      llm,      C_LLM)]

    labels = list(metrics.keys())
    n = len(labels)
    x = np.arange(n)
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (name, rows, color) in enumerate(systems):
        means = [_mean([_fv(r, col) for r in rows]) for col in metrics.values()]
        cis   = [_ci95([_fv(r, col) for r in rows]) for col in metrics.values()]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, [m if m is not None else 0 for m in means],
                      width, color=color, label=name, alpha=0.85,
                      yerr=[c if c is not None else 0 for c in cis],
                      capsize=3, error_kw={"elinewidth": 1, "capthick": 1})
        for bar, m in zip(bars, means):
            if m is not None:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{m:.3f}", ha="center", va="bottom", fontsize=7.5)

    ax.axhline(0.80, color="gray", linestyle="--", linewidth=0.8, label="Target 0.80")
    ax.axhline(0.85, color="black", linestyle=":", linewidth=0.8, label="Target 0.85")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Evaluation Results: Three Systems × Four Metrics", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_systems_4metrics.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 2: Ablation impact (Δ vs GraphRAG baseline) ────────────────────────

def fig_ablation_impact():
    baseline = _load_csv(DATA / "eval_results_graphrag_final.csv")
    ablation_files = {
        "A1: no_phase1":        DATA / "eval_results_ablation_A1.csv",
        "A2: no_multihop":      DATA / "eval_results_ablation_A2.csv",
        "A3: depth=2":          DATA / "eval_results_ablation_A3.csv",
        "A4: depth=3":          DATA / "eval_results_ablation_A4.csv",
        "A5: no_yaml_L3":       DATA / "eval_results_ablation_A5.csv",
        "A6c: no_multi_entity": DATA / "eval_results_ablation_A6c.csv",
        "A7: HAS_PROP only":    DATA / "eval_results_ablation_A7.csv",
    }

    if not baseline:
        log.warning("[SKIP] fig_ablation_impact: no baseline")
        return

    metric_col = "ansq_ansq_score"  # primary comparison metric
    base_mean = _mean([_fv(r, metric_col) for r in baseline])

    deltas, labels, colors = [], [], []
    for label, path in ablation_files.items():
        rows = _load_csv(path)
        if not rows:
            continue
        m = _mean([_fv(r, metric_col) for r in rows])
        if m is None or base_mean is None:
            continue
        deltas.append(m - base_mean)
        labels.append(label)
        colors.append(C_A7 if "A7" in label else C_GRAPHRAG)

    if not deltas:
        log.warning("[SKIP] fig_ablation_impact: no ablation data")
        return

    fig, ax = plt.subplots(figsize=(8, max(4, len(deltas) * 0.55 + 1)))
    y = np.arange(len(deltas))
    bar_colors = [C_A7 if d < 0 else "#22C55E" for d in deltas]
    bars = ax.barh(y, deltas, color=bar_colors, alpha=0.85, height=0.55)
    ax.axvline(0, color="black", linewidth=0.8)
    for bar, d in zip(bars, deltas):
        ax.text(d + (0.002 if d >= 0 else -0.002), bar.get_y() + bar.get_height() / 2,
                f"{d:+.3f}", ha="left" if d >= 0 else "right", va="center", fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel(f"Δ AnsQ vs GraphRAG Baseline (baseline={base_mean:.3f})", fontsize=10)
    ax.set_title("Ablation Impact on AnsQ (Δ = Ablated − Baseline)", fontsize=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_ablation_impact.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 3: T1 proof — HAS_PROPERTY-only (A7) vs 18-edge default ────────────

def fig_t1_contrast():
    default = _load_csv(DATA / "eval_results_graphrag_final.csv")
    a7      = _load_csv(DATA / "eval_results_ablation_A7.csv")

    if not default or not a7:
        log.warning("[SKIP] fig_t1_contrast: missing default or A7 data")
        return

    metrics = {
        "AnsQ": "ansq_ansq_score",
        "RetQ (F1)": "retq_f1",
        "Hop Accuracy": "reaq_hop_accuracy",
    }
    labels = list(metrics.keys())
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for i, (name, rows, color) in enumerate([("18-edge (default)", default, C_GRAPHRAG),
                                              ("HAS_PROPERTY only (A7)", a7, C_A7)]):
        means = [_mean([_fv(r, col) for r in rows]) for col in metrics.values()]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, [m if m is not None else 0 for m in means],
                      width, color=color, label=name, alpha=0.85)
        for bar, m in zip(bars, means):
            if m is not None:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{m:.3f}", ha="center", va="bottom", fontsize=8.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("T1 Evidence: 18-Edge Semantics vs HAS_PROPERTY-Only (A7)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_t1_has_property_vs_18edge.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 4: AnsQ + RetQ per intent category (GraphRAG) ─────────────────────

def fig_by_intent():
    rows = _load_csv(DATA / "eval_results_graphrag_final.csv")
    if not rows:
        log.warning("[SKIP] fig_by_intent: no graphrag data")
        return

    intents = {}
    for r in rows:
        intent = r.get("intent_detected", "").strip() or "unknown"
        if intent not in intents:
            intents[intent] = {"ansq": [], "retq": []}
        a = _fv(r, "ansq_ansq_score")
        b = _fv(r, "retq_f1")
        if a is not None: intents[intent]["ansq"].append(a)
        if b is not None: intents[intent]["retq"].append(b)

    if not intents:
        log.warning("[SKIP] fig_by_intent: no intent data")
        return

    sorted_intents = sorted(intents.items(), key=lambda kv: -(_mean(kv[1]["ansq"]) or 0))
    labels = [k for k, _ in sorted_intents]
    ansq_means = [_mean(v["ansq"]) or 0 for _, v in sorted_intents]
    retq_means = [_mean(v["retq"]) or 0 for _, v in sorted_intents]
    counts = [len(v["ansq"]) for _, v in sorted_intents]

    x = np.arange(len(labels))
    width = 0.38

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.4), 5))
    b1 = ax.bar(x - width / 2, ansq_means, width, color=C_GRAPHRAG, alpha=0.85, label="AnsQ")
    b2 = ax.bar(x + width / 2, retq_means, width, color=C_VECTOR, alpha=0.85, label="RetQ (F1)")
    for bar, m in zip(list(b1) + list(b2), ansq_means + retq_means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{m:.2f}", ha="center", va="bottom", fontsize=7.5)

    ax.axhline(0.80, color="gray", linestyle="--", linewidth=0.8, label="Target 0.80")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{l}\n(n={c})" for l, c in zip(labels, counts)], fontsize=9)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("GraphRAG: AnsQ & RetQ by Intent Category", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_by_intent.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 5: P/R/F1 per system ───────────────────────────────────────────────

def fig_prf_by_system():
    graphrag = _load_csv(DATA / "eval_results_graphrag_final.csv")
    vector   = _load_csv(DATA / "eval_results_vector_final.csv")

    if not graphrag and not vector:
        log.warning("[SKIP] fig_prf_by_system: no data")
        return

    cols = {"Precision": "retq_precision", "Recall": "retq_recall", "F1": "retq_f1"}
    systems = [("GraphRAG", graphrag, C_GRAPHRAG), ("Vector", vector, C_VECTOR)]

    x = np.arange(len(cols))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, (name, rows, color) in enumerate(systems):
        if not rows:
            continue
        means = [_mean([_fv(r, col) for r in rows]) for col in cols.values()]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, [m if m is not None else 0 for m in means],
                      width, color=color, label=name, alpha=0.85)
        for bar, m in zip(bars, means):
            if m is not None:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{m:.3f}", ha="center", va="bottom", fontsize=9)

    ax.axhline(0.80, color="gray", linestyle="--", linewidth=0.8, label="Target 0.80")
    ax.set_xticks(x)
    ax.set_xticklabels(list(cols.keys()), fontsize=12)
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("RetQ Components: Precision / Recall / F1 by System", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_prf_by_system.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 6: RAGAS faithfulness distribution (boxplot) ───────────────────────

def fig_ragas_dist():
    graphrag = _load_csv(DATA / "eval_results_graphrag_final.csv")
    vector   = _load_csv(DATA / "eval_results_vector_final.csv")

    data_map = {}
    for name, rows in [("GraphRAG", graphrag), ("Vector", vector)]:
        vals = [_fv(r, "reaq_reaq_score") for r in rows]
        vals = [v for v in vals if v is not None]
        if vals:
            data_map[name] = vals

    if not data_map:
        log.warning("[SKIP] fig_ragas_dist: no reaq_reaq_score data (run after RAGAS join)")
        return

    fig, ax = plt.subplots(figsize=(6, 4.5))
    positions = list(range(1, len(data_map) + 1))
    colors = [C_GRAPHRAG, C_VECTOR][:len(data_map)]
    bp = ax.boxplot(list(data_map.values()), positions=positions, patch_artist=True,
                    widths=0.45, medianprops={"color": "white", "linewidth": 2})
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    for i, (name, vals) in enumerate(data_map.items(), 1):
        ax.scatter([i] * len(vals), vals, alpha=0.35, s=12, color=colors[i - 1], zorder=3)
        m = _mean(vals)
        ax.text(i, -0.05, f"μ={m:.3f}", ha="center", va="top", fontsize=8.5,
                color=colors[i - 1])

    ax.axhline(0.80, color="gray", linestyle="--", linewidth=0.8, label="Target 0.80")
    ax.set_xticks(positions)
    ax.set_xticklabels(list(data_map.keys()), fontsize=11)
    ax.set_ylim(-0.1, 1.15)
    ax.set_ylabel("RAGAS Faithfulness (ReaQ)", fontsize=10)
    ax.set_title("ReaQ Distribution: RAGAS Faithfulness per System", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_ragas_faithfulness_dist.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 7: Forest plot — effect size + 95% CI from statistical_test ────────

def fig_significance_forest():
    stat_csv = DATA / "statistical_test_results.csv"
    rows = _load_csv(stat_csv)
    if not rows:
        log.warning("[SKIP] fig_significance_forest: no statistical_test_results.csv")
        return

    # Filter primary system comparisons (GraphRAG_vs_VectorRAG, GraphRAG_vs_VanillaLLM)
    primary = [r for r in rows if r.get("comparison", "").startswith("GraphRAG_vs")]
    if not primary:
        log.warning("[SKIP] fig_significance_forest: no primary comparisons found")
        return

    labels, effects, lo95, hi95, sig = [], [], [], [], []
    for r in primary:
        comp = r.get("comparison", "").replace("_", " ").replace("GraphRAG vs ", "vs ")
        metric = r.get("metric", "")
        effect = _fv(r, "delta")
        ci_lo = _fv(r, "ci_low")
        ci_hi = _fv(r, "ci_high")
        p = _fv(r, "p_holm")
        if effect is None:
            continue
        labels.append(f"{comp}\n{metric}")
        effects.append(effect)
        lo95.append(ci_lo if ci_lo is not None else effect)
        hi95.append(ci_hi if ci_hi is not None else effect)
        sig.append(p is not None and p < 0.05)

    if not effects:
        log.warning("[SKIP] fig_significance_forest: no plottable effect sizes")
        return

    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8, max(4, len(labels) * 0.5 + 1.5)))
    colors = [C_GRAPHRAG if s else C_GRAY for s in sig]
    ax.scatter(effects, y, color=colors, s=55, zorder=3)
    for i, (e, lo, hi) in enumerate(zip(effects, lo95, hi95)):
        ax.plot([lo, hi], [i, i], color=colors[i], linewidth=1.5, alpha=0.7)

    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Effect Size (Δ mean; GraphRAG − Baseline)", fontsize=10)
    ax.set_title("Statistical Significance: Effect Sizes + 95% CI\n(blue = p<0.05, gray = n.s.)", fontsize=11, fontweight="bold")
    sig_patch = mpatches.Patch(color=C_GRAPHRAG, label="p < 0.05 (significant)")
    ns_patch  = mpatches.Patch(color=C_GRAY, label="n.s.")
    ax.legend(handles=[sig_patch, ns_patch], fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_significance_forest.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 8: YAML validity (syntactic + schema) ──────────────────────────────

def fig_yaml_validity():
    rows = _load_csv(DATA / "eval_results_graphrag_final.csv")
    if not rows:
        log.warning("[SKIP] fig_yaml_validity: no data")
        return

    yaml_rows = [r for r in rows if r.get("type") == "yaml_gen"]
    if not yaml_rows:
        log.warning("[SKIP] fig_yaml_validity: no yaml_gen fixtures in data")
        return

    syn  = [_fv(r, "ansq_syntactic_validity") for r in yaml_rows]
    sch  = [_fv(r, "ansq_schema_compliance") for r in yaml_rows]
    syn_mean = _mean(syn)
    sch_mean = _mean(sch)

    if syn_mean is None and sch_mean is None:
        log.warning("[SKIP] fig_yaml_validity: all None values")
        return

    labels = ["Syntactic Validity", "Schema Compliance (K8s 1.30)"]
    means  = [syn_mean or 0, sch_mean or 0]
    colors = [C_GRAPHRAG, C_VECTOR]
    n = len(yaml_rows)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, means, color=colors, alpha=0.85, width=0.45)
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{m:.3f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.axhline(0.80, color="gray", linestyle="--", linewidth=0.8, label="Target 0.80")
    ax.axhline(0.85, color="black", linestyle=":", linewidth=0.8, label="Target 0.85")
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(f"YAML Answer Quality (n={n} yaml_gen fixtures)", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_yaml_validity.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Figure 9: Faith vs AnsQ scatter (orthogonality) ──────────────────────────

def fig_faith_vs_ansq_scatter():
    rows = _load_csv(DATA / "eval_results_graphrag_final.csv")
    if not rows:
        log.warning("[SKIP] fig_faith_vs_ansq_scatter: no data")
        return

    pts = []
    for r in rows:
        faith = _fv(r, "reaq_reaq_score")
        ansq  = _fv(r, "ansq_ansq_score")
        ftype = r.get("type", "unknown").strip() or "unknown"
        if faith is not None and ansq is not None:
            pts.append((faith, ansq, ftype))

    if not pts:
        log.warning("[SKIP] fig_faith_vs_ansq_scatter: no paired data")
        return

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n  = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov  = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    sx   = (sum((x - mx) ** 2 for x in xs) / n) ** 0.5
    sy   = (sum((y - my) ** 2 for y in ys) / n) ** 0.5
    pearson_r = cov / (sx * sy) if sx * sy > 0 else 0.0

    type_colors = {
        "yaml_gen":        "#2563EB",
        "conceptual":      "#16A34A",
        "relationship":    "#9333EA",
        "followup":        "#F59E0B",
        "realworld":       "#DC2626",
        "planning":        "#0891B2",
        "troubleshooting": "#78716C",
        "command":         "#EC4899",
    }

    by_type = {}
    for faith, ansq, ftype in pts:
        by_type.setdefault(ftype, ([], []))
        by_type[ftype][0].append(faith)
        by_type[ftype][1].append(ansq)

    fig, ax = plt.subplots(figsize=(7, 5.5))

    # Paradox quadrant: faith <= 0.30, ansq >= 0.70
    rect = mpatches.Rectangle((0, 0.70), 0.30, 0.40,
                               linewidth=0, facecolor="#F59E0B", alpha=0.09, zorder=0)
    ax.add_patch(rect)
    ax.axvline(0.30, color="#D97706", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axhline(0.70, color="#D97706", linewidth=0.8, linestyle="--", alpha=0.6)

    for ftype, (xs_t, ys_t) in sorted(by_type.items()):
        color = type_colors.get(ftype, C_GRAY)
        ax.scatter(xs_t, ys_t, color=color, s=30, alpha=0.78, label=ftype, zorder=3)

    n_paradox = sum(1 for f, a, _ in pts if f <= 0.30 and a >= 0.70)
    ax.text(0.15, 0.965, f"Kuadran paradoks\n(n={n_paradox})",
            ha="center", va="top", fontsize=7.5, color="#92400E",
            transform=ax.transAxes)

    ax.text(0.97, 0.03, f"Pearson r = {pearson_r:.2f}",
            ha="right", va="bottom", transform=ax.transAxes,
            fontsize=9, color="#374151",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#9CA3AF", alpha=0.8))

    ax.set_xlabel("RAGAS Faithfulness (ReaQ)", fontsize=11)
    ax.set_ylabel("AnsQ", fontsize=11)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0.0, 1.10)
    ax.set_title(f"Ortogonalitas Faithfulness vs AnsQ (GraphRAG, n={n})",
                 fontsize=11, fontweight="bold")
    ax.legend(title="Tipe", fontsize=7.5, title_fontsize=8,
              loc="lower right", markerscale=1.2, framealpha=0.88)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    out = IMAGES / "eval_faith_vs_ansq_scatter.png"
    fig.savefig(out, dpi=DPI, bbox_inches=BBOX)
    plt.close(fig)
    log.info(f"[OK] {out.name}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("=== eval_charts.py — generating evaluation figures ===")
    log.info(f"Output dir: {IMAGES}")

    fig_systems_4metrics()
    fig_ablation_impact()
    fig_t1_contrast()
    fig_by_intent()
    fig_prf_by_system()
    fig_ragas_dist()
    fig_significance_forest()
    fig_yaml_validity()
    fig_faith_vs_ansq_scatter()

    log.info("=== Done. Check images/ for output PNGs. ===")
