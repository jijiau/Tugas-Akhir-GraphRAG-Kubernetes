# Critical Review — Threats to Validity, Fase 0 Audit E2E

> **Dihasilkan:** 2026-06-09 — Fase 0 (READ-ONLY). Dokumen ini mendaftar ancaman metodologis dan klaim yang rentan dipertanyakan penguji, **bukan** sekadar angka rendah. Setiap isu berisi bukti `file:line`, penilaian keparahan, dan rekomendasi: fix genuinely (perbaiki mekanisme) vs disclose jujur (akui limitasi).
>
> **Framing:** hipotesis "angka rendah = measurement rusak" **ditolak sebagai asumsi**. Setiap skor rendah bisa jadi: (1) bug measurement, (2) bug GT, atau (3) **defisiensi KG/mekanisme yang nyata**. Dokumen ini fokus pada kelas 3 dan ancaman metodologis yang melampaui sekedar angka.

---

## Ancaman #1 — KG 18-Edge Ter-dekopling dari Generasi Jawaban (F14) [KRITIS]

**Bukti:** `src/graph/queries.py:24-48` (`SCHEMA_DEPS_QUERY`), `:109-135` (`HYBRID_VECTOR_GRAPH_QUERY`); `src/chatbot/graph_agent.py:102-109`; `src/chatbot/custom_retriever.py:194-198`

**Apa yang terjadi:**
- LLM context (`graph_context`) dibangun dari `-[HAS_PROPERTY*1..d]->` saja — satu edge type, satu sumber saja
- 14 semantic edge (SELECTS_POD, ROUTES_TO_SERVICE, BINDS_ROLE, SCALES_RESOURCE, dll.) + EXTENDS/ONE_OF/ANY_OF tidak pernah masuk konteks
- `PATH_EDGES_QUERY` (semua 18 edge) menghasilkan `reasoning_path` yang dipakai untuk `path_coverage` dan `hop_accuracy` — ini adalah **komputasi berbeda** dari konteks yang menghasilkan jawaban
- 12,9% dari GT edges (356/2.756) bertipe non-HAS_PROPERTY → secara struktural tidak dapat dicapai oleh konteks produksi → ceiling path_coverage teoritis ≈87%

**Mengapa fatal untuk sidang:**
*"Anda klaim sistem menggunakan 18 relasi lintas-resource untuk meningkatkan retrieval. Bisakah Anda tunjukkan eksperimen di mana relasi SELECTS_POD atau ROUTES_TO_SERVICE mempengaruhi jawaban yang dihasilkan?"*

Jawaban jujur berdasarkan kode: tidak bisa. Mereka tidak masuk ke konteks LLM.

**Keputusan desain (pilihan user — TIDAK diputuskan sepihak):**
- **Opsi A (fix genuinely):** Ganti `SCHEMA_DEPS_QUERY` dan `HYBRID_VECTOR_GRAPH_QUERY` agar traversal menggunakan `_ALL_EDGE_TYPES`. Ini membuat klaim T1 terbukti dan bisa di-ablation. Biaya: re-run semua evaluasi, potensi context bloat.
- **Opsi B (disclose jujur):** Sempitkan klaim T1 — KG berperan dalam *representasi pengetahuan* (pengayaan node description lewat relasi) tapi retrieval aktual masih property-traversal. Akui di Bab IV/VII sebagai limitasi desain.

**Rekomendasi:** Opsi A jika waktu memungkinkan (perbaikan nyata); Opsi B jika tidak — tapi harus eksplisit di tesis.

---

## Ancaman #2 — Circularitas Ground Truth (Construct Validity)

**Bukti:** Fixture `expected_path` ditulis dalam vocabulary edge sistem sendiri (mis. `Service -[SELECTS_POD]-> Pod`). `path_coverage` mengukur apakah sistem mengreproduksi skema yang dirancang sendiri.

**Mengapa bermasalah:**
- Tidak ada oracle independen. GT path adalah "apa yang seharusnya ditelusuri menurut desainer" bukan "apa yang benar-benar menjawab pertanyaan".
- Jika fixture ditulis ulang pasca-fix (Fase 2), metrik akan ikut berubah — ini konsisten tapi bukan bukti kinerja nyata di domain baru.
- `path_coverage=0,85` berarti sistem mereproduksi 85% dari path yang dirancangnya sendiri. Ini bukan evaluasi eksternal.

**Penanganan:**
- Disclose di Bab III/VI: GT path divalidasi berdasarkan struktur swagger + domain knowledge penulis; keterbatasan independensi diakui.
- Tambahkan inter-rater check: minta minimal 1 orang lain memvalidasi 10-20% fixture `expected_path` secara independen.

---

## Ancaman #3 — HopAccuracy Menjadi Tautologi Pasca-Fix F3

**Bukti:** `scripts/evaluate.py:387-393`; `src/chatbot/custom_retriever.py:33-39` (`_DEPTH_BY_INTENT`)

**Skenario pasca-fix F3** (d_gt = intended depth 1–5):
- Intent "explain" → _DEPTH_BY_INTENT = 2 → sistem traversal sampai depth 2 → d_pred=2 → hop_accuracy=1.0 (selalu)
- Intent "generate_yaml" → depth=3 → d_pred=3 → hop_accuracy=1.0 (selalu)
- Depth adalah fungsi deterministik dari intent; sistem selalu traversal sampai depth yang diminta

**Mengapa bermasalah:** Metrik yang selalu 1.0 tidak mengukur apa pun. Laporan 100% hop accuracy bukan prestasi — itu tautologi.

**Rekomendasi:**
- **Ganti** dengan edge-recall dari `reasoning_path` vs `expected_path` (mirip `reaq_hop_accuracy_corrected` di `scripts/recompute_ragas.py:137-143`) — ini mengukur apakah *path yang benar-benar ditelusuri* cocok dengan path GT, bukan apakah depth-nya sama.
- Atau hapus sama sekali dan andalkan `path_coverage` sebagai satu-satunya path metric.

---

## Ancaman #4 — Baseline Strawman: Perbandingan Tidak Adil [PENTING]

**Bukti-A (Vector RAG, F1):** `scripts/evaluate.py:553,561`; `src/graph/queries.py:141-147`
- Vector baseline memanggil `SIMPLE_GRAPH_EXPAND_QUERY` yang sudah includes 1-hop expansion (HAS_PROPERTY + EXTENDS + CONTAINS_POD_TEMPLATE)
- Ini bukan pure dense retrieval — baseline sudah di-augmentasi grafnya

**Bukti-B (LLM baseline, F11-stat):** `data/statistical_test_results.csv`
- LLM baseline RetQ=0,0 dan path_coverage=0,072 karena sistem tidak memiliki retriever
- Melaporkan retrieval metric untuk no-retrieval system dan menghitung Δ sebagai "improvement" adalah **category error**
- Implikasinya: kemenangan RetQ GraphRAG vs LLM tidak informatif — tentu saja retrieval system mengambil lebih banyak node daripada tidak ada retrieval

**Mengapa fatal untuk sidang:**
*"RetQ GraphRAG=0,66 vs LLM=0,0 — itu bukan perbandingan yang bermakna. LLM memang tidak punya retriever. Kenapa Anda melaporkan retrieval metric untuk sistem tanpa retrieval?"*

**Penanganan:**
- Perbaiki Vector baseline ke pure dense (Fase 1, F1)
- Untuk LLM: laporkan hanya AnsQ dan ReaQ (metrik yang relevan untuk no-retrieval system); jangan laporkan RetQ/path_coverage/RGA untuk LLM baseline — atau jelaskan secara eksplisit mengapa tetap dilaporkan (untuk transparansi)

---

## Ancaman #5 — AnsQ GraphRAG Lebih Rendah dari Kedua Baseline [SIGNIFIKAN]

**Bukti:** `data/statistical_test_results.csv`
- GraphRAG AnsQ=0,5771 vs Vector=0,5916 (Δ=−0,0145, p_holm=0,14 — tidak signifikan)
- GraphRAG AnsQ=0,5771 vs LLM=0,5956 (Δ=−0,0185, p_holm=0,053 — tidak signifikan)

**Interpretasi:** Secara direktional, retrieval GraphRAG *tidak* membantu kualitas jawaban — bahkan sedikit menurunkannya (meskipun tidak signifikan secara statistik). Ini adalah **genuine mechanism deficiency** (RC=3).

**Kemungkinan penyebab:**
1. Konteks HAS_PROPERTY-only terlalu lebar (puluhan child nodes) → speaker terkubur informasi tidak relevan
2. `SPEAKER_MAX_CONTEXT_CHARS=12000` truncate → bagian relevan mungkin hilang
3. Kualitas GT answer lebih tinggi dari kemampuan sistem → answer_relevance cosine rendah

**Penanganan:**
- Ini adalah temuan yang harus *dilaporkan jujur* di Bab VI/VII, bukan disembunyikan
- Perbaikan AnsQ bergantung pada kualitas context yang masuk ke speaker — kandidat: perbaiki F14 (richer context), atau pertajam prompt speaker

---

## Ancaman #6 — n=19 untuk Klaim T2 (YAML Validation)

**Bukti:** `data/eval_results_graphrag_final.csv` → `ansq_syntactic_validity` n=19 (hanya fixture yaml_gen)

**Mengapa bermasalah:**
- Dengan n=19, 1 fixture yang berubah = ±5,3 poin. CI sangat lebar.
- Klaim T2 ("GraphRAG meningkatkan presisi YAML yang dihasilkan") berbasis sampel sangat kecil
- Syntactic validity identik di ketiga sistem (0,8947) — tidak ada perbedaan yang bisa diklaim

**Penanganan:**
- Extend evaluasi YAML ke fixture `followup` dan `realworld` yang mengandung YAML dalam jawaban
- Laporkan distribusi error YAML (layer mana yang gagal) untuk meningkatkan informativeness
- Atau akui n kecil sebagai limitasi dan fokus klaim T2 pada mekanisme validator, bukan angka

---

## Ancaman #7 — Embedding Lintas-Bahasa + Query Tidak Natural (F15)

**Bukti:** `src/graph/vector_index.py:15` (text-embedding-3-small, English-generic); `src/chatbot/custom_retriever.py:117` (query = keyword soup)

**Apa yang terjadi:**
- KG terindeks dengan embedding dari deskripsi swagger (English)
- Pertanyaan pengguna dalam Bahasa Indonesia
- Vektor fallback menggunakan `f"{primary} {related} Kubernetes"` — bukan pertanyaan asli, melainkan entity string
- Baseline vector embed *pertanyaan asli* (`evaluate.py:560`) — asimetri desain

**Mengapa bermasalah:**
- Jika retrieval vektor lemah, ini adalah **genuine mechanism deficiency** (RC=3), bukan bug yang bisa diperbaiki dengan threshold tuning
- Pilihan embedding model tidak pernah dijustifikasi atau dibandingkan (tidak ada ablation embedding model)

**Penanganan:**
- Disclose dalam Bab III/VII sebagai pilihan implementasi dengan trade-off: multilingual model lebih lambat/mahal, English-specific lebih efisien untuk swagger terindeks dalam English
- Atau ablation: bandingkan `text-embedding-3-small` vs `multilingual-e5-large` pada subset fixture

---

## Ancaman #8 — Single-Run, LLM Stokastik, Tanpa Reliability Testing (F16)

**Bukti:** `scripts/evaluate.py` (tidak ada `random_seed` atau `temperature=0` yang dikunci); `scripts/statistical_test.py:129` (Wilcoxon one-run scores)

**Apa yang terjadi:**
- Setiap angka metrik adalah point estimate dari satu kali jalan evaluasi
- GPT-4o-mini (thinker) dan Groq (speaker) stokastik — RGA binary bisa flip per-run
- Wilcoxon + bootstrap mengasumsikan scores adalah tetap, padahal mereka adalah random variable

**Mengapa bermasalah:**
- Confidence interval dari bootstrap mengukur *sampling variability across fixtures*, bukan *measurement reliability across runs*
- Ini adalah systematic omission yang bisa dipertanyakan penguji: *"Apakah hasil ini reproducible jika dijalankan ulang?"*

**Penanganan:**
- Minimal: jalankan 3× dengan konfigurasi identik; laporkan mean ± std-dev per metrik
- Atau: lock temperature=0 untuk determinisme (tapi Groq mungkin tidak support fully)
- Atau: akui sebagai limitasi di Bab VI: "evaluasi single-run; reliabilitas antar-jalan tidak diuji"

---

## Ancaman #9 — Generalisasi T1: 14 Edge Hand-Coded, Tidak General (F9)

**Bukti:** `src/ingestion/parser.py:324-371` (Pass 3: 17 Cypher queries hardcoded untuk ~15 resource)

**Apa yang terjadi:**
- KG dengan 18 edge type hanya valid untuk resources yang dikodekan eksplisit di Pass 3
- CRD baru, operator, atau resource di luar daftar tidak akan memiliki semantic edges
- Tesis tidak boleh mengklaim "sistem otomatis mengekstraksi 18 jenis relasi dari swagger"

**Penanganan:**
- Ganti klaim menjadi: "14 relasi semantik diderivasi berdasarkan pola domain Kubernetes yang diidentifikasi secara manual dari struktur swagger + dokumentasi K8s"
- Akui keterbatasan skalabilitas di Bab VII

---

## Ancaman #10 — Validasi Pakar: Status Tidak Dikonfirmasi (F13)

**Bukti:** `docs/validation/expert-questionnaire.md`, `docs/validation/expert-brief.md` (materi ada); tidak ada `docs/validation/results*.json/csv`

**Apa yang bermasalah:**
- n=4 penguji terlalu kecil untuk klaim reliabilitas inter-annotator yang kuat
- Jika hasil belum terkumpul, klaim validasi eksternal tidak bisa masuk tesis

**Penanganan:**
- Konfirmasi ke user: apakah hasil pakar sudah dikumpulkan? Di mana filenya?
- Jika belum: akui sebagai "planned but not completed" atau hapus klaim validasi pakar

---

## Ringkasan: Apa yang Bisa vs Tidak Bisa Dijanjikan ≥0,85

| Kelompok | Metrik | Bisa ≥0,85? | Kondisi |
|----------|--------|-------------|---------|
| Sudah ≥0,85 | YAML syntactic (0,8947), path_coverage (0,8515) | ✅ Ya | Jaga (path_coverage perlu transparansi F14) |
| Kemungkinan pasca-fix | RetQ, ReaQ, YAML schema | ⚠️ Mungkin | Bergantung F1+F2+F7′ (RetQ), F12 (schema) |
| Tidak pasti | AnsQ, RGA | ⚠️ Tidak pasti | AnsQ < baseline → genuine deficiency (F14, F15); RGA binary sensitif |
| Intrinsik sulit | RAGAS faithfulness, ctx metrics | ⚠️ Sulit | LLM judge ketat; disclose sebagai limitasi jika <0,85 pasca-fix |
| Tautologi (harus diganti) | hop_accuracy (lama) | 🔴 N/A | Ganti formula (Ancaman #3) |
