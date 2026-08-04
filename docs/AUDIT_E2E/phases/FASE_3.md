# FASE 3 — Re-run Evaluasi Penuh

> Status: 🔶 IN-PROGRESS (2026-06-14)
> Prerequisite: Fase 0 ✅ · Fase 2 ✅ · Fase 1 ✅
> Next: Fase 4 (update angka tesis + sub-bab evaluasi)

---

## Tujuan

Menghasilkan angka `_final` baru yang valid metodologis untuk seluruh sistem + ablation + depth
sensitivity + RAGAS + uji statistik + boundary condition + figur, setelah Fase 1 (kode) dan Fase 2
(GT fixture) selesai. Melaporkan hasil **apa adanya** terhadap target >0,80 (mayoritas ≥0,85).

**Tidak ada perubahan prosa tesis di fase ini** — itu Fase 4.

---

## Keputusan terkunci

| # | Keputusan |
|---|-----------|
| **F16** | Single-run, speaker temperature **tetap 0.1** (nol perubahan kode). Disclosure Fase 4: *"single run; speaker temp 0.1 mendekati deterministik; keyakinan statistik dari Wilcoxon+bootstrap n=103."* |
| **Ablation** | Full 10: A1 no_phase1, A2 no_multihop, A3 depth_2, A4 depth_3, A5 no_yaml_layer3, A6c no_multi_entity, **A7 has_property_only** (T1/F14), depth_1, depth_4, depth_5. |
| **Figur** | 5 regen otomatis (depth_sensitivity + boundary) + 8 baru via `eval_charts.py`. Filter ke tesis di Fase 4. |

---

## Preflight terverifikasi (2026-06-14)

- ✅ `ragas 0.4.3` terpasang · `neo4j-driver` ok
- ✅ Neo4j ON: **725 Definition node · 18 tipe edge · v1.30**
- ✅ CSV lama diarsip ke `data/_archive_pre_fase3/` (22 file)
- ✅ Fix sisa F12: `evaluate.py:665` → `"1.30"` (diagnostik sidecar JSONL, bukan metrik)
- ✅ 103 fixture aktif (117 total; 14 selection_score=0)

---

## Skema metrik yang dihasilkan

| Metrik | Berlaku untuk | Sitasi |
|--------|---------------|--------|
| AnsQ: `answer_relevance` (cosine) | semua | es_ragas_2023 |
| AnsQ: `syntactic_validity`, `schema_compliance` | yaml_gen saja | OpenAPI K8s 1.30 |
| RetQ: `precision`, `recall`, `f1` | GraphRAG + Vector | Manning et al. 2008 |
| ReaQ: RAGAS `faithfulness` (`reaq_reaq_score`) | GraphRAG + Vector (via join) | es_ragas_2023 |
| `hop_accuracy` | GraphRAG-only | Manning et al. 2008 (edge recall) |
| Diagnostik: `intent_detected`, `gt_depth`, `n_roots`, `seed_node_degree`, `error_flag`, dll. | semua | — |

**Kolom ReaQ** baru terisi setelah Langkah 2 (RAGAS join). Ablation CSV tanpa ReaQ by-design.

---

## Langkah eksekusi

### Langkah 0 — Preflight ✅ DONE
- FASE_3.md ditulis · fix evaluate.py:665 · Neo4j terverifikasi · CSV lama diarsip.

### Langkah 1 — Re-run 3 sistem
```
python scripts/evaluate.py --mode graphrag --output data/eval_results_graphrag.csv
python scripts/evaluate.py --mode vector   --output data/eval_results_vector.csv
python scripts/evaluate.py --mode llm      --output data/eval_results_llm.csv
```
Target: 103 baris per CSV, `error_flag` mayoritas 0. Resume otomatis bila terputus.

### Langkah 2 — RAGAS faithfulness
```
python scripts/recompute_ragas.py --mode all
```
Membaca `eval_cases_<mode>.jsonl`, join ke `reaq_reaq_score` di 3 CSV Langkah 1.
Log skip per-metrik menjelaskan tiap n-mismatch.

### Langkah 3 — Promosi ke `_final`
Copy `eval_results_{graphrag,vector,llm}.csv` → `eval_results_{...}_final.csv`.
Verifikasi `reaq_reaq_score` terisi di graphrag & vector finals.

### Langkah 4 — 10 ablation (graphrag-only)

| Flag | Output CSV |
|------|-----------|
| `no_phase1` | `eval_results_ablation_A1.csv` |
| `no_multihop` | `eval_results_ablation_A2.csv` |
| `depth_2` | `eval_results_ablation_A3.csv` |
| `depth_3` | `eval_results_ablation_A4.csv` |
| `no_yaml_layer3` | `eval_results_ablation_A5.csv` |
| `no_multi_entity` | `eval_results_ablation_A6c.csv` |
| `has_property_only` | `eval_results_ablation_A7.csv` **(baru — bukti T1/F14)** |
| `depth_1` | `eval_results_depth_1.csv` |
| `depth_4` | `eval_results_depth_4.csv` |
| `depth_5` | `eval_results_depth_5.csv` |

### Langkah 5 — Uji statistik + artefak turunan
```
python scripts/statistical_test.py
python scripts/boundary_condition.py
python scripts/depth_sensitivity_plot.py
```

### Langkah 5b — Figur headline (8 baru via `eval_charts.py`)
Script dibuat sebelum dijalankan. Figur: perbandingan 3 sistem, ablation impact, T1 kontras,
per-intent, P/R/F1, RAGAS dist boxplot, forest plot signifikansi, YAML validity.

### Langkah 6 — Laporan before/after + update STATUS.md
Tiga sumbu: (a) Indonesia→Inggris, (b) GT lama→baru 97→103 fixture, (c) HAS_PROPERTY→18-edge.
Isolasi T1 via A7 vs default. Integrity report: metrik <0,80 dilaporkan apa adanya + root-cause.

---

## File terdampak

- **BUAT:** `docs/AUDIT_E2E/phases/FASE_3.md` (ini); `scripts/eval_charts.py`
- **FIX:** `scripts/evaluate.py:665` (1.29→1.30 sidecar diagnostik)
- **REGEN:** `data/eval_results_{graphrag,vector,llm}_final.csv`, ablation × 10, `ragas_results_*.csv`,
  `statistical_test_results.csv`, `boundary_condition_gain.csv`, figur di `docs/TA-STI-template-1.0/images/`
- **ARSIP:** `data/_archive_pre_fase3/` (22 file lama)
- **TIDAK DISENTUH:** `TA.tex`, `Bab *.tex`, semua prosa tesis

---

## Catatan biaya & risiko

- Total ≈ 13 konfigurasi × 103 fixture + RAGAS 3×103 → berjam-jam. Gunakan resume bila terputus.
- Bila rate-limit LLM massal: stop, diagnosa, resume — jangan loop blind.
- Rollback: `data/_archive_pre_fase3/` berisi snapshot lengkap.
