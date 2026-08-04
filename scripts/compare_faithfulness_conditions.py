"""
compare_faithfulness_conditions.py
===================================
Sensitivity-analysis script (FUTURE WORK, bukan bagian dari metrik resmi Bab VI).

Membandingkan secara BERPASANGAN (per fixture id):
  - baseline (strict)  : data/faithfulness_decomposition.csv       kolom faithfulness_run
  - tolerant (modality) : data/faithfulness_tolerant.csv            kolom faithfulness_tolerant

Memakai UJI YANG SAMA seperti Bab VI (Wilcoxon signed-rank + paired bootstrap 1000 iter),
di-reuse langsung dari scripts/statistical_test.py -- bukan ditulis ulang -- supaya
metodologinya identik dan hasilnya bisa dipertanggungjawabkan dengan cara yang sama.

Tidak menulis apa pun selain:
  data/faithfulness_condition_comparison.csv   (file baru)

Usage:
  python scripts/compare_faithfulness_conditions.py
  python scripts/compare_faithfulness_conditions.py --bootstrap-iter 2000
"""
import sys, csv, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statistical_test import wilcoxon_test, bootstrap_ci  # reuse, jangan tulis ulang

DATA_DIR = Path(__file__).parent.parent / "data"
BASELINE_PATH = DATA_DIR / "faithfulness_decomposition.csv"
TOLERANT_PATH = DATA_DIR / "faithfulness_tolerant.csv"
OUT_PATH = DATA_DIR / "faithfulness_condition_comparison.csv"

# Batas kewarasan dari rencana (Verifikasi bagian C)
CEILING_ARITMATIK = 0.4144  # (258 supported + 81 modality) / 818, dari baseline resmi
BASELINE_OFFICIAL = 0.3154  # faithfulness_micro, faithfulness_decomposition_summary.json


def load_csv(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] File tidak ditemukan: {path}")
        sys.exit(1)
    rows = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = r
    return rows


def main():
    parser = argparse.ArgumentParser(description="Bandingkan faithfulness baseline (strict) vs tolerant (modality-aware)")
    parser.add_argument("--bootstrap-iter", type=int, default=1000)
    args = parser.parse_args()

    baseline = load_csv(BASELINE_PATH)
    tolerant = load_csv(TOLERANT_PATH)

    common_ids = sorted(set(baseline) & set(tolerant))
    only_baseline = sorted(set(baseline) - set(tolerant))
    only_tolerant = sorted(set(tolerant) - set(baseline))

    print(f"\n{'='*70}")
    print("  Perbandingan Berpasangan: Faithfulness Strict vs Modality-Tolerant")
    print(f"{'='*70}")
    print(f"  Baseline (strict)  : {len(baseline)} fixture -> {BASELINE_PATH.name}")
    print(f"  Tolerant (modality): {len(tolerant)} fixture -> {TOLERANT_PATH.name}")
    print(f"  Fixture berpasangan (irisan): {len(common_ids)}")
    if only_baseline:
        print(f"  [INFO] Hanya di baseline, tidak diikutkan ({len(only_baseline)}): {only_baseline[:10]}{'...' if len(only_baseline) > 10 else ''}")
    if only_tolerant:
        print(f"  [INFO] Hanya di tolerant, tidak diikutkan ({len(only_tolerant)}): {only_tolerant}")

    if len(common_ids) < 2:
        print("\n[ERROR] Fixture berpasangan terlalu sedikit untuk uji statistik (butuh >= 2).")
        sys.exit(1)

    a_strict = [float(baseline[i]["faithfulness_run"]) for i in common_ids]
    b_tolerant = [float(tolerant[i]["faithfulness_tolerant"]) for i in common_ids]

    mean_strict = sum(a_strict) / len(a_strict)
    mean_tolerant = sum(b_tolerant) / len(b_tolerant)

    print(f"\n  Rata-rata faithfulness (subset {len(common_ids)} fixture berpasangan):")
    print(f"    strict (baseline)   = {mean_strict:.4f}")
    print(f"    tolerant (modality) = {mean_tolerant:.4f}")
    print(f"    delta               = {mean_tolerant - mean_strict:+.4f}")

    w_stat, w_p = wilcoxon_test(b_tolerant, a_strict)
    obs_diff, ci_lo, ci_hi, bs_p = bootstrap_ci(b_tolerant, a_strict, n_iter=args.bootstrap_iter)

    print(f"\n  Wilcoxon signed-rank (tolerant > strict, one-tailed):")
    print(f"    statistic = {w_stat}")
    print(f"    p-value   = {w_p}")
    print(f"\n  Paired bootstrap ({args.bootstrap_iter} iter):")
    print(f"    observed diff = {obs_diff:+.4f}")
    print(f"    95% CI        = [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"    p-value       = {bs_p}")

    # -- Kewarasan (Verifikasi bagian C rencana) --
    print(f"\n  {'-'*66}")
    print("  CEK KEWARASAN (terhadap rencana)")
    print(f"  {'-'*66}")
    in_range = BASELINE_OFFICIAL <= mean_tolerant <= CEILING_ARITMATIK
    print(f"    Rentang aman        : [{BASELINE_OFFICIAL}, {CEILING_ARITMATIK}]")
    print(f"    Hasil tolerant_mean : {mean_tolerant:.4f}  -> {'DI DALAM RENTANG (aman)' if in_range else '*** DI LUAR RENTANG -- SELIDIKI SEBELUM DIPAKAI ***'}")
    if mean_tolerant < BASELINE_OFFICIAL:
        print("    [PERINGATAN] Lebih rendah dari baseline -- prompt toleran malah lebih ketat, ada yang salah.")
    if mean_tolerant > CEILING_ARITMATIK:
        print("    [PERINGATAN] Melebihi ceiling aritmatik -- kemungkinan judge mereklasifikasi klaim")
        print("                 'absent' jadi supported (prompt terlalu longgar). JANGAN dipakai di slide")
        print("                 tanpa investigasi manual per-klaim di faithfulness_tolerant_raw.jsonl.")

    # Pergeseran distribusi kelas: absent seharusnya TIDAK runtuh drastis
    n_absent_baseline = sum(int(baseline[i]["absent"]) for i in common_ids)
    n_claims_baseline = sum(int(baseline[i]["n_claims"]) for i in common_ids)
    n_absent_tolerant = sum(int(tolerant[i]["absent"]) for i in common_ids)
    n_claims_tolerant = sum(int(tolerant[i]["n_claims"]) for i in common_ids)
    pct_absent_baseline = 100 * n_absent_baseline / max(n_claims_baseline, 1)
    pct_absent_tolerant = 100 * n_absent_tolerant / max(n_claims_tolerant, 1)
    print(f"\n    Proporsi 'absent' baseline : {pct_absent_baseline:.1f}%  ({n_absent_baseline}/{n_claims_baseline} klaim)")
    print(f"    Proporsi 'absent' tolerant : {pct_absent_tolerant:.1f}%  ({n_absent_tolerant}/{n_claims_tolerant} klaim)")
    drop = pct_absent_baseline - pct_absent_tolerant
    print(f"    Penurunan                 : {drop:.1f} poin persentase", end="")
    if drop > 15:
        print("  -> *** BESAR, curigai prompt jadi stempel karet ***")
    else:
        print("  -> wajar (target koreksi cuma kategori modality)")

    # -- Tulis output --
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "faithfulness_strict", "faithfulness_tolerant", "delta"])
        for i in common_ids:
            fs = float(baseline[i]["faithfulness_run"])
            ft = float(tolerant[i]["faithfulness_tolerant"])
            w.writerow([i, fs, ft, round(ft - fs, 4)])
    print(f"\n  Disimpan -> {OUT_PATH.name}  ({len(common_ids)} baris)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
