# Pemetaan Slide PPT Sidang → Halaman Laporan TA

Sumber slide: `18222001-JIHAN AURELIA-SlideTA.pdf` (21 slide)
Sumber laporan: `docs/18222001-JIHAN AURELIA-LaporanTA.pdf` (190 hal. fisik / 162 hal. cetak)

Konvensi nomor halaman: **cetak (PDF)**. Offset tetap: **PDF = halaman cetak + 28**
(front matter romawi i–xxviii = PDF 1–28; halaman cetak 1 = PDF 29; halaman cetak 162 = PDF 190).

Pemetaan diturunkan dari `TA.toc` / `TA.lof` / `TA.lot` (artefak build LaTeX, byte-identical dengan
PDF laporan) dan diverifikasi ulang dengan ekstraksi teks langsung dari PDF per halaman.

---

## Slide 1 — Sampul

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Judul TA, nama, NIM 18222001 | Halaman Judul | iii (PDF 3) |
| Dr. Ir. Dimitri Mahayana, M.Eng. (Pembimbing) | Lembar Pengesahan | iii (PDF 3) |
| Prof. Dr. Ir. Jaka Sembiring, M.Eng. (Penguji 1) | Lembar Pengesahan | iii (PDF 3) |
| Dion Tanjung, S.Kom., M.Sc., Ph.D. (Penguji 2) | Lembar Pengesahan | iii (PDF 3) |
| Tanggal "Selasa, 28 Juli 2026" | ⚠ tidak ada di laporan (tanggal sidang, bukan tanggal cetak) | — |

## Slide 2 — Latar Belakang

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| ">95% workload cloud-native" (Gartner 2021) | Bab I.1 Latar Belakang, paragraf 1 | 1 (PDF 29) |
| "84% pakai Kubernetes" (CNCF 2023) | Bab I.1, paragraf 1 (66% produksi + 18% evaluasi) | 1 (PDF 29) |
| Kompleksitas / Risiko Operasional / Inefisiensi Waktu | B01–B03 Business Understanding | 25–26 (PDF 53–54) |
| "Rahman dkk. (2023)" ~80% miskonfigurasi struktural | Bab I.1 & II.5.2 & III.1.1 | 2, 18, 26 (PDF 30, 46, 54) |
| Logo Botkube, K8sGPT, kubectl-ai, Kubeval | ⚠ **tidak ditemukan** di laporan manapun | — |
| "Limitasi Solusi: gagal memvalidasi relasi antar objek" | Padanan terdekat: Tabel III.1 Technical Gap Analysis | 31–33 (PDF 59–61) |

## Slide 3 — Metodologi & Rumusan Masalah

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Rumusan Masalah 1 (bangun KG) | Bab I.2, poin 1 | 4 (PDF 32) |
| Rumusan Masalah 2 (retriever intent) | Bab I.2, poin 2 | 4 (PDF 32) |
| Rumusan Masalah 3 (kinerja vs LLM/Vector) | Bab I.2, poin 3 | 4 (PDF 32) |
| Tujuan (3 poin, korespondensi 1:1) | Bab I.3 | 4 (PDF 32) |
| 6 tahap CRISP-DM | Bab I.5 Metodologi | 5 (PDF 33) |
| Gambar tahapan CRISP-DM | Gambar I.1 | 6 (PDF 34) |
| "Niaksu" sitasi | Niakšu (2015), sama seperti di atas | 5–6 (PDF 33–34) |

## Slide 4 — Arsitektur Kubernetes & Manifes

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Diagram Cluster Architecture (Master/Node) | Gambar II.1 | 10 (PDF 38) |
| Contoh YAML nested Deployment+Secret+ConfigMap | Subbab II.2.3 Manifes YAML & IaC | 12 (PDF 40) |
| "IaC deklaratif" & "cross-resource reference" | II.2.3 + III.1.2.4 (Listing III.1–III.6) | 12, 29–31 (PDF 40, 57–59) |

## Slide 5 — LLM, RAG, GraphRAG

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Definisi LLM ("kurang akurat topik teknis") | Subbab II.3.1 | 12–13 (PDF 40–41) |
| RAG: Indexing→Retrieval→Augmentasi (Gao dkk. 2024) | Subbab II.4.1 | 13–14 (PDF 41–42) |
| Definisi Knowledge Graph + triples (Hofer dkk. 2024) | Subbab II.5.1 | 16–17 (PDF 44–45) |
| Gambar Arsitektur Knowledge Graph (Yu 2021) | Gambar II.2 | 16 (PDF 44) |
| Taksonomi pembangunan KG (Abusalih 2021) | Gambar II.3 | 17 (PDF 45) |
| GraphRAG: integrasi KG + LLM (Wan dkk. 2025) | Subbab II.5.2 | 18–19 (PDF 46–47) |

## Slide 6 — Business & Data Understanding

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| B01/B02/B03 | Subbab III.1.1 | 25–26 (PDF 53–54) |
| x-kubernetes-group-version-kind / PodSpec | Subbab III.1.2.2 Struktur Dokumen | 27–28 (PDF 55–56) |
| Referensi Objek (`$ref`) | Listing III.1–III.2 | 30 (PDF 58) |
| Referensi Daftar (array `items`) | Listing III.3–III.4 | 30 (PDF 58) |
| Referensi Map (`additionalProperties`) | Listing III.5–III.6 | 30–31 (PDF 58–59) |

## Slide 7 — Kebutuhan Fungsional & Non-Fungsional

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| B01→T01/T03→F01/F02/F03/F04/F05 | Tabel III.2 | 33 (PDF 61) |
| B02→T02/T04→F07/F01 | Tabel III.2 | 33 (PDF 61) |
| B03→T05→F06/F07 | Tabel III.2 | 33 (PDF 61) |
| Rincian F-01…F-07 | Tabel III.3 Kebutuhan Fungsional | 34–35 (PDF 62–63) |
| NF01 Fail-Safe / NF02 Latency / NF03 CLI Usability / NF04 Resource Constraints | Tabel III.4 — ⚠ nama beda: laporan pakai **NF-03 Web UI Usability Standard** & **NF-04 Public Accessibility**, bukan "CLI"/"Resource Constraints" | 36 (PDF 64) |
| "F-06 Website Interaction" | ⚠ laporan: **F-06 Web Interaction Interface** | 33 (PDF 61) |

## Slide 8 — Arsitektur & Siklus Hidup Sistem

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Diagram siklus CRISP-DM melingkar | Gambar IV.1 Rancangan solusi CRISP-DM | 43 (PDF 71) |
| Pemetaan tiap tahap ke kebutuhan sistem | Tabel IV.1 + Subbab IV.2 | 44–47 (PDF 72–75) |
| Label "1. Ingestion Deterministik" | IV.3.1 Perancangan Pipeline Ingestion | 48 (PDF 76) |
| Label "2. GraphRAG Core" | IV.4 Perancangan Mekanisme GraphRAG | 49–52 (PDF 77–80) |
| Label "3. Evaluasi & Validasi" | Bab VI + IV.4.3 | 52, 81 (PDF 80, 109) |
| "Deployment: Streamlit CLI" | ⚠ laporan selalu menyebut antarmuka **web** Streamlit (IV.4.4/V.3.4), bukan CLI | 52, 76 (PDF 80, 104) |

## Slide 9 — Objective 1: Konstruksi KG Deterministik

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| "Node Creation (Fase 1)" | Subbab V.2.1 + Gambar V.2 | 59–60 (PDF 87–88) |
| "Edge Creation (Fase 2-3)" | Subbab V.2.2 + Gambar V.3–V.5 | 60–64 (PDF 88–92) |
| "Embedding Generation (Fase 4)" | ⚠ laporan menyebutnya **Fase 1.5** (dieksekusi setelah Fase 1, sebelum edge), bukan Fase 4 — Subbab V.2.3 + Gambar V.6 | 65–66 (PDF 93–94) |
| "Neo4J Indexing (Fase 5)" | ⚠ laporan tidak menomori langkah ini sebagai "Fase 5" — indeks dijelaskan menyatu di V.2.3 | 66 (PDF 94) |
| "725 Total Nodes" | Tabel V.4 Statistik KG + hal. 60 (183 root + 542 sub) | 60, 67 (PDF 88, 95) |
| "24,9% root / 75,1% sub-resource" + Gambar donat | ⚠ persentase ini dihitung dari **730 definisi** (bukan 725 node) — Gambar III.1 + hal. 28 | 28–29 (PDF 56–57) |
| "18 Tipe Edge" | Tabel V.4 | 67 (PDF 95) |
| "4 edge struktural / 14 edge operasional" | Subbab V.2.2, hal. 63–64 (Gambar V.4) | 63–64 (PDF 91–92) |
| "Takeaway: deterministik vs stokastik LLM" | Kontribusi Penelitian di Bab I.3 / VII.1 | 3, 109 (PDF 31, 137) |

## Slide 10 — Properti Node

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Contoh JSON node (id, name, fullName, kind, is_root, scope, description, source, embedding) | Listing A.2 Representasi Node dan Relationship | 118–119 (PDF 146–147) |
| "description_length", "was_truncated", batas 4000 karakter | ⚠ **tidak ditemukan** di laporan (properti ini tidak dijelaskan eksplisit di teks maupun listing) | — |
| Gambar placeholder (kotak silang) | ⚠ artefak kosong di slide, bukan bagian laporan | — |

## Slide 11 — Objective 2: LangGraph Agents

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Diagram Zona Konstruksi (Offline) / Zona Kueri (Runtime) | Gambar IV.2 Architecture Diagram / Gambar V.1 | 47, 58 (PDF 75, 86) |
| Memory / Thinker / Retriever / Speaker / Saver | Tabel V.5 Lima Modul Agent + Gambar V.7 | 68–69 (PDF 96–97) |
| Definisi & contoh 5 intent (Explain, Generate yaml, Trace Relationship, Followup, Planning) | Tabel V.6 Definisi Tipe Intent | 70 (PDF 98) |

## Slide 12 — Hybrid Retriever & Validasi YAML

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Langkah 1 Exact Match / 2 Vector Similarity / 3 Multi-Hop | Subbab IV.4.2 + Gambar V.8 (cascading retrieval 3 tahap) | 50–51, 71 (PDF 78–79, 99) |
| "Output: Reasoning path" | Listing V.2 contoh graph_context/reasoning_path | 74 (PDF 102) |
| d=2 default / d=3 yaml_gen & planning | Tabel V.7 Pemetaan Intent→Kedalaman + Listing DEPTH_BY_INTENT | 72 (PDF 100) |
| Top Layer: Graph Diagram (dry-run) | Tabel IV.4 Fungsi Tiga Lapis Validasi | 52 (PDF 80) |
| Middle Layer: kubernetes-validate | Tabel IV.4 + Gambar V.12 | 52, 77 (PDF 80, 105) |
| Bottom Layer: yaml.safe_load | Tabel IV.4 | 52 (PDF 80) |
| "OpenAPI K8s v1.3" | ⚠ typo — laporan konsisten pakai **v1.30** | 27, 52 (PDF 55, 80) |
| Template Cypher (exact match, multi-hop, vektor, required field) | Lampiran B | 121–124 (PDF 149–152) |

## Slide 13 — Tampilan Chatbot

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Tampilan Awal / Jawaban Manifest YAML / Jawaban Teks (screenshot) | ⚠ **tidak ada screenshot** di laporan — hanya deskripsi tekstual di V.3.4 | 76–78 (PDF 104–106) |
| UC "Generate a Kubernetes Deployment YAML..." | Gambar IV.4 Use Case Diagram (UC04) | 53 (PDF 81) |

## Slide 14 — Graph Visualization & Edge Table

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Graph Visualization / Edge Table / Sumber Referensi / Keterangan Warna (screenshot 4 tab) | ⚠ **tidak ada screenshot** — dideskripsikan sebagai 4 tab Retrieval Trace Expander di V.3.4 | 77 (PDF 105) |
| "Root Resource, API Version, Nodes, Unique Edges, Max Depth" | Deskripsi baris metrik komponen expander, V.3.4 | 74, 77 (PDF 102, 105) |

## Slide 15 — Evolusi Rancangan & Matriks Komparasi

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Diagram Vanilla LLM → Vector RAG → GraphRAG | Gambar IV.6 | 55 (PDF 83) |
| Tabel: Metode Retrieval / Sumber Konteks / Kedalaman Traversal | Tabel IV.5 Perbandingan Komponen Teknis | 56 (PDF 84) |
| "Key Insights: relational traceability & schema traversal" | Subbab IV.5.4, paragraf penutup | 56 (PDF 84) |
| Diagram alur eksekusi 3 sistem berdampingan | Gambar V.13 | 78 (PDF 106) |

## Slide 16 — Matriks Evaluasi (AnsQ/RetQ/ReaQ)

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Answer Semantic Similarity (kosinus embedding) | Subbab II.6.1 poin 1, Persamaan II.2 | 20 (PDF 48) |
| Syntactic Validity | Subbab II.6.1 poin 2, Persamaan II.3 | 20 (PDF 48) |
| Schema Compliance | Subbab II.6.1 poin 3, Persamaan II.4 | 20 (PDF 48) |
| Precision@k / Recall@k | Subbab II.6.2, Persamaan II.5 | 20–21 (PDF 48–49) |
| F1-Score@k | Subbab II.6.2, Persamaan II.6 | 21 (PDF 49) |
| Hop-Tracing (edge recall) | Subbab II.6.3 poin 1, Persamaan II.7 | 21 (PDF 49) |
| Faithfulness (Es dkk. 2023) | Subbab II.6.3 poin 2 | 21–22 (PDF 49–50) |
| Pemetaan B01-B03 → dimensi evaluasi | Tabel III.5 | 37 (PDF 65) |
| Protokol eksperimen (3 mode, 102 fixture, GPT-4o-mini) | Subbab VI.1.2–VI.1.3 | 83–84 (PDF 111–112) |

## Slide 17 — Hasil Evaluasi

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| AnsQ: GraphRAG 0,803 / Vector RAG 0,798 / Vanilla LLM 0,747 | Tabel VI.3 (nilai presisi: 0,8031/0,7984/0,7469) + VI.3.1 | 85, 92 (PDF 113, 120) |
| "100% Validitas Sintaksis vs 83%" | Tabel VI.3, baris Syntactic Validity (0,8333 Vanilla LLM) | 85 (PDF 113) |
| RetQ bar chart 0,7089/0,2437/0,000, Δ+0,465 (p<0,001) | Tabel VI.5 + Subbab VI.2.2 | 87–88 (PDF 115–116) |
| Precision 0,8405 / Recall 0,7258 | Tabel VI.5 | 88 (PDF 116) |
| Gauge Hop Accuracy 90,86% (fokus ≤15 edge), keseluruhan 75,62% | Tabel VI.6 Hop Accuracy Terstratifikasi | 89 (PDF 117) |
| Faithfulness GraphRAG 0,3055 vs Vector RAG 0,1675 | Tabel VI.7 | 90 (PDF 118) |
| Gambar batang perbandingan AnsQ/RetQ/HopAcc/Faithfulness | Gambar VI.1 | 84 (PDF 112) |
| Precision/Recall/F1 chart | Gambar VI.3 | 88 (PDF 116) |
| "Kesimpulan Evaluasi" narasi penutup slide | Subbab VI.3.7 & VII.1 | 101, 109 (PDF 129, 137) |

## Slide 18 — Analisis Ablasi

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| A2 no_multihop: −0,656 (Paling Krusial) | Tabel VI.12 + Subbab VI.3.6 narasi | 98–99 (PDF 126–127) |
| A1 no_phase1 (exact match): −0,309 | Tabel VI.12 + VI.3.6 | 98–99 (PDF 126–127) |
| A7 HAS_PROPERTY only: −0,152 | Tabel VI.12/VI.14 + Gambar VI.9 | 98, 100 (PDF 126, 128) |
| A3 depth=2 fixed: −0,123 | Tabel VI.12 + VI.3.6 | 98–99 (PDF 126–127) |
| A5 no_yaml_layer3: −0,057 | Tabel VI.12 + VI.3.6 | 98–99 (PDF 126–127) |
| "A4 & A6 tidak signifikan" | Tabel VI.13 Signifikansi Statistik (p=0,071–1,000) | 99 (PDF 127) |
| "Zona Optimal" (kueri relasional kompleks, konektivitas tinggi ρ=+0,245) | Subbab VI.3.8 + Tabel VI.17 | 102, 105 (PDF 130, 133) |
| "Boundary Conditions" (kueri konseptual terisolasi, konektivitas rendah) | Subbab VI.3.8, hal. 105–106 | 105–106 (PDF 133–134) |
| "Analytical Synthesis" penutup | Subbab VI.3.6/VI.3.8 sintesis | 99, 105 (PDF 127, 133) |

## Slide 19 — Validasi Pakar

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| 5 profil validator (nama, ID E.1–E.5) | Tabel F.1 Peran Lima Pakar | 157 (PDF 185) |
| Afiliasi perusahaan (Sharing Vision, GDP Labs, Accenture), lama pengalaman K8s per orang | ⚠ **tidak ada di laporan** — Tabel VI.1 pakai kode anonim N1–N3 (peran + pengalaman umum), Tabel F.1 hanya nama tanpa perusahaan | 82, 157 (PDF 110, 185) |
| Lembar tanda tangan validator (5 lembar) | Lampiran F.1–F.5 | 158–162 (PDF 186–190) |
| Realisme skenario uji: 3,87 | Tabel VI.2 Rata-rata Keseluruhan | 82 (PDF 110) |
| Relevansi 4,42 / Akurasi Teknis 4,08 / Kelengkapan 3,83 / Usability 3,92 | Tabel VI.18 kolom Rata-rata | 107 (PDF 135) |
| "Average 4,50/5,00" | ⚠ **salah kutip** — 4,50 di laporan adalah skor *Peningkatan kepercayaan* terhadap Retrieval Trace, bukan rata-rata 4 dimensi (rata-rata 4 dimensi ≈ 4,06) | 107 (PDF 135) |
| "Retrieval Trace membantu... rujukan skema" | Subbab VI.4 poin 2, hal. 107 | 107 (PDF 135) |
| "Skenario operasional 4,67/5,00" | Tabel VI.2, baris cronjob_backup/networkpolicy_deny_all/statefulset_with_pvc | 82 (PDF 110) |

## Slide 20 — Pemetaan Struktural (Kesimpulan)

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| RQ1 → Pipeline Ekstraksi Deterministik → 725 node/18 edge/7 kategori | VII.1 Kesimpulan poin 1 | 109 (PDF 137) |
| RQ2 → Mekanisme Ganda (Intent-Adaptive Depth + KG-Grounded Validation) → traversal optimal | VII.1 poin 2 | 109–110 (PDF 137–138) |
| RQ3 → Evaluasi Komparatif 102 fixture 8 kategori → RetQ +0,465, Hop Acc 0,908 | VII.1 poin 3 + VI.1.1 | 81, 110 (PDF 109, 138) |

## Slide 21 — Penutup

| Elemen di Slide | Lokasi di Laporan | Hal. |
|---|---|---|
| Nama, Pembimbing, 1 Penguji | Lembar Pengesahan | iii (PDF 3) |
| Tanggal "Kamis, 18 Desember 2025" | ⚠ **bertentangan** dengan tanggal sampul slide 1 ("Selasa, 28 Juli 2026") dan hanya mencantumkan 1 penguji vs 2 di sampul — murni isu draf slide, bukan isu laporan | — |

---

## Catatan Ketidaksesuaian (rangkuman untuk antisipasi sidang)

1. **Botkube/K8sGPT/kubectl-ai/Kubeval (S2)** — nama-nama tools ini tidak muncul sama sekali di laporan; hanya ada di slide.
2. **NF/F penamaan (S7)** — "NF03 CLI Usability"/"NF04 Resource Constraints" di slide vs "NF-03 Web UI Usability Standard"/"NF-04 Public Accessibility" di Tabel III.4 (hal. 36).
3. **"Streamlit CLI" (S8)** — laporan selalu bilang antarmuka **web**, bukan CLI.
4. **Penomoran fase ingestion (S9)** — slide pakai "Fase 4 Embedding"/"Fase 5 Indexing"; laporan pakai **Fase 1.5** untuk embedding, dan tidak menomori indexing sebagai fase terpisah.
5. **725 vs 730 (S9)** — persentase 24,9%/75,1% dihitung dari 730 definisi skema, bukan dari 725 node graf (725 = 183 root + 542 sub, setelah proses lanjutan).
6. **description_length/was_truncated/4000 karakter (S10)** — tidak ditemukan di teks laporan manapun.
7. **"5 Sesi Terakhir" (S11)** — laporan bilang 5 **giliran percakapan** (turns), bukan 5 sesi.
8. **"OpenAPI K8s v1.3" (S12)** — typo, seharusnya v1.30.
9. **Screenshot UI (S13–S14)** — laporan sama sekali tidak memuat screenshot; hanya deskripsi tekstual.
10. **Afiliasi perusahaan validator (S19)** — Sharing Vision/GDP Labs/Accenture tidak ada di laporan; Tabel VI.1 anonim (N1–N3), Tabel F.1 hanya nama.
11. **"Average 4,50/5,00" (S19)** — ini paling berisiko ditanya penguji: 4,50 sebenarnya skor kepercayaan terhadap Retrieval Trace, bukan rata-rata 4 dimensi kualitatif (yang sebenarnya ≈4,06).
12. **Pembulatan angka (S17)** — slide membulatkan 4 desimal jadi 3 (0,7469→0,747); "83%" merujuk ke Syntactic Validity Vanilla LLM, bukan metrik umum.
13. **Tanggal & jumlah penguji (S21)** — slide penutup tidak sinkron dengan slide sampul (S1).
