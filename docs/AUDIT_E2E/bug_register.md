# Bug Register — Fase 0 Audit E2E

> **Dihasilkan:** 2026-06-09 — Fase 0 (READ-ONLY). Setiap baris berisi `file:line`, kuantifikasi dampak, dan atribusi root-cause ke kelas 1 (measurement bug), 2 (gold-standard bug), atau 3 (defisiensi KG/mekanisme nyata).
>
> **Gunakan dokumen ini** sebagai input Fase 1 (perbaikan kode) dan Fase 2 (re-kurasi fixture). Jangan ubah kode/data tanpa konfirmasi user per-temuan.

---

## Legenda

| Kolom | Keterangan |
|-------|-----------|
| **RC** | Root-Cause Class: **1** = bug measurement, **2** = bug gold-standard, **3** = defisiensi KG/mekanisme nyata |
| **Sev** | Severity dampak terhadap target >0,85: 🔴 kritis · 🟠 tinggi · 🟡 sedang |
| **Fase** | Fase penanganan utama |
| **Verifiable-wrong?** | Apakah ini bug yang *dapat dibuktikan salah* (bukan opini/tuning)? |

---

## Tabel Temuan

| ID | Temuan | file:line | Mekanisme penekanan | Metrik terdampak + angka | RC | Sev | Fase | Verifiable-wrong? |
|----|--------|-----------|--------------------|--------------------------|----|-----|------|-------------------|
| **F14** | **Context path hanya traversal `HAS_PROPERTY`; 14 edge semantik + EXTENDS/ONE_OF/ANY_OF tidak pernah masuk konteks LLM** | `src/graph/queries.py:26` (`SCHEMA_DEPS_QUERY`), `:110-113` (`HYBRID_VECTOR_GRAPH_QUERY`); `src/chatbot/graph_agent.py:102-109`; `src/chatbot/custom_retriever.py:194-198` | LLM context dibangun dari `-[HAS_PROPERTY*1..d]->` saja. `PATH_EDGES_QUERY` (semua 18 edge, `:85-103`) dipakai hanya untuk *display* reasoning_path. Komentar `:52-53` klaim `_ALL_EDGE_TYPES` dipakai di `SCHEMA_DEPS_QUERY` — kontradiksi body query. Klaim T1 bahwa 18 edge meningkatkan retrieval tak terbukti dari jalur evaluasi. | RetQ (path_coverage kena: 12,9% GT edge tak terjangkau konteks path); RGA (mengandalkan path_coverage); AnsQ (faithfulness grounding dari konteks terbatas) | **3** | 🔴 | 1 (keputusan desain) | ✅ Ya: `SCHEMA_DEPS_QUERY` body ≠ komentar; verified end-to-end via `evaluate.py:535-548` → `graph_agent.py:102` → `custom_retriever.py:194` |
| **F2** | **Fixture `command` (3) + `troubleshooting` (3=6 total) out-of-scope: tanya operasi runtime, jawab flag `kubectl`, tak bisa diturunkan dari blok `definitions`** | `tests/fixtures/command/kubectl_force_delete_pod.json:9` (answer berisi `--grace-period=0 --force`); `tests/fixtures/command/kubectl_find_pods_with_env.json`; `tests/fixtures/troubleshooting/crashloopbackoff_oomkilled.json` dst. | Fixture menguji kinerja LLM (halusinasi pretrain) bukan retrieval. GT: `command` n_relevant=59,7 avg, n_edges=75,0 avg, n_key=59,7 avg (zero-curation 100%); `troubleshooting` n_relevant=65,4, n_edges=81,8, n_key=65,4 (zero-curation 100%). 6 fixture out-of-scope dari total 97 = 6,2% polusi | RetQ (recall/F1/ndcg ditekan: retriever balik ~3-5 node dari 60-87 GT); `path_coverage` mendekati 0 (edge GT 75-82 tak bisa dicakup 3-hop HAS_PROPERTY); AnsQ faithfulness (key_nodes=relevant_nodes, tak terkurasi) | **2** | 🔴 | 2 | ✅ Ya: domain definitions terkunci, runtime kubectl di luar scope |
| **F3** | **HopAccuracy menggunakan `d_gt = len(expected_path)` (jumlah edge ~28–111) bukan depth 1–5** | `scripts/evaluate.py:391` | `hop_accuracy = 1.0 if d_pred == d_gt else 0.0`. `d_gt` berkisar 3–112 (rata-rata GT edge), sementara `d_pred` = `len(reasoning_path)` ~3–10. Hampir selalu 0. | reaq_hop_accuracy baseline=0,3505 (artefak: sesekali path length kebetulan sama) | **1** | 🔴 | 1 | ✅ Ya: `d_gt` seharusnya depth 1–5 per intent-mapping |
| **F7′** | **3 nilai `top_k` berbeda tanpa justifikasi: prod seed=1, GraphRetriever=3, eval vector=5** | `src/graph/queries.py:110` (seed=1); `src/retrieval/graph_retriever.py:15` (top_k=3 default); `scripts/evaluate.py:561` (top_k=5 vector eval) | Seed=1 di HYBRID membatasi recall RetQ dari awal. top_k mempengaruhi jumlah kandidat awal yang lalu di-traverse. Nilai berbeda menjadikan perbandingan tak adil. | RetQ recall/F1/ndcg (directionally, belum dikuantifikasi; perlu sweep k) | **1** | 🟠 | 1 | ✅ Ya: inkonsistensi nilai terverifikasi; asimetri prod vs eval adalah bug desain |
| **F5** | **RAGAS faithfulness n lebih kecil dari answer_relevancy: graphrag faithfulness n=88 vs answer_relevancy n=97** | `scripts/recompute_ragas.py:226` (`has_retrieval` gate), `:148-153` (`_safe_float` NaN→None) | faithfulness membutuhkan `has_retrieval=True` dan pemanggilan RAGAS berhasil. 9 fixture graphrag gagal produce faithfulness (kemungkinan timeout/NaN RAGAS API). Tak ada log jumlah kegagalan per-metrik. | ragas_faithfulness graphrag 0,2125 (n=88); vector 0,1551 (n=59) | **1** | 🟡 | 1 | ✅ Ya: n-mismatch terverifikasi di `data/ragas_summary_by_mode.csv` |
| **F1** | **Vector RAG baseline tidak murni: menggunakan `SIMPLE_GRAPH_EXPAND_QUERY` (1-hop expansion HAS_PROPERTY+EXTENDS+CONTAINS_POD_TEMPLATE), bukan pure dense top-k** | `scripts/evaluate.py:553,561`; `src/graph/queries.py:141-147` | Perbandingan GraphRAG vs Vector tidak sahih. Vector baseline sudah memiliki akses graf 1-hop. | Semua metrik GraphRAG-vs-Vector: perbandingan tidak sahih | **1** | 🟠 | 1 | ✅ Ya: SIMPLE_GRAPH_EXPAND_QUERY body ada OPTIONAL MATCH 1-hop |
| **F6** | **Docstring basi RetQ: klaim `(f1+ndcg+path_coverage)/3` tapi kode `(f1+ndcg)/2`** | `scripts/evaluate.py:284` (docstring) vs `:341` (kode) | Bug komentar saja; kode benar. Tapi menyesatkan saat audit/peer-review | path_coverage dikira masuk RetQ composite (tidak; dilaporkan terpisah) | **1** | 🟡 | 1 | ✅ Ya: kontradiksi docstring vs kode |
| **F8** | **Threshold RGA 0,5 hardcode tanpa sitasi untuk sub-threshold** | `scripts/evaluate.py:435` | `RGA=1` jika faithfulness≥0,5 AND answer_relevance≥0,5 AND path_coverage≥0,5. Sitasi Han 2024 ada di .bib untuk metrik AR keseluruhan, tapi tidak untuk nilai 0,5 tiap sub-komponen. | RGA binary 0,4536 — sensitif terhadap threshold; belum dikalibrasi | **1** | 🟡 | 1 | ✅ Ya: sitasi Han 2024 tidak merujuk sub-threshold 0,5 |
| **F12** | **Schema validity divalidasi terhadap K8s 1.29, bukan 1.30 (scope data)** | `src/validation/yaml_validator.py:45`; `scripts/evaluate.py` (memanggil validator yang sama) | Perubahan schema v1.29→1.30 bisa menyebabkan field valid 1.30 ditolak validator 1.29 | `ansq_schema_compliance` 0,7895 (n=19) — mungkin underestimate | **1** | 🟡 | 1 | ✅ Ya: versi tidak cocok dengan scope data yang dideklarasikan |
| **F4** | **3 fixture conceptual memiliki node GT yang tidak ada di definitions swagger** | `tests/fixtures/conceptual/persistent_volume_concept.json` (`AccessMode`); `conceptual/secret_types.json` (`SecretType`); `conceptual/storageclass_concept.json` (FQN `io.k8s.storage.v1.StorageClass` → benar: `io.k8s.api.storage.v1.StorageClass`) | `AccessMode` dan `SecretType` tidak memiliki entry di swagger `definitions` (merupakan enum/string type, bukan resource). Node tak ada di KG → retriever tidak bisa balik → recall=0 untuk node tsb. | RetQ recall/F1/ndcg untuk 3 fixture ini; faithfulness untuk storageclass (node salah FQN) | **2** | 🟠 | 2 | ✅ Ya: node tidak ditemukan di `kubernetes_swagger.json["definitions"]` |
| **F9** | **14 dari 18 edge type adalah hand-coded semantic pattern, bukan auto-derived dari swagger** | `src/ingestion/parser.py:324-371` | Pass 3 menggunakan Cypher hardcode untuk ~15 resource spesifik. Tidak generalisasi ke resource/CRD baru. | Bukan penekan metrik; ancaman validitas klaim T1 ("auto-derived") | **3** | 🟡 | Dok (Bab IV/VII) | ✅ Ya: kode Pass 3 jelas hand-coded |
| **F10** | **Validator Layer 3 di evaluate.py hanya aktif saat ablation (bukan production)** | `scripts/evaluate.py:240` | Layer 3 Neo4j required-field check di-skip untuk production run (`ablation_mode=None`). Artinya `layer3_compliance=None` di angka utama. | AnsQ composite produksi tidak mencakup Layer 3; klaim T2 hanya valid pada ablation | **1** | 🟡 | 1/Dok | ✅ Ya: kondisi `ablation_mode is not None` terverifikasi |
| **F11** | **Statistik: AnsQ GraphRAG LEBIH RENDAH dari kedua baseline (meski tidak signifikan)** | `data/statistical_test_results.csv` | GraphRAG AnsQ=0,5771 vs Vector=0,5916 (Δ=−0,0145, p_holm=0,14) dan vs LLM=0,5956 (Δ=−0,0185, p_holm=0,053). Bukan signifikan, tapi arahnya terbalik. | AnsQ: klaim "GraphRAG meningkatkan kualitas jawaban" tidak didukung data | **3** | 🟠 | Dok/3 | ✅ Ya: data CSV terverifikasi |
| **F13** | **Hasil validasi pakar n=4 belum dikonfirmasi terkumpul** | `docs/validation/expert-questionnaire.md`, `docs/validation/expert-brief.md` | Materi ada, hasil belum terlihat. n=4 terlalu kecil untuk klaim reliabilitas inter-annotator | Klaim validitas eksternal tesis | **?** | 🟠 | Klarifikasi user | Perlu cek manual |
| **F15** | **Embedding bahasa campur + query tidak natural: `text-embedding-3-small` (English) meng-embed kueri Indonesia; kueri vector = keyword soup, bukan pertanyaan asli** | `src/graph/vector_index.py:15`; `src/chatbot/custom_retriever.py:117` | Embedding English-centric meng-embed Indonesia queries. Keyword soup `f"{primary} {related} Kubernetes"` menghilangkan konteks sintaksis pertanyaan. Baseline vector (evaluate.py:560) embed pertanyaan asli — asimetri. | RetQ (recall tergantung kualitas embedding); AnsQ (faithfulness tergantung node yang ditemukan) | **3** | 🟠 | Dok/1 | ✅ Ya: kode terverifikasi |
| **F16** | **Evaluasi tampak single-run; LLM stokastik tanpa seed/uji-ulang; komposit tanpa justifikasi bobot** | `scripts/evaluate.py` (tak ada `random_seed` / `temperature=0`); `evaluate.py:260` (AnsQ mean uniform); `:341` (RetQ 2-metric avg); `:416` (ReaQ = grounding saja) | LLM (GPT-4o-mini thinker + Groq speaker) stokastik → metrik binary (RGA) bisa flip per-run. Bobot komposit arbitrary (unweighted mean, droping path_coverage dan hop_accuracy dari composite) tanpa sensitivity analysis. | Semua metrik: reliability tidak diketahui; agregat bisa misleading | **3** | 🟠 | Dok | Perlu uji empiris (jalankan 3× lalu bandingkan) |

---

## Ringkasan per Root-Cause Class

| Kelas | ID bug | Penanganan |
|-------|--------|-----------|
| **1 — Measurement bug** | F1, F3, F5, F6, F7′, F8, F10, F12 | Perbaiki kode (Fase 1); angka naik secara sah |
| **2 — Gold-standard bug** | F2, F4 | Re-kurasi fixture (Fase 2); angka naik secara sah |
| **3 — Defisiensi KG/mekanisme nyata** | F9, F11, F14, F15, F16 | Keputusan desain (F14: opsi a/b); disclose jujur sebagai limitasi (Bab VII); JANGAN tuning |
| **? — Perlu konfirmasi** | F13 | Klarifikasi ke user |

---

## Distribusi fixture out-of-scope (6 dari 97)

| Fixture | Dir | n_relevant | n_edges | n_key | Answerability |
|---------|-----|-----------|---------|-------|--------------|
| kubectl_export_namespace_resources | command | 7 | 3 | 7 | OUT_OF_SCOPE |
| kubectl_find_pods_with_env | command | 86 | 111 | 86 | OUT_OF_SCOPE |
| kubectl_force_delete_pod | command | 86 | 111 | 86 | OUT_OF_SCOPE |
| crashloopbackoff_oomkilled | troubleshooting | 87 | 112 | 87 | OUT_OF_SCOPE |
| deployment_rollout_stuck | troubleshooting | 29 | 32 | 29 | OUT_OF_SCOPE |
| service_no_endpoints | troubleshooting | 39 | 43 | 39 | OUT_OF_SCOPE |

**3 troubleshooting lainnya**: tidak dikonfirmasi out-of-scope (SUSPECT; perlu cek manual isi jawaban).

---

## Distribusi edge type di `expected_path` (quantifikasi F14)

Dari 2.756 GT edge total (97 fixture):

| Edge type | Count | % | Terjangkau konteks? |
|-----------|-------|---|---------------------|
| HAS_PROPERTY | 2.400 | 87,1% | ✅ Ya |
| ONE_OF | 66 | 2,4% | ❌ Tidak |
| CONTAINS_POD_TEMPLATE | 45 | 1,6% | ❌ Tidak |
| EXTENDS | 41 | 1,5% | ❌ Tidak |
| USES_SERVICE_ACCOUNT | 33 | 1,2% | ❌ Tidak |
| HAS_CONTAINER | 31 | 1,1% | ❌ Tidak |
| MOUNTS_VOLUME | 31 | 1,1% | ❌ Tidak |
| USES_SECRET | 31 | 1,1% | ❌ Tidak |
| lainnya (9 tipe) | 78 | 2,8% | ❌ Tidak |
| **Total non-HAS_PROPERTY** | **356** | **12,9%** | ❌ **Tidak — ceiling path_coverage dari sisi context = ~87,1%** |

> **Implikasi:** meskipun fixture GT-nya sempurna, `path_coverage` di jalur produksi secara struktural terbatas ≤ ~0,87 (ceiling teoritis) selama konteks dibangun HAS_PROPERTY-only. Ini adalah defisiensi mekanisme (RC=3, F14), bukan measurement bug.

---

## Node GT tidak ada di KG (3 fixture)

| Fixture | Node Hilang | Status |
|---------|-------------|--------|
| conceptual/persistent_volume_concept | `io.k8s.api.core.v1.AccessMode` | Tidak ada di swagger definitions (enum, bukan resource) |
| conceptual/secret_types | `io.k8s.api.core.v1.SecretType` | Tidak ada di swagger definitions (string type, bukan resource) |
| conceptual/storageclass_concept | `io.k8s.storage.v1.StorageClass` | FQN salah; benar: `io.k8s.api.storage.v1.StorageClass` |
