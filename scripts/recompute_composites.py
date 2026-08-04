"""
scripts/recompute_composites.py
Recompute RetQ dan ReaQ composite scores dari sub-metrik yang sudah ada di CSV.

Definisi komposit baru (shared-target, adil untuk 3 sistem):
  RetQ = (f1_at_k + ndcg_at_k) / 2
  ReaQ = grounding_score

Tidak menyentuh kolom sub-metrik (path_coverage, hop_accuracy tetap ada
sebagai metrik intrinsik graf untuk Tabel VI.4 dan Lampiran-C).

Idempoten: aman dijalankan ulang.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent

CSV_FILES = [
    ROOT / "data" / "eval_results_graphrag_final.csv",
    ROOT / "data" / "eval_results_vector_final.csv",
    ROOT / "data" / "eval_results_llm_final.csv",
    ROOT / "data" / "eval_results_ablation_A1.csv",
    ROOT / "data" / "eval_results_ablation_A2.csv",
    ROOT / "data" / "eval_results_ablation_A3.csv",
    ROOT / "data" / "eval_results_ablation_A4.csv",
    ROOT / "data" / "eval_results_ablation_A5.csv",
    ROOT / "data" / "eval_results_ablation_A6c.csv",
    ROOT / "data" / "eval_results_depth_1.csv",
    ROOT / "data" / "eval_results_depth_4.csv",
    ROOT / "data" / "eval_results_depth_5.csv",
]


def recompute(path: Path) -> None:
    if not path.exists():
        print(f"  [SKIP] {path.name} tidak ditemukan")
        return

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        if not rows:
            print(f"  [SKIP] {path.name} kosong")
            return
        fieldnames = list(rows[0].keys())

    n_updated = 0
    for row in rows:
        try:
            f1    = float(row.get("retq_f1_at_k", "") or 0)
            ndcg  = float(row.get("retq_ndcg_at_k", "") or 0)
            grnd  = float(row.get("reaq_grounding_score", "") or 0)
        except ValueError:
            continue

        new_retq = round((f1 + ndcg) / 2, 6)
        new_reaq = round(grnd, 6)

        if (row.get("retq_retq_score") != str(new_retq) or
                row.get("reaq_reaq_score") != str(new_reaq)):
            n_updated += 1

        row["retq_retq_score"] = new_retq
        row["reaq_reaq_score"] = new_reaq

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [OK] {path.name}: {n_updated}/{len(rows)} baris diperbarui")


def main():
    print("Recompute RetQ = (F1+NDCG)/2 dan ReaQ = Grounding Score ...\n")
    for csv_path in CSV_FILES:
        recompute(csv_path)
    print("\nSelesai.")


if __name__ == "__main__":
    main()
