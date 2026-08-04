# Skeleton Slide Presentasi Sidang

**Durasi target:** 20 menit presentasi + 30 menit tanya jawab
**Jumlah slide:** ~18-22 slide

---

## Slide 1 — Cover
- Judul: "Implementasi Graph Retrieval-Augmented Generation untuk Meningkatkan Presisi Retrieval dan Validitas Sintaksis pada Konfigurasi Kubernetes"
- Nama: Jihan Aurelia — 18222001
- Pembimbing: Dr. Ir. Dimitri Mahayana, M.Eng.
- Tanggal sidang

---

## Slide 2 — Latar Belakang
- Kubernetes: platform orkestrasi kontainer dominan, konfigurasi YAML kompleks
- LLM generatif berguna tapi sering menghasilkan YAML tidak valid / jawaban tanpa jejak logis
- Gap: tidak ada sistem yang mengkombinasikan retrieval berbasis KG dengan validasi struktural tanpa dry-run
- → Motivasi GraphRAG Kubernetes

---

## Slide 3 — Rumusan Masalah & Tujuan
- **T1:** Bagaimana membangun KG dari spesifikasi Kubernetes?
- **T2:** Bagaimana merancang retriever adaptif berbasis intent?
- **T3:** Apakah GraphRAG lebih unggul dari Vector RAG dan Vanilla LLM?
- Kontribusi: (1) KG Kubernetes dari Swagger, (2) retriever adaptif multi-hop, (3) validasi YAML via KG tanpa dry-run

---

## Slide 4 — Arsitektur Sistem (Diagram)
- Gambar arsitektur: Ingestion pipeline → Neo4j KG → LangGraph agent (Thinker → Retriever → Speaker)
- Highlight: 3 fase ingestion → 5-fase SwaggerGraphBuilder → 18 jenis edge
- Highlight: intent-aware depth (2 atau 3)

---

## Slide 5 — Knowledge Graph Kubernetes
- 5-fase pipeline pembangunan KG (Pass 1 → 1.5 → 2 → 2.5 → 3)
- 18 jenis edge semantik: HAS_PROPERTY, CONTAINS_POD_TEMPLATE, BINDS_ROLE, dll.
- Visualisasi sub-graph Deployment → PodSpec → Container
- Statistik: jumlah node, jumlah edge

---

## Slide 6 — Retriever Adaptif
- Phase 1 (exact match) → Phase 2 (vector fallback)
- Depth adaptif: explain/followup = 2, generate_yaml/planning/trace = 3
- Multi-entity retrieval untuk planning/generate_yaml

---

## Slide 7 — Validasi YAML 3 Lapisan
- Layer 1: PyYAML syntactic parsing
- Layer 2: kubernetes-validate schema (v1.29)
- Layer 3: KG required-field check (KONTRIBUSI BARU — tanpa dry-run pada kluster aktif)
- Bandingkan dengan alternatif: dry-run perlu kluster aktif dan berrisiko

---

## Slide 8 — Metodologi Evaluasi
- 97 fixture, 8 kategori pertanyaan
- Metrik: AnsQ (Answer Quality), RetQ (Retrieval Quality), ReaQ (Reasoning Quality)
- + metrik domain K8s: Path Coverage, Hop Accuracy, RGA, YAML Syntactic Validity
- 3 sistem: GraphRAG vs Vector RAG vs Vanilla LLM
- Uji statistik: Wilcoxon + bootstrap, koreksi Holm-Bonferroni

---

## Slide 9 — Hasil Utama: Bar Chart per Faktor ⭐

```
Faktor          GraphRAG  Vector RAG  Vanilla LLM
-----------------------------------------------------
RetQ            0,7259    0,4255      0,0241      ***
ReaQ            0,5554    0,3307      0,3351      ***
Path Coverage   0,8515    0,5411      0,0722      ***
Hop Accuracy    0,3505    0,0000      0,0722      ***
RGA             0,4536    0,2784      0,0206      ***
AnsQ            0,5771    0,5916      0,5956      n.s.
YAML Syntactic  0,8947    0,8947      0,8947      n.s.
```

*Gunakan bar chart horizontal dengan warna berbeda per sistem. Highlight kolom GraphRAG.*

---

## Slide 10 — Keunggulan RetQ (Klaim 1)

- Δ RetQ vs Vector RAG = **+0,30** (CI [+0,23; +0,37])
- **Path Coverage: 0,85** — sistem berhasil menemukan jalur skema yang relevan
- **Hop Accuracy: 0,35** — traversal multi-hop mencapai node tujuan
- **RGA: 0,45** — konteks KG benar-benar dimanfaatkan LLM

---

## Slide 11 — Ablasi: Validasi Komponen (Klaim 1 & 2)

| Ablasi | Perubahan | Dampak |
|---|---|---|
| A1 no_phase1 | Hapus exact match | RetQ −0,249 *** |
| A2 no_multihop | Seed node only | RetQ −0,601 *** |
| A3 depth=2 | Paksa depth 2 | HopAcc −0,124 *** |
| A4 depth=3 | Paksa depth 3 | ≈0 n.s. |
| A5 no_yaml_layer3 | Hapus validasi KG | ReaQ turun p=0,007 |
| A6c no_multi_entity | Hapus multi-entity | Penurunan kecil |

**Takeaway:** Komponen terpenting = multi-hop traversal (A2). Validasi KG Layer 3 terbukti berkontribusi (A5).

---

## Slide 12 — Boundary Condition

- Unggul di **semua 8 tipe fixture**
- Tertinggi: command +0,671, planning +0,605, followup +0,574
- Terendah: realworld +0,089 (heterogen, masih positif)
- Spearman: degree ρ=+0,467*** → resource kompleks → keunggulan lebih besar
- Spearman: hops ρ=+0,290** → multi-hop → keunggulan lebih besar

---

## Slide 13 — Validasi YAML (Klaim 3)

- **Identitas skor syntactic validity (0,8947)**: ketiga sistem setara
- Kontribusi bukan pada skor, melainkan pada **metode**: validasi tanpa dry-run
- Bukti A5: menghapus Layer 3 → ReaQ turun (p=0,007)
- Praktis: aman untuk lingkungan produksi tanpa akses kluster aktif

---

## Slide 14 — Evaluasi Pakar

- n=4 chatbot evaluator, n=5 fixture validator
- Relevansi jawaban: **4,42/5** ★★★★½
- Kepercayaan trace: **4,50/5** ★★★★½
- Komentar umum: reasoning path yang eksplisit meningkatkan kepercayaan

---

## Slide 15 — Diskusi: Keterbatasan

- KG statis (Swagger 1.29) — tidak otomatis update ke K8s versi baru
- AnsQ tidak berbeda signifikan — kualitas teks bergantung pada LLM, bukan retriever
- Hop Accuracy 0,35 — masih ada ruang peningkatan untuk query multi-hop kompleks
- Realworld Δ terendah (+0,089) — heterogenitas skenario nyata sulit di-cover sepenuhnya
- Satu LLM (GPT-4o-mini) — generalisasi ke model lain perlu studi lanjutan

---

## Slide 16 — Simpulan

**T1:** KG Kubernetes berhasil dibangun via 5-fase pipeline, 18 jenis edge semantik.
**T2:** Retriever adaptif intent-aware (depth 2/3) + multi-entity + 2-fase (exact+vector) terbukti efektif.
**T3:** GraphRAG unggul signifikan di RetQ (+0,30, p<0,001) dan ReaQ vs kedua baseline. AnsQ setara (n.s.).

Kontribusi utama: sistem *end-to-end* GraphRAG Kubernetes dengan validasi YAML berbasis KG tanpa dry-run pada kluster aktif.

---

## Slide 17 — Saran untuk Penelitian Lanjutan

- KG dinamis: sinkronisasi otomatis dengan CRD dan versi K8s terbaru
- Multi-LLM evaluation: uji dengan Llama 3, Claude, Gemini
- Peningkatan Hop Accuracy untuk query dengan 4+ hop
- Deployment production dengan monitoring dan feedback loop
- Generalisasi ke domain IaC lain (Terraform, Helm)

---

## Slide 18 — Terima Kasih / Q&A

- GitHub: [link repositori]
- Live demo: [link HF Spaces]
- Kontak: jihanaurelia.jiji@gmail.com

---

**Tips presentasi:**
- Slide 9 (hasil utama) adalah pusat argumen — pastikan jelas dan mudah dibaca
- Siapkan pointer ke Tabel 31, 32, 33, 34 di dokumen TA untuk backup detail
- Klaim 3 (YAML) kemungkinan akan ditanya — gunakan jawaban Q8 dari anticipated_questions.md
