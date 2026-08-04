# Rangkuman Daftar Pustaka TA — Panduan Sidang

Dokumen ini merangkum seluruh **27 entri** di `daftar-pustaka.bib` (per 2026-07-25): apa yang dibahas tiap sumber, metode & hasilnya, di mana disitasi dalam naskah, untuk mendukung klaim apa, dan kalimat siap-ucap kalau penguji menanyakannya langsung.

**Cara pakai saat sidang:**
- Penguji sebut judul/nama penulis → cari di **Bagian 1** (tabel utama, per referensi).
- Penguji tanya "di Bab X kamu nyitir apa saja?" → cari di **Bagian 2** (indeks per-Bab).
- Kolom **Jawaban siap ucap** dirancang untuk dibaca hampir apa adanya.

**Legenda kolom Hasil Utama:** ✓ = dinyatakan di naskah TA dan/atau diverifikasi ke sumber asli · — = tidak ada klaim hasil kuantitatif yang relevan disitasi (sumber bersifat definisi/dokumentasi/deskriptif, bukan dikarang).

---

## Bagian 1 — Tabel Utama (per Referensi)

### A. Motivasi & Masalah

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 1 | Gartner (2021) `gartner_cloud_2021` | Gartner (*Press Release*) | Proyeksi adopsi *cloud-native* pada beban kerja digital global | Laporan/proyeksi industri (*press release*) | ✓ >95% beban kerja digital ter-*deploy* *cloud-native* pd 2025, naik dari 30% (2021) | Bab I §Latar Belakang | Membuka argumen urgensi transformasi *cloud-native* | "Proyeksi Gartner: >95% beban kerja digital jadi *cloud-native* di 2025, naik dari 30% di 2021 — jadi dasar urgensi industri buat penelitian ini." |
| 2 | CNCF (2023) `cncf_2023_survey` | CNCF Annual Survey (Laporan Industri) | Adopsi Kubernetes di produksi/evaluasi industri | Survei tahunan industri | ✓ Produksi naik 58%→66% (2022→2023); total adopsi 81%→84% | Bab I; Bab III (B01) | Bukti dominasi pasar K8s; landasan B01 (inefisiensi waktu) | "Survei CNCF: adopsi produksi K8s naik 58%→66% dalam setahun — buktinya K8s itu mainstream, jadi masalah konfigurasinya berdampak luas, bukan niche." |
| 3 | Soldani dkk. (2018) `soldani_pains_2018` | Journal of Systems and Software | Tantangan & manfaat arsitektur *microservices* | *Systematic grey literature review* | — (tinjauan kualitatif, bukan angka) | Bab II §Arsitektur *Cloud* Modern (4×) | Definisi *cloud-native*, *microservices*, API sbg kontrak, *cascading failures* | "Tinjauan literatur sistematis ini sumber definisi *cloud-native* dan *microservices* saya, termasuk kenapa API jadi kontrak kritikal dan risiko *cascading failures*." |
| 4 | Rahman dkk. (2023) `rahman2023misconfigurations` | ACM Transactions on Software Engineering and Methodology (TOSEM) | Miskonfigurasi keamanan pada manifes K8s *open-source* | Studi empiris (*mining* manifes OSS) | ✓ 18% manifes rentan serius; ~80% miskonfigurasi bersifat struktural | Bab I; Bab II (validator graf); Tabel 12 | Justifikasi B03; dasar validasi struktural berbasis graf sbg alternatif *dry-run* | "Studi ini: 18% manifes K8s *open-source* rentan, dan ~80% miskonfigurasi sifatnya struktural — bisa dideteksi analisis statis. Itu dasar kenapa saya bangun validasi struktural berbasis graf." |
| 5 | Liu dkk. (2024) `liu2024deepanalysis` | IEEE Transactions on Software Engineering (TSE) | Korektnas, kompleksitas, keamanan kode hasil *LLM code-gen* | Studi analitis/empiris keluaran *code-gen* LLM | — (temuan kualitatif: sintaksis benar tapi semantik keliru) | Bab I; Bab III (B02); Tabel 12 | Bukti LLM bisa salah semantik walau sintaksis benar → dasar B02 | "Studi ini tunjukkan LLM bisa hasilkan kode yang sintaksisnya benar tapi semantiknya salah — makanya sistem saya tidak cukup andalkan *syntactic validity*, harus ada *schema compliance* & *hop-accuracy* juga." |

### B. Keterbatasan LLM & Halusinasi

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 6 | Ji dkk. (2023) `ji_hallucination_2023` | ACM Computing Surveys | Survei fenomena halusinasi pada *natural language generation* | Survei literatur (ACM Computing Surveys) | — (deskriptif: taksonomi jenis & sumber halusinasi) | Bab III (B02) | Legitimasi bahwa halusinasi itu fenomena terdokumentasi & terukur | "Survei ACM ini justifikasi bahwa halusinasi LLM itu fenomena yang sudah terdokumentasi & terukur secara akademik, bukan cuma anekdot — jadi B02 punya dasar ilmiah." |
| 7 | Wan dkk. (2025) `wan2025empowering` | Advanced Engineering Informatics | RAG hibrida (KG Neo4j + *vector*) utk Q&A domain *smart manufacturing* (DfAM) | Eksperimen — KG dari 69 publikasi teknis + *Semantic Alignment*/*Prompt Enhancement*, GPT-4o vs *vector-only* | ✓ *Exact Match* 63,4%→77,8% (+14,4pp); *Context Precision* 69,8%→76,5% (+6,7pp) | **Sitasi terpadat** — Bab I (2×); Bab II (3×); Bab III (adopsi, adaptasi, keterbatasan); Tabel 12 (2×) | Bukti kuantitatif keunggulan hybrid KG-*vector*; basis pendekatan yg diadopsi & diadaptasi | "Sitasi paling sentral di TA saya. Wan dkk. buktikan hybrid KG-*vector* naikkan *Exact Match* 63,4%→77,8% dibanding *vector-only* — dasar kuantitatif saya pilih hybrid. Tapi *constraint* manual mereka (*Semantic Alignment*) tak *scalable* utk 730 skema K8s, makanya saya ganti dg validasi struktural berbasis graf — itu kontribusi pembeda saya." |

### C. Fondasi RAG

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 8 | Gao dkk. (2024) `rag_survey` | arXiv (*preprint*, 2312.10997) | Survei komprehensif RAG — taksonomi Naive/Advanced/Modular RAG | Survei literatur (arXiv 2312.10997) | ✓ Taksonomi 3 paradigma RAG; tinjauan *retrieval-generation-augmentation* | Bab II (arsitektur RAG, keterbatasan *chunking*); Tabel 12 (2×) | Definisi & keterbatasan mendasar RAG *vector-based* (relasi struktural hilang saat *chunking*) | "Survei Gao dkk. ini sumber definisi umum RAG saya, sekaligus tempat saya kutip keterbatasan mendasarnya: *chunking* memecah dokumen jadi potongan independen sehingga relasi struktural hilang — argumen inti kenapa saya pakai graf, bukan *vector-only*." |
| 9 | Zhao dkk. (2024) `zhao_rag_survey_2024` | arXiv (*preprint*, 2402.19473) | Survei RAG utk *AI-generated content* secara luas | Survei literatur (arXiv 2402.19473) | — (dipakai utk definisi metrik, bukan hasil kuantitatif sumber) | Bab II (def Precision@k/Recall@k/F1@k; klasifikasi tipe kueri) | Sumber definisi metrik RetQ; justifikasi *intent-adaptive retrieval* | "Survei ini sumber definisi metrik *retrieval* saya (Precision@k, Recall@k, F1@k), dan bukti bahwa klasifikasi tipe kueri sebelum *retrieval* naikkan presisi konteks — landasan *intent-adaptive depth traversal* saya." |
| 10 | Moreno-Cediel dkk. (2025) `moreno2025rag` | Knowledge-Based Systems | Strategi *chunking* semantik baru (*growing window*) atasi *weak semantic boundaries* | Eksperimen — strategi *chunking* baru vs *existing* | — (tidak dikutip angka di naskah) | Bab II (RAG utk *knowledge-intensive tasks*; metrik *Syntactic Validity*) | Definisi RAG utk tugas *knowledge-intensive*; rujukan metrik *Syntactic Validity* YAML | "Saya kutip paper strategi *chunking* semantik ini sbg sumber definisi RAG utk tugas *knowledge-intensive*, dan rujukan metrik *Syntactic Validity* yg saya pakai utk YAML." |
| 11 | Es dkk. (2023) `es_ragas_2023` | arXiv (*preprint*, 2309.15217) | Kerangka evaluasi RAG *reference-free* — RAGAS | Proposal *framework* metrik (arXiv 2309.15217) | ✓ 3 komponen: *Faithfulness*, *Answer Relevance*, *Context Relevance*; tanpa perlu anotasi manusia | **Sentral utk metrik** — Bab II (2×); Bab VI (2×); Tabel 29a/29c/31c | Sumber 2 metrik yg diadopsi: AnsQ (*Answer Semantic Similarity*) & ReaQ (*Faithfulness*) | "RAGAS itu kerangka evaluasi RAG *reference-free* dg 3 metrik: *Faithfulness*, *Answer Relevance*, *Context Relevance*. Saya adopsi 2 saja jadi AnsQ & ReaQ. *Context Precision/Recall* punya RAGAS sengaja saya ganti RetQ berbasis *node* mengikuti IR standar Manning, karena *retrieval* saya berbasis graf, bukan *chunk* teks." |

### D. Knowledge Graph

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 12 | Hofer dkk. (2024) `hofer2024construction` | Information (MDPI) | *State-of-the-art* & tantangan konstruksi *Knowledge Graph* | Survei/tinjauan literatur (Information, MDPI) | — (deskriptif) | Bab II (definisi KG) | Definisi dasar *Knowledge Graph* (node-*entitas*, *edge*-relasi) | "Ini sumber definisi dasar *Knowledge Graph* saya — representasi pengetahuan berbentuk *node* (entitas) dan *edge* (relasi) yang bermakna semantik." |
| 13 | Yu dkk. (2021) `yu2021visualkg` | Journal of Physics: Conference Series | Aplikasi praktis *visual knowledge graph* pd model layanan teknologi | Studi aplikasi/kasus | — (sumber ilustrasi, bukan klaim kuantitatif) | Bab II (*caption* gambar arsitektur KG) | Sumber gambar ilustrasi arsitektur *Knowledge Graph* | "Ini sumber gambar ilustrasi arsitektur *Knowledge Graph* di Bab II — murni referensi visual, bukan klaim kuantitatif." |
| 14 | Abu-Salih (2021) `abusalih2021domain` | Journal of Network and Computer Applications | Survei taksonomi konstruksi KG spesifik domain | Survei literatur (J. Network & Computer Applications) | ✓ Taksonomi 2 dimensi: basis pengetahuan (*schema-based/-free/hybrid*) × teknik (*rule-based/learning-based/neural/off-the-shelf*) | Bab II (teks + *caption* gambar taksonomi) | Kerangka memposisikan penelitian: *schema-based* + *rule/knowledge-based* | "Taksonomi Abu-Salih ini yg saya pakai memposisikan penelitian: *schema-based* (dari OpenAPI K8s) dikombinasikan *rule/knowledge-based* (aturan transformasi deterministik) — beda dari pendekatan *schema-free* berbasis LLM yang stokastik." |
| 15 | Pan dkk. (2024) `pan2024unifying` | IEEE Transactions on Knowledge and Data Engineering (TKDE) | *Roadmap* integrasi LLM & KG — 3 kerangka besar | *Roadmap*/survei posisi (IEEE TKDE) | ✓ 3 *framework*: KG-*enhanced* LLM, LLM-*augmented* KG, *Synergized* LLM+KG | Bab I (justifikasi *pipeline* deterministik); Bab II (2×) | Argumen LLM & KG saling melengkapi; dasar ekstraksi KG deterministik (bukan berbasis LLM yg stokastik) | "*Roadmap* Pan dkk. definisikan 3 skema integrasi LLM-KG. Saya pakai utk: (1) argumen LLM & KG saling melengkapi, dan (2) dasar kenapa saya pilih ekstraksi KG deterministik berbasis skema, bukan berbasis LLM yg stokastik & tak konsisten antareksekusi." |
| 16 | Ma dkk. (2025) `ma_llm_kg_2025` | arXiv (*preprint*, 2505.20099) | Taksonomi sintesis LLM+KG utk *Question Answering* | Survei literatur/taksonomi terstruktur (arXiv 2505.20099) | ✓ Taksonomi berbasis kategori QA & peran KG; identifikasi limitasi LLM-QA (*reasoning* lemah, pengetahuan usang, halusinasi) | **Sentral** — Bab II (4×: kerangka evaluasi, def GraphRAG formal, model $p_\theta$) | Fondasi kerangka evaluasi 3 dimensi AnsQ/RetQ/ReaQ (tulang punggung Bab VI) | "Ini fondasi metodologi evaluasi saya — kerangka 3 dimensi AnsQ/RetQ/ReaQ yg saya pakai sepanjang Bab VI diadaptasi langsung dari taksonomi Ma dkk. Saya juga pakai formulasi matematis GraphRAG $p_\theta(y\mid x,\mathcal{K})$ dari paper ini." |

### E. GraphRAG & Sistem Terkait

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 17 | Han dkk. (2024/25) `han_graphrag_2024` | arXiv (*preprint*, 2501.00309) | Survei komprehensif GraphRAG — kerangka 5 komponen | Survei literatur besar (arXiv 2501.00309, 18 penulis) | ✓ Kerangka: *query processor*, *retriever*, *organizer*, *generator*, *data source* | Bab II (2×: def GraphRAG; risiko *information overload*) | Definisi formal GraphRAG; landasan risiko *traversal* dalam → *intent-adaptive depth* | "Survei GraphRAG Han dkk. ini sumber definisi GraphRAG saya — mekanisme *graph traversal* utk ambil konteks terstruktur. Temuan mereka soal risiko *information overload* kalau *traversal* terlalu dalam jadi salah satu alasan saya butuh kedalaman adaptif per *intent*." |
| 18 | Yu dkk. (2025) `civiot2025graphrag` | Future Internet (MDPI) | Mesin dialog GraphRAG utk QA platform *Civil IoT Taiwan* | Studi kasus/eksperimen — KG semi-otomatis via GPT-4.1 + Llama-3-TAIDE utk NL→*graph query* | ✓ F1 > 0,7 pd kueri multi-entitas | Bab II (*Penelitian Terkait*, 2×); Bab III (celah teknis); Tabel 12 (2×) | Penelitian pembanding #1 — bukti KG statis tanpa *update* dinamis jadi limitasi umum | "Ini salah satu dari 3 penelitian pembanding utama saya. Mereka capai F1>0,7 pakai GraphRAG utk platform IoT Taiwan, tapi KG-nya statis & mahal diadaptasi ke platform lain. Beda dg saya: graf mereka dari narasi dokumen tak terstruktur, punya saya dari skema OpenAPI deterministik." |
| 19 | Lu dkk. (2025) `hsgrag2025acm` | ACM Transactions on Design Automation of Electronic Systems (TODAES) | Konstruksi basis pengetahuan graf semantik hierarkis (HSG-RAG) utk *embedded system* | Eksperimen — graf dari SDK/*datasheet* 3 platform HW, pencarian *top-down* dg dekomposisi sub-kueri | ✓ (kualitatif) Jawaban lebih spesifik/ringkas/lengkap vs VanillaRAG & GraphRAG konvensional | Bab II (*Penelitian Terkait*); Bab III; Tabel 12 (2×) | Penelitian pembanding #2 — pola keterbatasan berulang (KG statis + taksonomi relasi generik) | "HSG-RAG ini penelitian pembanding kedua saya — KG hierarkis utk dokumentasi *embedded*, dg strategi pencarian *top-down* yg memecah kueri jadi sub-kueri. Saya adopsi ide dekomposisi bertingkat ini, tapi terapkan ke skema Kubernetes yg hierarkinya lebih terstruktur & formal." |
| 20 | He dkk. (2024) `he2024gretriever` | ICLR 2024 (Prosiding) | Arsitektur G-Retriever — GNN + LLM utk pemahaman graf tekstual besar | Eksperimen — algoritma *Prize-Collecting Steiner Tree* (PCST), tanpa *fine-tuning* LLM | ✓ Token dipangkas 99%; validitas *node* 31%→77% (+46pp); validitas *edge* 12%→76% | Bab III (Alternatif Solusi #2; Matriks WSM K1–K4) | Kandidat alternatif solusi #2 — kuat presisi konteks (K4=5), lemah fleksibilitas pemeliharaan (K3=4) | "G-Retriever salah satu dari 3 alternatif solusi yg saya bandingkan pakai WSM. Hasilnya impresif — validitas *node* naik 31%→77%, *edge* 12%→76%, token dipangkas 99% — tapi butuh GNN yg harus di-*index* ulang tiap versi K8s berubah, jadi kalah di kriteria fleksibilitas pemeliharaan dibanding *hybrid* saya." |
| 21 | Cao dkk. (2025) `cao2025neusymrag` | arXiv (*preprint*, 2505.19754) | *Hybrid neural-symbolic* RAG dg *relational DB* + aturan simbolik utk PDF QA | Eksperimen — validasi inferensi LLM deterministik via aturan simbolik (arXiv 2505.19754) | ✓ Akurasi validasi >90% pd dataset QA terstruktur | Bab III (Alternatif Solusi #3; Matriks WSM); Tabel 12 (2×) | Kandidat alternatif solusi #3 — kuat kontrol halusinasi (K4=4), lemah representasi hierarki (K1=3) & generatif (K2=2) | "NeuSym-RAG capai akurasi validasi >90% dg pendekatan *neural-symbolic* berbasis *relational DB*. Tapi skema relasional kurang cocok utk hierarki bersarang 730 skema K8s tanpa banyak SQL *join*, dan sifatnya lebih ke validasi/*consistency-checking* — makanya K1 & K2 saya beri lebih rendah dibanding *hybrid* KG-*vector*." |
| 22 | Li dkk. (2025) `li_cotrag_2025` ⚠️ | arXiv (*preprint*, 2504.13534) | Integrasi *Chain-of-Thought reasoning* ke *pipeline* RAG (CoT-RAG) | — (tidak diverifikasi, tak disitasi) | — | **TIDAK ADA — entri mati di `.bib`** | **TIDAK ADA** | "Entri ini ada di daftar pustaka tapi TIDAK saya sitasi di mana pun dalam naskah. Kalau ditanya: ini perlu dibersihkan dari `.bib`, bukan bagian argumen TA." |

### F. Dokumentasi API & Kubernetes

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 23 | Kotstein & Decker (2024) `kotstein_restberta_2024` | Cluster Computing | QA berbasis *transformer* (BERT) utk pencarian semantik dok. Web API tanpa ontologi formal | Eksperimen — model *transformer* utk *semantic search* (Cluster Computing) | — (deskriptif, tak ada angka dikutip di naskah) | Bab II (relevansi RAG thd dok K8s API); Tabel 12 | Bukti pemrosesan semantik dok API bisa tanpa ontologi formal; sumber ambiguitas *keyword-based search* | "RESTBERTa tunjukkan pemrosesan semantik dokumentasi API bisa tanpa ontologi formal, cukup dari nama parameter & struktur hierarkis. Saya pakai juga utk tunjukkan kelemahan *keyword-based search*: ambiguitas saat *keyword* sama (mis. 'labels', 'ports') muncul di banyak objek beda." |
| 24 | *The Kubernetes Authors* (2024) `k8s_docs_concepts` | kubernetes.io (Dokumentasi Resmi) | Dokumentasi resmi konsep-konsep Kubernetes | Dokumentasi resmi | — (n/a) | Bab II (IaC) | Definisi pendekatan *Infrastructure as Code* & *desired state* | "Ini dokumentasi resmi Kubernetes, sumber definisi *Infrastructure as Code* saya — pengembang mendeklarasikan *desired state* via YAML." |
| 25 | *The Kubernetes Authors* (2024) `kubernetes_docs` | kubernetes.io / CNCF (Dokumentasi Resmi) | Dokumentasi resmi lengkap Kubernetes (arsitektur, API, dst.) | Dokumentasi resmi (CNCF) | — (n/a) | Bab II (3×: def platform, gambar arsitektur, metrik *Schema Compliance*) | Definisi K8s sbg platform orkestrasi; acuan skema OpenAPI v1.30 utk *Schema Compliance* | "Dokumentasi resmi K8s ini sumber definisi platform, gambar arsitektur klaster (*Control Plane* + *Worker Nodes*), dan acuan skema OpenAPI v1.30 yg saya pakai utk metrik *Schema Compliance*." |

### G. Metodologi & Fondasi IR

| No | Sitasi | Nama Jurnal/Sumber | Membahas Apa | Metode | Hasil Utama | Disitasi Di | Untuk Klaim Apa | Jawaban Siap Ucap |
|---|---|---|---|---|---|---|---|---|
| 26 | Niaksu (2015) `niaksu2015` | Baltic Journal of Modern Computing | Perluasan metodologi CRISP-DM utk domain medis | *Position paper*/proposal metodologi | — (n/a, sumber definisi metodologi) | Bab I §Metodologi (2×: teks + gambar) | Justifikasi pemilihan CRISP-DM sbg kerangka metodologi TA | "Niaksu ini rujukan CRISP-DM saya — saya pilih *framework* ini karena prosesnya terstruktur, iteratif, dan bisa diadaptasi utk sistem berbasis data & representasi pengetahuan, sesuai kebutuhan TA saya." |
| 27 | Manning, Raghavan, Schütze (2008) `manning_ir_2008` | Cambridge University Press (Buku) | Buku teks fondasi *Information Retrieval* — *precision*, *recall*, *indexing*, evaluasi sistem | Buku teks akademik (Cambridge University Press) | ✓ Kerangka formal *precision/recall/relevance*, *inverted index*, evaluasi sistem IR klasik | **Sentral utk metrik** — Bab II (3×: RetQ, *Hop-Accuracy*); Bab VI; Tabel 29b/29c/31b | Fondasi metrik IR standar (P/R) → RetQ berbasis *node*; *edge recall* → *Hop-Accuracy* | "Buku IR klasik Manning dkk. ini fondasi metrik saya: Precision@k & Recall@k berbasis *node* utk RetQ, dan konsep *edge recall* yg saya adaptasi jadi *Hop-Accuracy* utk ReaQ. Saya sengaja pilih metrik IR standar berbasis *node*, bukan *Context Precision/Recall* RAGAS, karena *retrieval* saya berbasis graf bukan *chunk* teks." |

---

## Bagian 2 — Indeks Balik per-Bab (Lookup Mundur)

Dipakai untuk pertanyaan tipe *"di bagian ini kamu nyitir apa saja?"* — dicek ulang terhadap naskah, termasuk kalimat yang panjang.

```
Bab I (Pendahuluan)
  gartner_cloud_2021, cncf_2023_survey, rahman2023misconfigurations,
  liu2024deepanalysis, wan2025empowering, pan2024unifying, niaksu2015

Bab II (Studi Literatur)
  soldani_pains_2018, kubernetes_docs, k8s_docs_concepts, wan2025empowering,
  kotstein_restberta_2024, hofer2024construction, yu2021visualkg,
  abusalih2021domain, pan2024unifying, rahman2023misconfigurations,
  ma_llm_kg_2025, han_graphrag_2024, es_ragas_2023, manning_ir_2008,
  rag_survey, zhao_rag_survey_2024, moreno2025rag,
  civiot2025graphrag, hsgrag2025acm   (§Penelitian Terkait, bersama wan2025empowering)

Bab III (Analisis Masalah)
  cncf_2023_survey (B01), ji_hallucination_2023 (B02), liu2024deepanalysis (B02),
  rahman2023misconfigurations (B03), civiot2025graphrag, hsgrag2025acm,
  wan2025empowering, he2024gretriever, cao2025neusymrag
  → Tabel 12 (perbandingan gap): liu2024deepanalysis, wan2025empowering, rag_survey,
    kotstein_restberta_2024, civiot2025graphrag, hsgrag2025acm,
    rahman2023misconfigurations, cao2025neusymrag

Bab VI (Evaluasi)
  es_ragas_2023 (AnsQ & Faithfulness), manning_ir_2008 (Hop-Accuracy)
  → Tabel 29a/29b/29c, 31b/31c mengulang kedua sitasi ini sbg rujukan formula metrik

Tidak disitasi di bab manapun
  li_cotrag_2025  ⚠️ entri mati di .bib
```

**Cek silang:** setiap `key` di atas punya baris di Bagian 1, dan sebaliknya — tidak ada sitasi yang hilang di salah satu sisi.

---

## Catatan Penting

1. **`li_cotrag_2025` (CoT-RAG, Li dkk. 2025) tidak disitasi di manapun** dalam naskah TA meski ada di `daftar-pustaka.bib`. Sebelum sidang, putuskan: hapus dari `.bib`, atau cari titik yang relevan untuk menyitasinya (mis. terkait *reasoning path*/CoT pada mekanisme *traversal*).
2. **Tanda ✓ / —** pada kolom *Hasil Utama*: ✓ berarti klaim didukung naskah TA sendiri dan/atau diverifikasi ke sumber asli (abstrak/paper). Tanda — berarti sumber tersebut memang tidak digunakan untuk klaim angka spesifik di TA ini (biasanya sumber definisi/dokumentasi/tinjauan kualitatif) — bukan kelalaian, dan tidak dikarang.
3. **8 sumber yang diverifikasi langsung ke publikasi asli** (bukan hanya dari kutipan naskah): `es_ragas_2023`, `manning_ir_2008`, `rag_survey`, `he2024gretriever` (juga dari naskah), `cao2025neusymrag` (juga dari naskah), `pan2024unifying`, `ma_llm_kg_2025`, `han_graphrag_2024`.
4. Sitasi paling sering & paling penting untuk dikuasai: **`wan2025empowering`** (7+ titik sitasi, tulang punggung argumen Bab I–III), **`ma_llm_kg_2025`** (kerangka evaluasi AnsQ/RetQ/ReaQ), **`manning_ir_2008`** & **`es_ragas_2023`** (fondasi seluruh metrik Bab VI).
