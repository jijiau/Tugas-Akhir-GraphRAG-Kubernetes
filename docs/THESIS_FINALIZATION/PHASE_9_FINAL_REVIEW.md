# Phase 9 — Final Pre-Sidang Review + Sidang Companion

**Status:** PENDING  
**Prasyarat:** Phase 1–8 semua selesai  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — tabel konsistensi & pertanyaan penguji berubah

Final review perlu memeriksa struktur **tujuan baru** (T1/T2/T3) dan **tidak ada angka lama** di dokumen.

Perubahan utama dari plan lama:
1. Tabel B1 pemetaan: T1→Bab IV/V, T2→Bab IV/V (validasi YAML termasuk), **T3→Bab VI**.
2. Tabel B2 angka: **semua angka = TBD dari re-run**; baru diisi setelah `evaluate.py` final dijalankan untuk 3 sistem.
3. Tidak ada `eq:total_score`, bobot, atau skor Total di seluruh dokumen.
4. Tambah pertanyaan penguji baru (lihat bagian C5 di bawah).

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH** (hanya di-compile)
- Compile sequence: `xelatex TA.tex → biber TA → xelatex TA.tex → xelatex TA.tex`
- Tidak ada perubahan konten di phase ini — hanya review, fix minor, dan materials sidang

---

## Konteks Phase 9

Phase terakhir. Berperan sebagai dosen penguji. Tujuannya:
1. **Verifikasi compilation** — TA.pdf bersih tanpa error
2. **Konsistensi struktural** — 3 Tujuan ↔ 3 Bab IV ↔ 3 Bab V ↔ 3 Kesimpulan VII
3. **Mock review dosen penguji** — identifikasi semua pertanyaan yang mungkin ditanyakan
4. **Sidang companion materials** — slide skeleton, cheatsheet, anticipated questions

---

## A. Compilation Test

### Sequence Compile (Jalankan di terminal PowerShell)

```powershell
cd "c:\Users\Jihan Aurelia\Documents\SMT8\Tugas-Akhir-GraphRAG-Kubernetes\docs\TA-STI-template-1.0"

# Pass 1: Generate aux files
xelatex -interaction=nonstopmode TA.tex

# Pass 2: Resolve bibliography
biber TA

# Pass 3: Resolve cross-references
xelatex -interaction=nonstopmode TA.tex

# Pass 4: Final (resolve all)
xelatex -interaction=nonstopmode TA.tex
```

### Error yang Harus Nol

- `! LaTeX Error` — error fatal
- `LaTeX Warning: Reference ... undefined` — \ref{} tidak punya \label{}
- `LaTeX Warning: Citation ... undefined` — \cite{} tidak punya entry .bib
- `Package biblatex Warning: ... undefined` — citekey hilang
- `Error! Bookmark not defined` — di PDF output (hyperref issue)
- `Overfull \hbox` — lebih dari 5pt overfull tidak boleh ada

---

## B. Checklist Konsistensi Struktural

### B1: 3 Tujuan ↔ Bab IV/V/VI ↔ 3 Kesimpulan VII (REVISI)

| Posisi | T1 | T2 | T3 |
|--------|----|----|-----|
| Bab I Tujuan | Membangun KG dari OpenAPI | Mengembangkan sistem GraphRAG (*intent-adaptive* + validasi YAML) | **Membandingkan** kinerja GraphRAG vs Vector RAG vs Vanilla LLM |
| Bab IV Section | 4.3 KG Construction | 4.4 GraphRAG Pipeline + 4.5 YAML Validation | — (tidak ada section di Bab IV) |
| Bab V Section | 5.2 Implementasi KG | 5.3 Implementasi GraphRAG + 5.4 Implementasi YAML | — (tidak ada section di Bab V) |
| Bab VI | Angka Path Coverage | Angka RetQ/Hop Accuracy/validitas YAML | **Seluruh Bab VI = jawaban T3** |
| Bab VII Kesimpulan | Pertama: KG deterministik | Kedua: sistem GraphRAG + validasi YAML | Ketiga: hasil perbandingan per-faktor (TBD) |

### B2: Sinkronisasi Angka Kunci (REVISI)

Angka struktural (tidak berubah) harus **identik** di seluruh dokumen:

| Angka | Nilai | Muncul Di |
|-------|-------|-----------|
| Node KG | 725 | Bab IV, V, VI, VII, Abstrak |
| Edge types | 18 | Bab IV, V, VI, VII, Abstrak |
| Kategori relasi | 7 | Bab IV, V, VI, VII |
| Fixture uji | 97 | Bab VI, VII, Abstrak |
| Versi K8s | v1.30 | Bab III, IV, V, VI |
| Speaker LLM | GPT-4o-mini | Bab IV, V, Abstrak |

Angka evaluasi — **TBD dari re-run `evaluate.py` final** (3 sistem). Tidak ada angka lama (v12/v13/v17):

| Angka | Nilai | Muncul Di |
|-------|-------|-----------|
| RetQ GraphRAG | **TBD** | Bab VI, VII, Abstrak |
| RetQ Vector RAG | **TBD** | Bab VI, VII |
| RetQ Vanilla LLM | **TBD** | Bab VI, VII |
| Path Coverage GraphRAG | **TBD** | Bab VI, VII |
| Hop Accuracy GraphRAG | **TBD** | Bab VI, VII |
| *Syntactic validity* | **TBD** | Bab VI, VII, Abstrak |
| Spearman ρ derajat | **TBD** | Bab VI, VII |
| Delta & 95% CI per faktor | **TBD** | Bab VI, VII |

⚠ Tidak ada "Total" berbobot di tabel manapun.

### B3: Page Count Check

Target: ≤ 150 halaman total (frontmatter + bab + daftar pustaka + lampiran).

Jika > 150 halaman:
1. Identifikasi konten paling panjang yang bisa dipindah ke Lampiran
2. Tabel per-fixture di Bab VI → Lampiran D
3. Kode Python panjang (> 30 baris) → Lampiran A

---

## C. Mock Review Dosen Penguji

Berikut adalah daftar pertanyaan yang kemungkinan besar ditanyakan oleh dosen penguji, beserta arah jawaban yang direkomendasikan.

### C1: Pertanyaan tentang Knowledge Graph (T1)

**Q1:** "Mengapa Anda memilih membangun KG dari swagger.json, bukan dari dokumentasi HTML kubernetes.io?"
> **A:** swagger.json memberikan representasi formal yang machine-readable dan terstruktur. Setiap type reference dapat langsung dikonversi ke edge tanpa interpretasi semantik. Ini menghasilkan KG yang deterministik dan reproducible, berbeda dengan ekstraksi dari HTML yang memerlukan NLP/LLM dan bersifat stokastik (Pan 2024, Wan 2025).

**Q2:** "Bagaimana Anda memastikan KG yang dibangun akurat dan lengkap?"
> **A:** Akurasi dijamin oleh proses deterministik — setiap edge merupakan direct mapping dari referensi tipe dalam skema. Kelengkapan dijamin oleh coverage: 725 dari 739 total definisi (dikecualikan 14 tipe generik seperti ObjectMeta yang tidak representasikan resource utama). Validitas diverifikasi melalui ablation study A1 dan A2 yang menunjukkan kontribusi terukur setiap komponen retrieval.

**Q3:** "Ada 18 jenis edge — apakah semua digunakan secara seimbang? Apakah ada yang terlalu jarang?"
> **A:** Distribusi tidak seimbang karena skema Kubernetes sendiri tidak seimbang (beberapa relasi seperti CONTAINS_PROPERTY lebih sering dari USES_SECRET). Ini adalah representasi yang akurat dari struktur domain. Analisis kondisi batas menunjukkan bahwa resource dengan konektivitas rendah (derajat 2) seperti ConfigMap tidak mendapat manfaat signifikan dari traversal → menunjukkan bahwa distribusi edge sudah merefleksikan kompleksitas domain secara wajar.

### C2: Pertanyaan tentang Mekanisme GraphRAG (T2)

**Q4:** "Mengapa kedalaman maksimal 3? Mengapa tidak lebih dalam?"
> **A:** Analisis sensitivitas kedalaman d∈{1,2,3,4,5} menunjukkan penurunan RetQ mulai d=4 akibat diminishing returns — traversal menjangkau node utilitas generik (Quantity, IntOrString) yang dibagikan oleh 19-136 resource, menurunkan presisi konteks. Precision@k turun monoton dari d=3 ke d=5. Kedalaman 3 adalah titik optimal berdasarkan data empiris.

**Q5:** "Bagaimana intent classifier bekerja? Apakah ada risk misclassification?"
> **A:** Thinker menggunakan GPT-4o-mini dengan temperature=0.0 dan structured output untuk mengklasifikasikan intent ke {explain, followup, generate_yaml, trace_relationship, planning, troubleshooting, command}. Risk misclassification ada, namun dampaknya terbatas: worst case adalah kedalaman 2 untuk query yang seharusnya 3, atau sebaliknya. Ablation A3 (fixed depth 2) menunjukkan dampak worst case ini: RetQ turun 0,0484 poin, yang masih dapat ditoleransi.

**Q6:** "Vector RAG tetap unggul di AnsQ — apakah ini merupakan kelemahan sistem Anda?"
> **A:** Perbedaan AnsQ (−0,0075, tidak signifikan, p=0,390) mencerminkan karakteristik yang dapat dijelaskan: Vector RAG menyediakan konteks lebih ringkas (top-5 + 1-hop) sehingga Speaker tidak "teralihkan" oleh intermediate structural nodes dari traversal yang lebih dalam. Ini adalah trade-off yang disengaja antara konteks yang lebih luas (GraphRAG) vs konteks yang lebih ringkas (Vector RAG). GraphRAG unggul di RetQ (+0,26, p<0,001) dan Total (+0,0878).

### C3: Pertanyaan tentang YAML Validation (T3)

**Q7:** "Lapisan 3 validasi (Neo4j) tidak signifikan di ablation study (A5) — apakah ini berarti kontribusinya tidak ada?"
> **A:** A5 menguji pada level agregat 97 fixture. Hanya 15 fixture yaml_gen yang memicu lapisan 3, sehingga efeknya terdilusi dalam rata-rata. Pada level yaml_gen saja, lapisan 3 memberikan kontribusi terhadap syntactic validity 0,9474. Interpretasi yang tepat: A5 tidak signifikan secara agregat karena cakupan fixture yang kecil, bukan karena lapisan 3 tidak berguna.

**Q8:** "Anda menggunakan kubernetes-validate versi 1.29, sedangkan swagger.json v1.30 — apakah ini konsisten?"
> **A:** Ada minor version mismatch karena keterbatasan library kubernetes-validate yang belum mendukung v1.30 saat penelitian dilakukan. Perbedaan v1.29 vs v1.30 minimal untuk resource utama. Ini adalah keterbatasan yang perlu dicatat dan dapat dimigrasi ke library yang lebih baru dalam pengembangan lanjutan.

### C4: Pertanyaan tentang Evaluasi

**Q9:** "Mengapa menggunakan 97 fixture, bukan benchmark standar seperti KubeBench atau Kubernetes certification exam?"
> **A:** Tidak ada benchmark standar untuk evaluasi GraphRAG pada konfigurasi Kubernetes yang mencakup semua dimensi (AnsQ, RetQ, ReaQ). Dataset 97 fixture dirancang khusus berdasarkan wawancara dengan 3 praktisi DevOps/SRE aktif untuk memastikan relevansi operasional nyata. Validasi pakar memberikan skor realisme tinggi (4,67-5,00) untuk fixture yang paling representatif.

**Q10:** "Vanilla LLM memperoleh ReaQ 0,6313 — mengapa cukup tinggi padahal tidak ada retrieval?"
> **A:** ReaQ untuk Vanilla LLM mendapat skor tinggi pada sub-metrik tertentu secara vakuus: multi_hop_success=1,0 karena tidak ada reasoning path yang bisa gagal, dan grounding_score=0,5975 karena model menyebut istilah K8s dari knowledge bawaan. Ini adalah artifact dari definisi metrik pada baseline tanpa retrieval — bukan berarti kualitasnya tinggi.

**Q11:** "Bagaimana Anda memastikan reproducibility evaluasi dengan LLM yang stokastik?"
> **A:** Thinker menggunakan temperature=0.0 untuk output JSON yang deterministik. Evaluator juga menggunakan temperature rendah. Variasi stokastik diakui: perbandingan v12→v13 menunjukkan RetQ fluktuasi dalam ±0,005 (noise level). Uji signifikansi statistik menggunakan Wilcoxon signed-rank + paired bootstrap 1000 iterasi untuk mengkonfirmasi bahwa perbedaan RetQ +0,26 bukan hasil variasi acak.

### C5-BARU: Pertanyaan tentang Keputusan Metrik & Evaluasi

**Q-A:** "Mengapa Anda menggunakan 'Membandingkan' sebagai Tujuan ke-3? Bukankah Kaprodi melarang evaluasi sebagai tujuan?"
> **A:** Arahan Kaprodi melarang kata "mengevaluasi/menguji". Perbandingan sistematis antar-pendekatan (komparasi) adalah aktivitas riset yang valid sebagai tujuan — menghasilkan temuan empiris tentang faktor-faktor keunggulan sistem yang dibangun. (Siapkan bukti sudah dikonfirmasi pembimbing jika ada.)

**Q-B:** "Mengapa tidak ada satu skor Total yang bisa dibandingkan?"
> **A:** Skor Total berbobot menyembunyikan trade-off antar-dimensi — sistem A bisa lebih baik di RetQ tapi lebih rendah di AnsQ, dan bobot yang dipilih menentukan pemenang secara artifisial. Perbandingan per-faktor lebih informatif dan lebih jujur secara akademis: pengguna domain Kubernetes yang peduli presisi *retrieval* akan mengambil kesimpulan berbeda dari yang peduli kualitas jawaban.

**Q-C:** "Apa itu Path Coverage? Apa bedanya dengan Graph Coverage?"
> **A:** Path Coverage mengukur edge-coverage terhadap *expected path* — berapa proporsi *edge* yang diharapkan berhasil diambil selama *traversal*. Graph Coverage sebelumnya hanya memeriksa source-node tanpa memperhatikan *edge* yang menghubungkannya; sebuah node bisa diambil tanpa relasi yang benar. Path Coverage lebih diskriminatif karena mengikat node dan relasi sekaligus.

**Q-D:** "Mengapa Hop Accuracy dipertahankan sebagai metrik tersendiri?"
> **A:** Hop Accuracy memvalidasi mekanisme *intent-adaptive depth* (T2) secara langsung: apakah sistem memilih kedalaman traversal yang tepat untuk tiap intent. Ini adalah satu-satunya metrik yang memeriksa ketepatan mekanisme adaptif, bukan hanya kualitas keluaran.

**Q-E:** "Mengapa *hallucination rate* dibuang dari ReaQ?"
> **A:** *Hallucination rate* dan *Grounding Score* mengukur hal yang sama dari arah berlawanan (lebih rendah = lebih baik vs lebih tinggi = lebih baik). Menggabungkan keduanya dalam komposit menyebabkan inkonsistensi arah agregasi. Grounding Score dipilih karena orientasinya seragam (lebih tinggi = lebih baik) dan sudah menjadi basis RGA.

**Q-F:** "Bagaimana Anda memastikan baseline Vector RAG dan Vanilla LLM dihitung dengan metrik yang sama?"
> **A:** Ketiga sistem — GraphRAG, Vector RAG, dan Vanilla LLM — di-*rerun* bersamaan menggunakan `evaluate.py` final yang sama. CSV lama (termasuk v17) tidak dipakai karena dihitung dengan formula berbeda.

### C5: Pertanyaan tentang Metodologi & Struktur

**Q12:** "Anda menggunakan CRISP-DM — apakah semua fase CRISP-DM diikuti?"
> **A:** Ya, semua 6 fase: Business Understanding (Bab I-III), Data Understanding + Preparation (Bab III-IV), Modeling (Bab IV-V), Evaluation (Bab VI), Deployment (Bab IV antarmuka Streamlit). Pemetaan lengkap ada di Tabel IV.X (tabel pemetaan metodologi).

**Q13:** "Apa perbedaan utama penelitian ini dengan Wan (2025) yang juga mengusulkan GraphRAG?"
> **A:** Wan (2025) adalah motivasi, bukan sistem yang sama. 3 kontribusi khas penelitian ini: (1) KG deterministik dari OpenAPI formal (bukan NLP-extracted), (2) intent-adaptive depth (Wan tidak adaptive), (3) KG-grounded YAML validation (fitur unik untuk domain konfigurasi). Wan juga tidak spesifik ke domain Kubernetes melainkan domain umum.

---

## D. Sidang Companion Materials

Output files di `docs/sidang/`:

### D1: Slide Skeleton (`docs/sidang/slide_skeleton.md`)

```markdown
# Slide Skeleton TA — GraphRAG Kubernetes

## Slide 1: Title
- Judul TA
- Nama, NIM, Pembimbing, Tanggal Sidang

## Slide 2: Latar Belakang
- Kubernetes sebagai standar de facto (CNCF 2023: 66% produksi)
- Kompleksitas YAML → halusinasi LLM
- Vector RAG tidak cukup: 63,4% exact match
- Visual: YAML snippet + error LLM

## Slide 3: 3 Kontribusi (Preview)
- Klaim 1: Schema-derived deterministic KG
- Klaim 2: Intent-adaptive depth traversal
- Klaim 3: KG-grounded YAML validation
- Visual: diagram overview 3 klaim

## Slide 4: Arsitektur Sistem
- Gambar Architecture.png (Bab IV)
- Highlight 3 komponen utama

## Slide 5: Klaim 1 — Knowledge Graph
- 725 node, 18 edge types, 7 kategori relasi
- Deterministik vs stokastik
- Ablation A1: −0,2428 RetQ tanpa exact match

## Slide 6: Klaim 2 — Intent-Adaptive Depth
- Depth sensitivity chart (depth_sensitivity_retq.png)
- followup: d=2 optimal (0,943); d=3 turun ke 0,769
- yaml_gen: d=3 optimal (0,909)
- Ablation A3: −0,0484 RetQ dengan fixed depth 2

## Slide 7: Klaim 3 — YAML Validation
- 3 lapis: PyYAML → kubernetes-validate → Neo4j
- syntactic validity 0,9474
- Tanpa dry-run pada cluster aktif

## Slide 8: Hasil Evaluasi
- Tabel perbandingan 3 sistem
- Bar chart: Total 0,6989 vs 0,6111 vs 0,4015
- Highlight RetQ gap: +0,26 (p<0,001)

## Slide 9: Boundary Condition
- Gambar boundary_retq_gain_by_type.png
- GraphRAG paling unggul di: followup (+0,59), planning (+0,59)
- Paling lemah di: realworld (+0,04)

## Slide 10: Kesimpulan & Saran
- 3 Klaim diverifikasi empiris
- Keterbatasan: directed graph, realworld, CGG
- Saran: relasi operasional, Watch API, CGG selektif

## Slide 11: Demo (jika ada)
- Screenshot antarmuka Streamlit
- Contoh reasoning path
```

### D2: Cheatsheet 3 Klaim (`docs/sidang/cheatsheet_3_klaim.md`)

```markdown
# Cheatsheet 3 Klaim Utama

## Klaim 1: Schema-Derived Deterministic KG Construction
**Apa:** KG dibangun dari swagger.json via rule-based type references (bukan LLM-extracted)
**Mengapa penting:** Reproducible, verifiable otomatis, konsisten
**Bukti:** 725 node, 18 edge types, 7 kategori; Ablation A1 (−0,2428 RetQ) + A2 (−0,5585 RetQ)
**Vs. SOTA:** Pan (2024), Wan (2025) extract KG via LLM → stokastik

## Klaim 2: Intent-Adaptive Depth Traversal
**Apa:** d=2 untuk explain/followup; d=3 untuk yaml_gen/planning/trace_relationship
**Mengapa penting:** Tidak ada kedalaman tetap tunggal yang optimal untuk semua intent
**Bukti:** followup: RetQ 0,943 (d=2) → 0,769 (d=3), Δ=−17,4; yaml_gen: 0,755 (d=2) → 0,909 (d=3), Δ=+15,4; Ablation A3 (−0,0484 RetQ)
**Vs. SOTA:** Vector RAG tidak adaptive; fixed depth approach suboptimal

## Klaim 3: KG-Grounded Structural YAML Validation
**Apa:** 3 lapis: PyYAML → kubernetes-validate → Neo4j required fields check
**Mengapa penting:** Validasi tanpa dry-run pada cluster aktif
**Bukti:** syntactic validity 0,9474 (GraphRAG) vs 0,8947 (Vector RAG) vs 0,7895 (Vanilla LLM)
**Vs. SOTA:** Tidak ada penelitian sebelumnya yang menggunakan KG untuk YAML validation

## Hasil Keseluruhan
| Sistem | Total | RetQ |
|--------|-------|------|
| GraphRAG v13 | **0,6989** | **0,6801** |
| Vector RAG | 0,6111 | 0,4249 |
| Vanilla LLM | 0,4015 | 0,0241 |

RetQ: Δ=+0,26, p<0,001, 95% CI [+0,19, +0,33]
```

---

## E. Checklist Final Pre-Sidang

### Compile
- [ ] `xelatex → biber → xelatex → xelatex` berjalan tanpa error
- [ ] Zero `Reference undefined`, zero `Citation undefined`
- [ ] Zero `Error! Bookmark not defined` di output PDF
- [ ] Page count ≤ 150 halaman

### Konsistensi Struktural (REVISI)
- [ ] T1→Bab IV/V, T2→Bab IV/V (incl. validasi YAML), T3→Bab VI; Kesimpulan VII = T1/T2/T3
- [ ] Tidak ada angka evaluasi lama (v12/v13/v17) di seluruh dokumen; hanya angka re-run final
- [ ] Tidak ada `eq:total_score`, bobot 0,40/0,35/0,25, atau "skor Total" di seluruh dokumen
- [ ] Judul Bab IV deskriptif (bukan "PERANCANGAN")
- [ ] Sistematika Penulisan ada di Bab I
- [ ] "Membandingkan" sebagai T3 konsisten: Bab I Tujuan/RM ↔ Bab VI pembuka ↔ Bab VII Ketiga

### Auto-List Compliance
- [ ] Semua `figure` → `\caption{}` + `\label{fig:...}` → masuk Daftar Gambar
- [ ] Semua `table` → `\caption{}` + `\label{tbl:...}` → masuk Daftar Tabel
- [ ] Semua persamaan numbered → `\eqcaption{}` → masuk Daftar Persamaan
- [ ] Semua `lstlisting` → `caption={}` + `label={lst:...}` → masuk Daftar Listing

### Daftar
- [ ] Daftar Simbol up-to-date (semua simbol matematis terdaftar)
- [ ] Daftar Singkatan up-to-date (semua akronim terdaftar)
- [ ] Daftar Isi auto-generated, no "Error!" entries

### Bahasa (Sampling Check)
- [ ] Sample Bab I, III, VI: zero "dimana", zero desimal titik, zero kalimat awal angka
- [ ] Speaker = GPT-4o-mini di semua tempat (Bab V, Abstrak)
- [ ] Zero angka evaluasi lama (0,6989/0,6943/0,6111/0,4015) di Bab VI, VII, Abstrak — hanya angka re-run final
- [ ] Zero `\ref{eq:total_score}` di seluruh dokumen
- [ ] *Path Coverage*, *Hop Accuracy*, *Grounding Score* — italic konsisten di semua bab

### Sidang Companion
- [ ] `docs/sidang/slide_skeleton.md` dibuat
- [ ] `docs/sidang/cheatsheet_3_klaim.md` dibuat
- [ ] `docs/sidang/anticipated_questions.md` dibuat (dari Section C di atas)

### Memory
- [ ] `project_thesis_doc_updates.md` mencatat semua fase Phase 1–9 sebagai SELESAI

---

## Catatan Akhir

Setelah Phase 9 selesai, dokumen siap untuk sidang. Selanjutnya:
1. Konversi slide skeleton ke presentasi actual (PowerPoint/Keynote/Beamer)
2. Latihan jawab pertanyaan dari `anticipated_questions.md`
3. Print hard copy TA.pdf untuk pembimbing dan penguji
