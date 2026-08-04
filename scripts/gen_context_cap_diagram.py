"""Generate context-cap selection diagrams for thesis (Bab V).

Outputs two separate PNG files:
  context_cap_distribution.png  -- bimodal context-length distribution (97 fixtures)
  context_cap_sweep.png         -- per-factor evaluation scores vs 5 cap values
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

IMG_DIR = Path(__file__).parent.parent / "docs" / "TA-STI-template-1.0" / "images"
OUT_DIST  = IMG_DIR / "context_cap_distribution.png"
OUT_SWEEP = IMG_DIR / "context_cap_sweep.png"

# Bimodal distribution from 97 fixtures (dry-run retriever audit)
LENGTHS = [11_606] * 79 + [17_849] * 18

# Empirical evaluation results (5 cap values, mode=graphrag, 97 fixtures)
CAPS      = [10_000, 12_000, 15_000, 18_000, 20_000]
ANSQ      = [0.5718, 0.5904, 0.5687, 0.5706, 0.5739]
RETQ      = [0.6827, 0.6801, 0.6842, 0.6841, 0.6757]
REAQ      = [0.9033, 0.8989, 0.8957, 0.8968, 0.9009]

CHOSEN_IDX = 1   # 12k is the selected value
CAP_TICKS  = [10_000, 12_000, 15_000, 18_000, 20_000]
CAP_LABELS = ["10k", "12k\n(dipilih)", "15k", "18k", "20k"]

# ══════════════════════════════════════════════════════════════════════════════
# Gambar 1: Distribusi Panjang Graph Context
# ══════════════════════════════════════════════════════════════════════════════
fig_dist, ax_dist = plt.subplots(figsize=(9, 3.8))

ax_dist.bar([11_606], [79], width=900, color="#4C72B0", edgecolor="white",
            zorder=3, label="Kelompok konteks pendek (79 kueri, 81,4%)")
ax_dist.bar([17_849], [18], width=900, color="#DD8452", edgecolor="white",
            zorder=3, label="Kelompok konteks panjang (18 kueri, 18,6%)")

ax_dist.axvline(12_000, color="#27ae60", linestyle="-", linewidth=2.0, zorder=5,
                label="Batas dipilih: 12.000 karakter")
ax_dist.axvline(20_000, color="#7f8c8d", linestyle="--", linewidth=1.3, zorder=4,
                label="Kandidat awal: 20.000 karakter")

ax_dist.text(11_606, 81, "79", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax_dist.text(17_849, 20, "18", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax_dist.annotate(
    "18,6% terpotong\npada batas 12k",
    xy=(12_000, 55), xytext=(14_200, 60),
    fontsize=8, color="#27ae60",
    arrowprops=dict(arrowstyle="->", color="#27ae60", lw=1.0),
)

ax_dist.set_xlim(7_000, 23_000)
ax_dist.set_ylim(0, 96)
ax_dist.set_ylabel("Jumlah Kueri", fontsize=10)
ax_dist.set_title("Distribusi Panjang Graph Context (97 fixture)", fontsize=11, loc="left")
ax_dist.yaxis.grid(True, linestyle=":", alpha=0.4)
ax_dist.set_axisbelow(True)
ax_dist.set_xticks([10_000, 11_606, 12_000, 17_849, 20_000])
ax_dist.set_xticklabels(["10k", "11.606", "12k", "17.849", "20k"], fontsize=8)
ax_dist.legend(fontsize=7.8, loc="upper right")
ax_dist.set_xlabel("Panjang Karakter", fontsize=10)

fig_dist.tight_layout()
fig_dist.savefig(OUT_DIST, dpi=180, bbox_inches="tight")
print(f"Saved: {OUT_DIST}")
plt.close(fig_dist)

# ══════════════════════════════════════════════════════════════════════════════
# Gambar 2: Skor Evaluasi Per-Faktor vs Nilai Batas
# ══════════════════════════════════════════════════════════════════════════════
fig_sweep, ax_eval = plt.subplots(figsize=(9, 4.5))

x = np.array(CAPS)

ax_eval.plot(x, ANSQ, color="#4C72B0", linewidth=2.0, marker="s", markersize=6,
             zorder=4, label="AnsQ (Kualitas Jawaban)")
ax_eval.plot(x, RETQ, color="#DD8452", linewidth=2.0, marker="^", markersize=6,
             zorder=4, label="RetQ (Kualitas Retrieval)")
ax_eval.plot(x, REAQ, color="#55a868", linewidth=2.0, marker="D", markersize=6,
             zorder=4, label="ReaQ (Kualitas Penalaran)")

chosen_cap  = CAPS[CHOSEN_IDX]
chosen_ansq = ANSQ[CHOSEN_IDX]
ax_eval.scatter([chosen_cap], [chosen_ansq], color="#27ae60", s=120, zorder=7, marker="*")
ax_eval.axvline(chosen_cap, color="#27ae60", linestyle="-", linewidth=1.5, alpha=0.6, zorder=3)
ax_eval.annotate(
    "Nilai dipilih: 12.000\n(AnsQ tertinggi)",
    xy=(chosen_cap, chosen_ansq),
    xytext=(chosen_cap + 800, chosen_ansq - 0.009),
    fontsize=8.5, color="#27ae60",
    arrowprops=dict(arrowstyle="->", color="#27ae60", lw=1.0),
)

ax_eval.set_xlim(9_000, 21_000)
ax_eval.set_ylim(min(min(ANSQ), min(RETQ)) - 0.01,
                 max(max(REAQ), max(RETQ)) + 0.015)
ax_eval.set_xticks(CAP_TICKS)
ax_eval.set_xticklabels(CAP_LABELS, fontsize=8.5)
ax_eval.set_xlabel("Nilai Batas Karakter (Context Cap)", fontsize=10)
ax_eval.set_ylabel("Skor Evaluasi", fontsize=10)
ax_eval.set_title("Skor Evaluasi Per-Faktor vs Nilai Context Cap (97 fixture)",
                  fontsize=11, loc="left")
ax_eval.yaxis.grid(True, linestyle=":", alpha=0.4)
ax_eval.set_axisbelow(True)
ax_eval.legend(fontsize=8.5, loc="lower right")

fig_sweep.tight_layout()
fig_sweep.savefig(OUT_SWEEP, dpi=180, bbox_inches="tight")
print(f"Saved: {OUT_SWEEP}")
plt.close(fig_sweep)
