# Daftar Pertanyaan Sidang yang Diantisipasi

**Acuan angka:** Selalu gunakan tabel di Bab VI, bukan dokumen PHASE_9 (sudah usang).

---

## Q1: Mengapa menggunakan GraphRAG bukan Vector RAG biasa?

**Jawaban:** Kubernetes adalah domain berbasis skema hierarkis dengan relasi eksplisit antar-resource (Deployment → PodSpec → Container). Vector RAG menggunakan kemiripan semantik teks, yang gagal menangkap relasi struktural ini. GraphRAG menggunakan traversal deterministik pada *knowledge graph* yang dibangun dari Swagger/OpenAPI Kubernetes — memberikan konteks multi-hop yang presisi.

**Bukti:** RetQ GraphRAG = 0,7259 vs Vector RAG = 0,4255 (Δ = +0,30, p < 0,001). Path Coverage 0,8515 vs 0,5411.

---

## Q2: Bagaimana knowledge graph Kubernetes dibangun?

**Jawaban:** KG dibangun dari Swagger spec Kubernetes v1.29 melalui 5-fase pipeline (`SwaggerGraphBuilder`):
1. Pass 1: Node `Definition` (nama, kind, scope, deskripsi)
2. Pass 1.5: Embedding vektor 1536-dim (`text-embedding-3-small`)
3. Pass 2: Edge `HAS_PROPERTY` struktural (resolusi `$ref`)
4. Pass 2.5: Edge `EXTENDS`/`ONE_OF`/`ANY_OF` (pewarisan tipe)
5. Pass 3: 18 jenis edge semantik (`CONTAINS_POD_TEMPLATE`, `USES_SECRET`, dll.)

KG disimpan di Neo4j dan di-query via Cypher deterministik.

---

## Q3: Bagaimana retriever memilih node awal?

**Jawaban:** Dua fase:
1. **Phase 1 (exact match):** Cypher query cocokkan `primary_resource` ke node `Definition` secara eksak. Jika ditemukan, traversal dilanjutkan.
2. **Phase 2 (vector fallback):** Jika tidak ada exact match, gunakan `db.index.vector.queryNodes` untuk cari node terdekat berdasarkan embedding pertanyaan.

Kedalaman traversal adaptif berdasarkan intent: `explain`/`followup` = depth 2, `generate_yaml`/`planning`/`trace_relationship` = depth 3.

---

## Q4: Mengapa AnsQ tidak berbeda signifikan?

**Jawaban:** AnsQ mengukur kualitas teks jawaban akhir (relevansi cosine, faithfulness, syntactic validity). Ketiga sistem menggunakan model LLM yang sama (GPT-4o-mini). Perbedaan utama ada di *context* yang diberikan, bukan di kemampuan teks generation LLM itu sendiri. AnsQ lebih sensitif terhadap kualitas LLM daripada kualitas konteks.

**Angka:** AnsQ: GraphRAG 0,5771 | Vector RAG 0,5916 | Vanilla LLM 0,5956 → n.s.

---

## Q5: Apa arti RGA dan mengapa penting?

**Jawaban:** RGA (Retrieval-to-Generation Alignment) mengukur seberapa banyak node yang diambil oleh retriever benar-benar muncul dalam jawaban LLM. RGA GraphRAG = 0,4536 vs Vector RAG = 0,2784 — menunjukkan bahwa konteks KG yang diambil lebih banyak dimanfaatkan oleh LLM, bukan dibuang.

---

## Q6: Seberapa besar keunggulan GraphRAG dan apakah praktis signifikan?

**Jawaban:** Δ RetQ = +0,30 (CI 95% [+0,23; +0,37]). Ini adalah practical significance yang besar — dari 0,43 ke 0,73, hampir 70% peningkatan relatif. Uji statistik: Wilcoxon signed-rank + bootstrap, koreksi Holm-Bonferroni untuk multiple comparison, p < 0,001 (***).

Untuk ReaQ: Δ = +0,225 (0,5554 − 0,3307), p < 0,001.

---

## Q7: Apa peran ablasi dalam validasi klaim?

**Jawaban:** 6 studi ablasi memvalidasi setiap komponen arsitektur:
- **A1** (no_phase1/exact match): RetQ −0,249*** → exact match esensial
- **A2** (no_multihop): RetQ −0,601*** → traversal multi-hop adalah komponen terpenting
- **A3** (depth=2 fixed): HopAcc −0,124*** → depth adaptif diperlukan
- **A4** (depth=3 fixed): ≈0 n.s. → depth 3 aman, tapi adaptif lebih optimal untuk explain/followup
- **A5** (no_yaml_layer3): ReaQ turun (p=0,007) → lapisan validasi KG berkontribusi nyata
- **A6c** (no_multi_entity): penurunan kecil untuk planning/generate_yaml → multi-entity penting untuk query kompleks

---

## Q8: Validitas YAML ketiga sistem identik (0,8947) — di mana kontribusi validasi YAML?

**Jawaban:** Kontribusi validasi YAML bukan pada *skor* syntactic validity yang lebih tinggi, melainkan pada **metode**: validasi required-field berbasis KG (Layer 3) tanpa memerlukan *dry-run* pada kluster Kubernetes aktif. Ini praktis dan aman untuk lingkungan produksi.

Bukti bahwa lapisan 3 berkontribusi nyata: ablasi A5 menunjukkan ReaQ turun signifikan (p = 0,007) ketika lapisan 3 dinonaktifkan — artinya validasi struktural KG memengaruhi kualitas penalaran sistem.

Identitas 0,8947 antar-sistem bukan kelemahan: menunjukkan sistem GraphRAG tidak over-constrain output YAML dengan validasi yang berlebihan, sambil tetap memberikan keunggulan ReaQ.

---

## Q9: Mengapa menggunakan dataset 97 fixture, bukan dataset publik?

**Jawaban:** Tidak ada *benchmark* publik yang tersedia untuk domain spesifik ini (konfigurasi Kubernetes dalam bahasa Indonesia/teknis campuran). Dataset 97 fixture didesain berdasarkan 8 kategori pertanyaan yang diidentifikasi dari wawancara mendalam dengan 3 praktisi DevOps/SRE. Validitas dataset dikonfirmasi melalui expert evaluation: 4 pakar menilai relevansi 4,42/5 dan kepercayaan trace 4,50/5.

---

## Q10: Apa keterbatasan sistem dan penelitian ini?

**Jawaban:**
1. KG dibangun dari Swagger spec statis — tidak *real-time* update dengan versi Kubernetes baru
2. Evaluasi dengan LLM tunggal (GPT-4o-mini) — hasil mungkin berbeda dengan model lain
3. Dataset dalam konteks Kubernetes spesifik — generalisasi ke domain lain perlu penelitian lanjutan
4. Hop Accuracy masih 0,35 — banyak query multi-hop yang path-nya belum optimal
5. Realworld fixture menunjukkan Δ terendah (+0,089) — skenario dunia nyata yang sangat beragam masih sulit

---

*Untuk angka detail: gunakan Tabel 31 (perbandingan), Tabel 32 (ablasi), Tabel 33 (uji statistik), Tabel 34 (boundary condition) di Bab VI.*
