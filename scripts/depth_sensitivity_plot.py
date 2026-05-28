"""
scripts/depth_sensitivity_plot.py
Visualisasi pengaruh max_depth terhadap RetQ per fixture type.

Cara pakai:
  1. Jalankan evaluasi untuk depth 1, 4, 5 (depth 2 dan 3 sudah ada dari ablation A3/A4):
       python scripts/evaluate.py --mode graphrag --ablation depth_1 --output data/eval_results_depth_1.csv
       python scripts/evaluate.py --mode graphrag --ablation depth_4 --output data/eval_results_depth_4.csv
       python scripts/evaluate.py --mode graphrag --ablation depth_5 --output data/eval_results_depth_5.csv
  2. Jalankan script ini:
       python scripts/depth_sensitivity_plot.py
  3. Diagram disimpan ke: docs/figures/depth_sensitivity_retq.png
                          docs/figures/depth_sensitivity_submetrics.png
"""
import csv
import sys
import math
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")   # non-interactive backend (safe for headless & VSCode)
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
except ImportError:
    sys.exit("[ERROR] matplotlib tidak terinstal. Jalankan: pip install matplotlib")

ROOT = Path(__file__).parent.parent
FIGURES_DIR = ROOT / "docs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Path ke CSV per depth ─────────────────────────────────────────────────────
DEPTH_CSV = {
    1: ROOT / "data" / "eval_results_depth_1.csv",
    2: ROOT / "data" / "eval_results_ablation_A3.csv",   # depth_2 fixed
    3: ROOT / "data" / "eval_results_ablation_A4.csv",   # depth_3 fixed
    4: ROOT / "data" / "eval_results_depth_4.csv",
    5: ROOT / "data" / "eval_results_depth_5.csv",
}

# Adaptive baseline: depth yang SESUNGGUHNYA digunakan per fixture type
# (berdasarkan intent mapping di _DEPTH_BY_INTENT)
ADAPTIVE_DEPTH = {
    "conceptual":     2,   # intent → explain → depth 2
    "followup":       2,   # intent → followup → depth 2
    "yaml_gen":       3,   # intent → generate_yaml → depth 3
    "relationship":   3,   # intent → trace_relationship → depth 3
    "planning":       3,   # intent → planning → depth 3
    "troubleshooting": 3,  # intent → explain/trace → depth 3
    "realworld":      3,   # mixed; mostly depth 3
    "command":        3,   # intent → explain → depth 2/3 mixed
}

FIXTURE_TYPES = [
    "conceptual", "followup", "yaml_gen", "relationship",
    "planning", "realworld", "troubleshooting", "command",
]

# Warna per fixture type — cukup kontras untuk print grayscale juga
COLORS = {
    "conceptual":     "#2196F3",   # biru
    "followup":       "#FF9800",   # oranye
    "yaml_gen":       "#4CAF50",   # hijau
    "relationship":   "#9C27B0",   # ungu
    "planning":       "#F44336",   # merah
    "realworld":      "#607D8B",   # abu-abu biru
    "troubleshooting": "#795548",  # coklat
    "command":        "#00BCD4",   # cyan
}
MARKERS = {
    "conceptual":     "o",
    "followup":       "s",
    "yaml_gen":       "^",
    "relationship":   "D",
    "planning":       "P",
    "realworld":      "X",
    "troubleshooting": "v",
    "command":        "*",
}

# ── Baca data ─────────────────────────────────────────────────────────────────

def read_retq_per_type(csv_path: Path) -> dict:
    """
    Baca CSV dan kembalikan dict {fixture_type: avg_retq_score}.
    Fixture type 'realworld' di-effective-type ke concrete sub-type
    tapi tetap di-bucket sebagai 'realworld' di sini (tidak di-split).
    """
    buckets: dict[str, list] = {t: [] for t in FIXTURE_TYPES}
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = row.get("type", "").strip()
                v = row.get("retq_retq_score", "").strip()
                if t in buckets and v:
                    try:
                        buckets[t].append(float(v))
                    except ValueError:
                        pass
    except FileNotFoundError:
        return {}
    return {t: (sum(vs) / len(vs)) if vs else None for t, vs in buckets.items()}


def read_submetrics_per_type(csv_path: Path) -> dict:
    """Baca precision@k, recall@k, NDCG@k per fixture type."""
    cols = ["retq_precision_at_k", "retq_recall_at_k", "retq_ndcg_at_k"]
    buckets: dict[str, dict[str, list]] = {t: {c: [] for c in cols} for t in FIXTURE_TYPES}
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = row.get("type", "").strip()
                if t not in buckets:
                    continue
                for c in cols:
                    v = row.get(c, "").strip()
                    if v:
                        try:
                            buckets[t][c].append(float(v))
                        except ValueError:
                            pass
    except FileNotFoundError:
        return {}
    result = {}
    for t, cdict in buckets.items():
        result[t] = {
            c: (sum(vs) / len(vs)) if vs else None
            for c, vs in cdict.items()
        }
    return result


# ── Kumpulkan data untuk semua depth ─────────────────────────────────────────

available_depths = []
data_retq: dict[int, dict] = {}

for d, path in sorted(DEPTH_CSV.items()):
    if path.exists():
        scores = read_retq_per_type(path)
        if scores:
            data_retq[d] = scores
            available_depths.append(d)
        else:
            print(f"  [SKIP] depth={d}: {path.name} kosong atau tidak terbaca")
    else:
        print(f"  [MISS] depth={d}: {path.name} belum ada")

if len(available_depths) < 2:
    sys.exit(
        "[ERROR] Minimal 2 depth diperlukan untuk membuat diagram.\n"
        "Jalankan evaluasi terlebih dahulu (lihat docstring di atas)."
    )

print(f"\n[Plot] Depth tersedia: {available_depths}")
depths_x = sorted(available_depths)


# ── Plot 1: RetQ per fixture type vs depth ────────────────────────────────────

fig1, ax1 = plt.subplots(figsize=(10, 6))

for ftype in FIXTURE_TYPES:
    y_vals = []
    x_vals = []
    for d in depths_x:
        score = data_retq[d].get(ftype)
        if score is not None:
            x_vals.append(d)
            y_vals.append(score)

    if not y_vals:
        continue

    line, = ax1.plot(
        x_vals, y_vals,
        marker=MARKERS[ftype],
        color=COLORS[ftype],
        linewidth=1.8,
        markersize=7,
        label=ftype,
    )

    # Tandai titik adaptive depth untuk fixture type ini
    adp_d = ADAPTIVE_DEPTH.get(ftype)
    if adp_d in data_retq and data_retq[adp_d].get(ftype) is not None:
        ax1.scatter(
            [adp_d], [data_retq[adp_d][ftype]],
            color=COLORS[ftype],
            s=120,
            zorder=5,
            edgecolors="black",
            linewidths=1.2,
        )

# Garis vertikal menandai titik adaptive depth per kelompok intent
ax1.axvline(x=2, color="gray", linestyle="--", linewidth=0.8, alpha=0.6,
            label="adaptive depth: explain/followup=2")
ax1.axvline(x=3, color="gray", linestyle=":",  linewidth=0.8, alpha=0.6,
            label="adaptive depth: others=3")

ax1.set_xlabel("Max Traversal Depth", fontsize=12)
ax1.set_ylabel("RetQ Score (average)", fontsize=12)
ax1.set_title(
    "Pengaruh Max Depth terhadap RetQ per Fixture Type\n"
    "(titik bertanda hitam = depth yang digunakan oleh adaptive system)",
    fontsize=12,
)
ax1.set_xticks(depths_x)
ax1.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))
ax1.set_ylim(0, 1.05)
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
ax1.grid(axis="y", alpha=0.3)
ax1.grid(axis="x", alpha=0.15)
ax1.legend(loc="upper left", fontsize=9, ncol=2, framealpha=0.85)

fig1.tight_layout()
out1 = FIGURES_DIR / "depth_sensitivity_retq.png"
fig1.savefig(out1, dpi=180, bbox_inches="tight")
print(f"[OK] Diagram 1 disimpan: {out1}")
plt.close(fig1)


# ── Plot 2: Precision@k, Recall@k, NDCG@k per depth (aggregate) ──────────────

data_sub: dict[int, dict] = {}
for d in depths_x:
    data_sub[d] = read_submetrics_per_type(DEPTH_CSV[d])

col_labels = {
    "retq_precision_at_k": ("Precision@k", "#E53935"),
    "retq_recall_at_k":    ("Recall@k",    "#1E88E5"),
    "retq_ndcg_at_k":      ("NDCG@k",      "#43A047"),
}

fig2, ax2 = plt.subplots(figsize=(9, 5))

for col, (label, color) in col_labels.items():
    y_vals = []
    x_vals = []
    for d in depths_x:
        if d not in data_sub:
            continue
        all_scores = [
            data_sub[d][t][col]
            for t in FIXTURE_TYPES
            if data_sub[d].get(t, {}).get(col) is not None
        ]
        if all_scores:
            x_vals.append(d)
            y_vals.append(sum(all_scores) / len(all_scores))

    if y_vals:
        ax2.plot(
            x_vals, y_vals,
            marker="o", color=color, linewidth=2,
            markersize=7, label=label,
        )

ax2.axvline(x=2, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
ax2.axvline(x=3, color="gray", linestyle=":",  linewidth=0.8, alpha=0.6)
ax2.set_xlabel("Max Traversal Depth", fontsize=12)
ax2.set_ylabel("Score (average across all types)", fontsize=12)
ax2.set_title("Precision@k, Recall@k, NDCG@k vs Max Depth\n(aggregate — semua fixture types)", fontsize=12)
ax2.set_xticks(depths_x)
ax2.set_ylim(0, 1.05)
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
ax2.grid(axis="y", alpha=0.3)
ax2.grid(axis="x", alpha=0.15)
ax2.legend(fontsize=10, framealpha=0.85)

fig2.tight_layout()
out2 = FIGURES_DIR / "depth_sensitivity_submetrics.png"
fig2.savefig(out2, dpi=180, bbox_inches="tight")
print(f"[OK] Diagram 2 disimpan: {out2}")
plt.close(fig2)


# ── Tabel ringkasan di terminal ───────────────────────────────────────────────

print()
print("=== RetQ per Fixture Type per Depth ===")
header = f"  {'Type':<18}" + "".join(f"  d={d:>1}" for d in depths_x)
print(header)
print("  " + "-" * (18 + 7 * len(depths_x)))
for ftype in FIXTURE_TYPES:
    row = f"  {ftype:<18}"
    for d in depths_x:
        v = data_retq[d].get(ftype)
        row += f"  {v:.3f}" if v is not None else "     —"
    # Tandai adaptive depth per type
    adp = ADAPTIVE_DEPTH.get(ftype, "?")
    row += f"   (adaptive={adp})"
    print(row)

print()
print("Keterangan:")
print("  Titik bertanda hitam di diagram = depth yang digunakan baseline adaptive system.")
print("  Garis putus-putus: depth=2 (explain/followup), garis titik-titik: depth=3 (others).")
