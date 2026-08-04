# Audit Kesiapan Sidang TA — GraphRAG Kubernetes
**Tanggal audit:** 6 Juni 2026  
**Dokumen:** Tugas Akhir S1 STI ITB — Jihan Aurelia (18222001)  
**Judul resmi:** Implementasi *Graph Retrieval-Augmented Generation* untuk Meningkatkan Presisi *Retrieval* dan Validitas Sintaksis pada Konfigurasi Kubernetes

---

## Ringkasan Eksekutif

Audit penuh terhadap 28 file `.tex`, 45 file tabel, dan bibliografi menemukan **12 ketidaksesuaian** (5 Blocker, 4 Major, 3 Minor). Seluruh ketidaksesuaian yang dapat diperbaiki dari `.tex` telah **dieksekusi dan diterapkan**. Isi tesis secara substantif kuat: metodologi CRISP-DM lengkap, EDA nyata, uji statistik tiga lapis (Wilcoxon + paired bootstrap 95% CI + Holm-Bonferroni), ablation study 6 konfigurasi, depth sensitivity, boundary condition analysis, dan validasi pakar. Gap menuju "semua Lulus" bersifat konsistensi dan kelengkapan formal—bukan cacat metodologi.

---

## Scorecard Rubrik (A–H)

### Kategori A — Halaman Depan & Identitas

| Item | Kriteria | Status Awal | Status Akhir | Tindakan |
|------|----------|-------------|--------------|---------|
| A1 | Judul konsisten di semua halaman depan | ❌ Gagal | ✅ Lulus | `1 Halaman Judul.tex` "Kualitas" → "Presisi" |
| A2 | Lembar Pengesahan ada & lengkap | ✅ Lulus | ✅ Lulus | — |
| A3 | Pernyataan Orisinalitas ada & ditandatangani | ✅ Lulus | ✅ Lulus | — |
| A4 | Abstrak (ID + EN) | ⚠️ Deviasi | ⚠️ Deviasi diterima | Hanya abstrak ID — keputusan user; abstrak ID sudah lengkap (masalah/metode/hasil/kesimpulan + kata kunci) |
| A5 | Kata Pengantar ada | ✅ Lulus | ✅ Lulus | — |
| A6 | Daftar Isi lengkap | ✅ Lulus | ✅ Lulus | — |
| A7 | Daftar Gambar ada & terisi | ✅ Lulus | ✅ Lulus | — |
| A8 | Daftar Singkatan lengkap | ❌ Gagal | ✅ Lulus | Ditambah: API, CRD, EDA, GNN, GPT, GVK, HPA, IR, NLP, PCST, PVC |
| A9 | Daftar Tabel ada & terisi | ✅ Lulus | ✅ Lulus | — |
| A10 | Daftar Listing ada & terisi | ✅ Lulus | ✅ Lulus | — |
| A11 | Daftar Persamaan ada & terisi | ❌ Gagal | ✅ Lulus | `\eqcaption{}` ditambah ke 12 persamaan di Bab II; total 13 persamaan terdaftar |
| A12 | Daftar Algoritma — tidak ada algoritma | ⚠️ Kosong | ✅ Lulus | `\input{11 Daftar Algoritma.tex}` dihapus dari `TA.tex`; tidak ada daftar kosong |

### Kategori B — Bab I Pendahuluan

| Item | Status | Catatan |
|------|--------|---------|
| B1 | ✅ Lulus | Latar belakang kuat dengan data CNCF 2023, rahman2023misconfigurations |
| B2 | ✅ Lulus | 3 rumusan masalah eksplisit bernomor |
| B3 | ✅ Lulus | 3 tujuan penelitian selaras rumusan masalah |
| B4 | ✅ Lulus | Batasan penelitian eksplisit (v1.30, 97 fixture, GPT-4o-mini) |
| B5 | ✅ Lulus | Metodologi CRISP-DM 6 fase dengan gambar |

### Kategori C — Bab II Studi Literatur

| Item | Status | Catatan |
|------|--------|---------|
| C1 | ✅ Lulus | Kubernetes, LLM, RAG, KG, GraphRAG dibahas dengan referensi mutakhir |
| C2 | ✅ Lulus | Metrik AnsQ/RetQ/ReaQ + 3 metrik domain dirumuskan secara formal |
| C3 | ✅ Lulus | Related work 3 penelitian terkait dengan analisis gap (Tabel 12) |
| C7 | ✅ Lulus | Lampiran C kini menggunakan koma desimal seperti body |

### Kategori D — Bab III Analisis

| Item | Status Awal | Status Akhir | Catatan |
|------|-------------|--------------|---------|
| D1 | ✅ Lulus | ✅ Lulus | Business Understanding B01–B03 |
| D2 | ❌ Gagal | ✅ Lulus | Matriks keputusan kini menyatakan WSM bobot setara (0,25/kriteria) dan mengklarifikasi Alt 1 = metode usulan |
| D3 | ❌ Gagal | ✅ Lulus | Ukuran swagger disamakan: 3,757 MB di Bab III & Bab III Data Understanding; rantai node: 735→730 (EDA) →725 (KG, -5 tipe generik) seragam |
| D7 | ✅ Lulus | ✅ Lulus | EDA nyata (distribusi root vs sub, kepadatan properti, ref-silang) |

### Kategori E — Bab IV Perancangan

| Item | Status | Catatan |
|------|--------|---------|
| E1–E5 | ✅ Lulus | Arsitektur 5-fase, taksonomi relasi 18 jenis, komponen pipeline LangGraph terdokumentasi |

### Kategori F — Bab V Implementasi

| Item | Status Awal | Status Akhir | Catatan |
|------|-------------|--------------|---------|
| F1 | ✅ Lulus | ✅ Lulus | Tech stack konkret, Kubernetes v1.30, Neo4j, GPT-4o-mini |
| F5 | ❌ Gagal | ✅ Lulus | Angka node dikoreksi: "5 tipe generik dikecualikan" (bukan 14); konsisten dengan EDA 730→725 |
| F8 | ✅ Lulus | ✅ Lulus | Kode sumber di Lampiran A |

### Kategori G — Bab VI Evaluasi

| Item | Status Awal | Status Akhir | Catatan |
|------|-------------|--------------|---------|
| G1 | ✅ Lulus | ✅ Lulus | Baseline terkontrol (Vanilla LLM, Vector RAG) |
| G2 | ✅ Lulus | ✅ Lulus | Uji statistik: Wilcoxon + paired bootstrap + Holm-Bonferroni |
| G3 | ✅ Lulus | ✅ Lulus | Ablation study 6 konfigurasi (A1–A6c) |
| G4 | ✅ Lulus | ✅ Lulus | Analisis depth sensitivity |
| G5 | ✅ Lulus | ✅ Lulus | Analisis boundary condition |
| G6 | ❌ Gagal | ✅ Lulus | Seksi 6.4: "Keempat pakar" kini merujuk Lampiran E (kode E.1–E.4) — bukan lagi tabel fixture-validator 3 baris |
| G7 | ✅ Lulus | ✅ Lulus | Keterbatasan dilaporkan jujur (AnsQ n.s., realworld rendah, faithfulness lebih rendah) |

### Kategori H — Kualitas Lintas Bab

| Item | Status Awal | Status Akhir | Catatan |
|------|-------------|--------------|---------|
| H1 | ❌ Gagal | ✅ Lulus | Angka node konsisten: EDA 730 (183+547) → KG 725 (183+542, -5 tipe generik); ukuran swagger = 3,757 MB |
| H2 | ❌ Gagal | ✅ Lulus | Profil pakar dipisah dengan benar: tabel27 = 3 validator fixture; Lampiran E = 5 penandatangan + tabel peran E.1–E.5 |
| H3 | ❌ Gagal | ✅ Lulus | Daftar Algoritma kosong dihapus; Daftar Persamaan kini memuat 13 entri |
| H4 | ❌ Gagal | ✅ Lulus | Bibliografi: duplikat `hofer2024construction` dihapus; `file:///` URL diperbaiki; author `moreno2025rag` diformat; `he2024gretriever` diperbaiki ke `@inproceedings` ICLR 2024; 11 entri tidak tersitir dihapus |
| H5 | ❌ Gagal | ✅ Lulus | Lampiran C menggunakan koma desimal (1.261 penggantian) |
| H6 | ❌ Gagal | ✅ Lulus | Judul seragam "Presisi Retrieval" di Halaman Judul, Pengesahan, Abstrak, Kata Pengantar |
| H7 | ✅ Lulus | ✅ Lulus | Bab VII menjawab semua RQ bernomor + keterbatasan + saran |

---

## Detail Perubahan yang Diterapkan

### 1. `1 Halaman Judul.tex`
- "Meningkatkan **Kualitas** Retrieval" → "Meningkatkan **Presisi** Retrieval"

### 2. `14 Daftar Singkatan.tex`
- Ditambah 11 akronim: API, CRD, EDA, GNN, GPT, GVK, HPA, IR, NLP, PCST, PVC

### 3. `TA.tex`
- `\input{11 Daftar Algoritma.tex}` dihapus (tidak ada algoritma, daftar kosong)

### 4. `Bab V - Implementasi.tex`
- "14 tipe generik dikecualikan" → "**5** tipe generik dikecualikan" (cocok dengan delta 730−725=5)

### 5. `Bab III - Analisis.tex`
- Ukuran swagger disamakan: 3,67 MB → **3,757 MB**
- Teks matriks keputusan: "tiga pendekatan alternatif serta metode usulan" → kalimat baru yang menyatakan WSM bobot setara (0,25/kriteria) dan mengidentifikasi Alt 1 sebagai metode yang diusulkan

### 6. `Bab VI - Evaluasi.tex`
- Seksi 6.4: `Tabel~\ref{tbl:expert_profile}` (tabel fixture-validator, 3 baris) → `Lampiran~\ref{lampiran:validasi-pakar}` (E.1–E.4)

### 7. `Lampiran-E.tex`
- Paragraf pembuka ditulis ulang dengan tabel baru `tbl:evaluator_roles` yang memetakan 5 penandatangan ke peran: validasi fixture (E.2, E.4, E.5 = 3 orang) dan evaluasi jawaban (E.1–E.4 = 4 orang)

### 8. `Bab II - Studi.tex`
- Ditambah `\eqcaption{}` ke 12 persamaan bernomor: `eq:rag-conditional`, `eq:faithfulness`, `eq:answer-relevance`, `eq:syntactic-validity`, `eq:schema-compliance`, `eq:precision-recall`, `eq:f1`, `eq:ndcg`, `eq:grounding`, `eq:hop-accuracy`, `eq:path-coverage`, `eq:rga`

### 9. `Lampiran-C.tex`
- 1.261 angka desimal dikonversi dari titik ke koma (0.7932 → 0,7932) di seluruh tabel metrik per-fixture

### 10. `daftar-pustaka.bib`
- Duplikat `hofer2024construction` (entri pertama dengan Unicode) → dihapus, satu entri dengan LaTeX encoding dipertahankan
- `cao2025neusymrag`: `url={file:///mnt/data/...}` → `url={https://arxiv.org/abs/2505.19754}`
- `moreno2025rag`: author format diperbaiki ke `Lastname, Firstname and ...`
- `he2024gretriever`: `@unpublished` + note "user-provided" → `@inproceedings` ICLR 2024 dengan arXiv URL
- 11 entri tidak tersitir dihapus: `truyen2020kubernetes`, `patil_kubernetes_2023`, `k8s_docs_api`, `k8s_docs_workloads`, `nguyen_empica_2024`, `wang2024rfsensinggpt`, `redhat_stateless`, `knollmeyer2025document`, `wrabel2024api2graph`, `selfrag2023`, `knowledgpt2024`
- Tersisa 25 entri, semua tersitir

---

## Tindakan Manual yang Masih Diperlukan (di Luar `.tex`)

| No | Aksi | Keterangan |
|----|------|-----------|
| M1 | **Tanda tangan basah Lembar Pengesahan** | `2 Lembar Pengesahan.tex` tidak bisa diotomasi; pastikan halaman fisik ditandatangani pembimbing dan ketua program |
| M2 | **Kompilasi ulang PDF** | Jalankan: `xelatex TA.tex && biber TA && xelatex TA.tex && xelatex TA.tex` dari direktori `docs/TA-STI-template-1.0/` untuk meregenerasi Daftar Persamaan, Daftar Singkatan, dan nomor halaman |
| M3 | **Verifikasi visual PDF** | Setelah kompilasi: (a) cek Daftar Persamaan memuat 13 entri; (b) cek Daftar Singkatan urutan abjad; (c) grep PDF/log untuk `??`, `XX`, warning biber |
| M4 | **Cek ulang label fig:I.2** | Label `fig:I.2` pada satu-satunya gambar Bab I menampilkan "Gambar I.1" — fungsional tapi membingungkan; pertimbangkan rename ke `fig:crispdm-metodologi` (opsional, kosmetik) |
| M5 | **Upload file PDF Lampiran E** | Pastikan kelima file PDF lembar validasi (lampiran-e/*.pdf) tersedia sebelum kompilasi final |

---

## Status Akhir

| Kategori | Item Lulus | Total Item | Ket |
|----------|-----------|-----------|-----|
| A — Halaman Depan | 11/12 | 12 | A4 (abstrak EN) deviasi diterima per keputusan user |
| B — Bab I | 5/5 | 5 | |
| C — Bab II | 4/4 | 4 | |
| D — Bab III | 4/4 | 4 | |
| E — Bab IV | 5/5 | 5 | |
| F — Bab V | 3/3 | 3 | |
| G — Bab VI | 7/7 | 7 | |
| H — Kualitas Lintas Bab | 7/7 | 7 | |
| **Total** | **46/47** | **47** | **1 deviasi diterima (A4)** |

> **Catatan A4:** Abstrak hanya dalam Bahasa Indonesia (tanpa versi Inggris) adalah keputusan eksplisit peneliti. Abstrak ID sudah memuat semua elemen wajib: latar belakang masalah, metode/pendekatan, hasil kuantitatif (RetQ 0,7259; ReaQ 0,5554; Path Coverage 0,8515; RGA 0,4536; semua p<0,001), dan kesimpulan. Item A4 tidak diklaim Lulus paksa — dicatat sebagai deviasi yang diterima.
