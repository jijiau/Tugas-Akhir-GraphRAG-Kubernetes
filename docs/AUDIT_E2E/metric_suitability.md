# Metric Suitability — Fase 0 Audit E2E

> **Dihasilkan:** 2026-06-09 — Fase 0 (READ-ONLY). Tiap metrik dinilai: formula, tujuan, sitasi, kecocokan scope `definitions`, dan verdict (pertahankan / perbaiki / buang).
>
> Target: **>0,85 semua metrik** setelah perbaikan Fase 1+2. Jika setelah perbaikan jujur masih <0,85, laporkan apa adanya (Bab VII) — jangan tuning threshold.
>
> **Angka baseline:** dari `data/eval_results_graphrag_final.csv` (n=97) + `data/ragas_summary_by_mode.csv`.

---

## Dimensi AnsQ (Answer Quality)

### AnsQ-1: `ansq_syntactic_validity`

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0` jika `yaml.safe_load(yaml_candidate)` sukses, else `0.0` — `scripts/evaluate.py:187-194` |
| **GT field** | Tidak perlu GT; cukup YAML string dari jawaban |
| **Tujuan** | T2 (YAML validator) |
| **Sitasi** | Implicit (standar YAML parsing); tidak memerlukan sitasi eksternal |
| **Scope definitions?** | ✅ Ya — menguji output sistem |
| **Baseline GraphRAG** | **0,8947** (n=19; hanya fixture yaml_gen) |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | n=19 terlalu kecil; CI lebar. Metrik valid tapi klaim T2 rapuh di n kecil. Pastikan semua `yaml_gen` (15) + subset `followup`/`realworld` yang menghasilkan YAML dihitung. |

### AnsQ-2: `ansq_schema_compliance`

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0` jika `kubernetes_validate.validate(data, "1.29", strict=False)` sukses, else `0.0` — `src/validation/yaml_validator.py:42-53`; `scripts/evaluate.py:199-213` |
| **GT field** | Tidak perlu GT |
| **Tujuan** | T2 |
| **Sitasi** | Kubernetes OpenAPI schema (implicit); versi 1.29 perlu dikonfirmasi ke sitasi resmi K8s docs |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | **0,7895** (n=19) |
| **Verdict** | ⚠️ **Perbaiki (F12)** |
| **Catatan** | Scope data K8s v1.30, validator memakai v1.29 (`yaml_validator.py:45`). Update ke 1.30 atau jelaskan justifikasi 1.29 (versi stabil closest). |

### AnsQ-3: `ansq_answer_relevance`

| Aspek | Detail |
|-------|--------|
| **Formula** | Cosine similarity (OpenAI `text-embedding-3-small`) antara jawaban sistem dan `ground_truth["answer"]` — `scripts/evaluate.py:218-222` |
| **GT field** | `ground_truth.answer` |
| **Tujuan** | T1, T3 (relevansi jawaban terhadap pertanyaan) |
| **Sitasi** | Perlu sitasi untuk cosine embedding similarity sebagai proxy relevance (mis. BERTScore, atau RAGAS answer_relevancy) |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | AnsQ composite=0,5771 (sub-metric tidak tersedia terpisah di CSV; estimasi dari AnsQ avg) |
| **Verdict** | ✅ **Pertahankan** dengan catatan |
| **Catatan** | ⚠️ Secara intrinsik sulit ≥0,85 (bergantung kualitas jawaban referensi dan panjang GT answer). Jika <0,85 pasca-perbaikan: kandidat perbaikan = pertajam GT answer, BUKAN tuning embedding. |

### AnsQ-4: `ansq_faithfulness`

| Aspek | Detail |
|-------|--------|
| **Formula** | `hit / len(gt_nodes)` di mana `hit` = jumlah node dari `key_nodes` (atau `relevant_nodes` jika key_nodes absen) yang disebut dalam jawaban — `scripts/evaluate.py:224-235` |
| **GT field** | `ground_truth.key_nodes` (primer) → `ground_truth.relevant_nodes` (fallback) |
| **Tujuan** | T1 (retrieved context masuk jawaban) |
| **Sitasi** | Konsep grounding/faithfulness dari RAGAS (es_ragas_2023 di .bib:134) |
| **Scope definitions?** | ✅ Ya — tapi tergantung kurasi `key_nodes` |
| **Baseline GraphRAG** | Terikat ke AnsQ composite 0,5771 |
| **Verdict** | ⚠️ **Perbaiki (F2, F4)** |
| **Catatan** | Fixture command+troubleshooting: key_nodes = relevant_nodes (tidak dikurasi, 60-87 node) → faithfulness artifisial rendah. Setelah re-kurasi Fase 2, sub-metrik ini seharusnya naik. |

### AnsQ-5: `ansq_layer3_compliance`

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0` jika tidak ada field required Neo4j yang hilang dari YAML; hanya aktif di ablation (bukan production) — `scripts/evaluate.py:237-258` |
| **GT field** | YAML dari jawaban + Neo4j `HAS_PROPERTY {is_required: true}` |
| **Tujuan** | T2 (ablation study) |
| **Sitasi** | Internal |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | `None` (production run) |
| **Verdict** | ✅ **Pertahankan untuk ablation** |
| **Catatan** | Logis bahwa L3 hanya diukur di ablation; tapi tesis harus jelas bahwa production AnsQ tidak mencakup L3. |

---

## Dimensi RetQ (Retrieval Quality)

### RetQ-1: `retq_f1_at_k`

| Aspek | Detail |
|-------|--------|
| **Formula** | `2PR/(P+R)` di mana P=precision@k, R=recall@k atas `relevant_nodes` — `scripts/evaluate.py:312-315` |
| **GT field** | `ground_truth.relevant_nodes` |
| **Tujuan** | T1 |
| **Sitasi** | Standard IR metric; tidak butuh sitasi spesifik |
| **Scope definitions?** | ✅ Ya — tapi rentan F2 (GT terlalu lebar) |
| **Baseline GraphRAG** | Bagian dari RetQ composite 0,6631 |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | Akan membaik secara sah setelah re-kurasi `relevant_nodes` (Fase 2) dan perbaikan top_k (Fase 1). |

### RetQ-2: `retq_ndcg_at_k`

| Aspek | Detail |
|-------|--------|
| **Formula** | `DCG/IDCG` dengan discount log2 — `scripts/evaluate.py:318-326` |
| **GT field** | `ground_truth.relevant_nodes` |
| **Tujuan** | T1 |
| **Sitasi** | Standard NDCG (Manning et al., IR textbook); tambahkan ke .bib jika belum ada |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | Bagian dari RetQ composite 0,6631 |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | Edge case: `if no expected_nodes → NDCG=1.0` (`evaluate.py:326`) dapat inflate NDCG untuk fixture tanpa GT. Periksa apakah ada fixture dengan `relevant_nodes=[]`. |

### RetQ-3: `retq_path_coverage`

| Aspek | Detail |
|-------|--------|
| **Formula** | `matched_edges / len(expected_path)` — `scripts/evaluate.py:328-339` |
| **GT field** | `ground_truth.expected_path` |
| **Tujuan** | T1 (multi-hop graph traversal coverage) |
| **Sitasi** | Kustom; perlu justifikasi di Bab II |
| **Scope definitions?** | ✅ Ya — tapi ceiling teoritis ~87,1% (12,9% GT edge bertipe non-HAS_PROPERTY tak terjangkau konteks produksi) |
| **Baseline GraphRAG** | **0,8515** ≥0,85 ✅ |
| **Verdict** | ⚠️ **Pertahankan dengan transparansi F14** |
| **Catatan** | Dilaporkan terpisah dari RetQ composite (benar). Angka 0,85 terlihat bagus, **tetapi** ini adalah perbandingan path display (`PATH_EDGES_QUERY`, 18 edge) vs GT path — bukan path context (`SCHEMA_DEPS_QUERY`, HAS_PROPERTY only). Jika F14 diperbaiki (opsi a), ceiling akan naik lebih akurat. Jika tidak, harus didisclose. |

### RetQ-composite: `retq_retq_score`

| Aspek | Detail |
|-------|--------|
| **Formula** | `(f1_at_k + ndcg_at_k) / 2` — `scripts/evaluate.py:341` |
| **Baseline GraphRAG** | **0,6631** |
| **Verdict** | ⚠️ **Perbaiki docstring F6** |
| **Catatan** | path_coverage tidak masuk composite (dilaporkan terpisah) — keputusan yang defensible. Perbaiki docstring `:284` yang salah klaim `/3`. |

---

## Dimensi ReaQ (Reasoning Quality)

### ReaQ-1: `reaq_hop_accuracy`

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0 if d_pred == d_gt else 0.0`; `d_gt = len(expected_path)` — `scripts/evaluate.py:387-393` |
| **GT field** | `ground_truth.expected_path` |
| **Tujuan** | T1 (depth akurasi) |
| **Sitasi** | Tidak ada sitasi untuk formula ini |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | **0,3505** (artefak F3); `reaq_hop_accuracy_corrected` dari RAGAS = 0,6389 (n=90, edge-recall formula berbeda) |
| **Verdict** | 🔴 **Perbaiki (F3) atau BUANG** |
| **Catatan** | Setelah F3 fix (d_gt = intended depth 1–5), metrik menjadi **tautologi**: depth selalu = _DEPTH_BY_INTENT[intent] (deterministik). Hampir pasti 1.0. Pertimbangkan: ganti dengan edge-recall dari reasoning_path vs expected_path edges (mirip `hop_accuracy_corrected` di recompute_ragas.py), atau hapus dan ganti. **Ini metrik paling bermasalah secara konseptual.** |

### ReaQ-2: `reaq_grounding_score`

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0 - hallucination_rate`; `hallucination_rate = 1 - (grounded_terms/answer_terms)` menggunakan regex K8s + KG vocabulary — `scripts/evaluate.py:395-414` |
| **GT field** | `graph_context` (hasil retrieval, bukan GT fixture) |
| **Tujuan** | T1 (halusinasi) |
| **Sitasi** | Perlu sitasi untuk hallucination rate via grounding check (mis. RAGAS faithfulness, atau Es et al. 2023) |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | Bagian dari ReaQ composite 0,7602 |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | Grounding terhadap `graph_context` (HAS_PROPERTY only) — bila F14 diperbaiki, vocabulary lebih kaya. |

### ReaQ-composite: `reaq_reaq_score`

| Aspek | Detail |
|-------|--------|
| **Formula** | `= grounding_score` (hop_accuracy dilaporkan terpisah) — `scripts/evaluate.py:416` |
| **Baseline GraphRAG** | **0,7602** |
| **Verdict** | ✅ **Pertahankan** |

---

## RGA (Retrieval-Grounded Answer)

| Aspek | Detail |
|-------|--------|
| **Formula** | `1.0` jika `faithfulness≥0,5 AND answer_relevance≥0,5 AND path_coverage≥0,5` — `scripts/evaluate.py:435` |
| **Tujuan** | T1 (end-to-end correctness) |
| **Sitasi** | Han et al. 2024 (`han_graphrag_2024`, .bib:101) untuk metrik AR keseluruhan; sub-threshold 0,5 tanpa sitasi langsung |
| **Scope definitions?** | ✅ Ya |
| **Baseline GraphRAG** | **0,4536** |
| **Verdict** | ⚠️ **Perbaiki (F8)** |
| **Catatan** | Binary metric sensitif terhadap threshold. Setelah F1-F3-F7′ diperbaiki, angka akan berubah. Justifikasikan threshold 0,5 atau rujuk Han 2024 lebih spesifik. |

---

## RAGAS Metrics (Eksternal)

### RAGAS-1: `ragas_faithfulness`

| Aspek | Detail |
|-------|--------|
| **Formula** | Entailment antara jawaban dan retrieved contexts via LLM judge — Es et al. 2023 |
| **Sitasi** | `es_ragas_2023` (.bib:134) ✅ |
| **Baseline GraphRAG** | **0,2125** (n=88 dari 97; 9 missing kemungkinan NaN/timeout) |
| **Verdict** | ⚠️ **Perbaiki (F5)** |
| **Catatan** | ⚠️ Secara intrinsik sulit ≥0,85 (LLM judge ketat). Bila <0,85 pasca-perbaikan: laporkan sebagai limitasi. Investigasi 9 missing (F5). |

### RAGAS-2: `ragas_answer_relevancy`

| Aspek | Detail |
|-------|--------|
| **Formula** | Cosine similarity antara pertanyaan dan jawaban (via LLM-generated questions) |
| **Sitasi** | `es_ragas_2023` ✅ |
| **Baseline GraphRAG** | **0,5118** (n=97) |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | ⚠️ Secara intrinsik sulit ≥0,85; bergantung kualitas jawaban. Bila <0,85: kandidat perbaikan = pertajam GT answer dan prompt speaker. |

### RAGAS-3: `ragas_context_precision`

| Aspek | Detail |
|-------|--------|
| **Formula** | Fraction of retrieved context chunks grounded dalam GT answer |
| **Sitasi** | `es_ragas_2023` ✅ |
| **Baseline GraphRAG** | **0,3169** (n=97) |
| **Verdict** | ✅ **Pertahankan** |
| **Catatan** | Rendah: konteks HAS_PROPERTY only mengambil banyak node tak relevan untuk pertanyaan spesifik. Akan membaik bila F14 opsi (a) diterapkan. |

### RAGAS-4: `ragas_context_recall`

| Aspek | Detail |
|-------|--------|
| **Formula** | Fraction of GT answer grounded dalam retrieved context |
| **Sitasi** | `es_ragas_2023` ✅ |
| **Baseline GraphRAG** | **0,3799** (n=97) |
| **Verdict** | ✅ **Pertahankan** |

---

## YAML Metrics

### YAML syntactic + schema (per-fixture, n=19)

| Metrik | Formula | Baseline | Verdict |
|--------|---------|---------|---------|
| Syntactic | `yaml.safe_load` sukses | 0,8947 ✅ | Pertahankan; pastikan n coverage benar |
| Schema | `kubernetes_validate(data, "1.29")` | 0,7895 | Perbaiki versi ke 1.30 (F12) |

---

## Rekap verdict per metrik

| Metrik | Baseline | Target >0,85 | Verdict | Bisa ≥0,85 secara jujur? |
|--------|---------|-------------|---------|--------------------------|
| YAML syntactic | 0,8947 | ✅ sudah | Pertahankan | ✅ Ya |
| path_coverage | 0,8515 | ✅ sudah | Pertahankan + transparansi F14 | ✅ Ya (ceiling ~0,87 tanpa F14 fix) |
| RetQ composite | 0,6631 | ❌ | Pertahankan + perbaiki F1/F2/F7′ | ✅ Mungkin setelah fix |
| ReaQ composite | 0,7602 | ❌ | Pertahankan | ✅ Mungkin setelah fix |
| YAML schema | 0,7895 | ❌ | Perbaiki F12 | ✅ Mungkin setelah fix |
| AnsQ composite | 0,5771 | ❌ | Pertahankan + perbaiki F2 | ⚠️ Tidak pasti (AnsQ < baseline) |
| RGA | 0,4536 | ❌ | Perbaiki F8 + tergantung F1/F2/F3 | ⚠️ Tidak pasti |
| hop_accuracy (lama) | 0,3505 | ❌ | **PERBAIKI atau BUANG** (F3) | 🔴 Tautologi pasca-fix |
| RAGAS faithfulness | 0,2125 | ❌ | Pertahankan + investigasi F5 | ⚠️ Intrinsik sulit; laporkan apa adanya |
| RAGAS ctx_precision | 0,3169 | ❌ | Pertahankan | ⚠️ Tergantung F14 |
| RAGAS ctx_recall | 0,3799 | ❌ | Pertahankan | ⚠️ Tergantung F14 |
| RAGAS answer_relevancy | 0,5118 | ❌ | Pertahankan | ⚠️ Intrinsik sulit |
