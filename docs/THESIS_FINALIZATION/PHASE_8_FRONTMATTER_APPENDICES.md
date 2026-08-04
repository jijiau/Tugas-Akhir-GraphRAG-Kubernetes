# Phase 8 — Frontmatter, Lampiran, Daftar Simbol/Singkatan

**Status:** PENDING  
**Prasyarat:** Phase 5 (angka v13 final), Phase 6 (Bab VII selesai)  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI (Mei 2026) — abstrak & daftar

**Abstrak (perubahan penting):**
- Narasi per-faktor (RetQ, Path Coverage, Hop Accuracy, *syntactic validity*) tanpa skor Total berbobot.
- Tonjolkan perbandingan 3 sistem; faktor unggul disebutkan setelah re-run, BUKAN diasumsikan sekarang.
- **Angka = TBD** — isi setelah re-run `evaluate.py` final untuk 3 sistem. Tidak ada 0,6989 atau angka lama.
- Stack: GPT-4o-mini Thinker & Speaker (bukan Groq LLaMA).
- T3 di abstrak: "penelitian ini membandingkan..." (bukan "mengimplementasikan validasi YAML ketiga").
- Validasi YAML disebut sebagai komponen sistem (T2), bukan tujuan tersendiri.

**Daftar Singkatan — tambah:**
- **RGA** — *Retrieval-Grounded Accuracy* (atau sesuai nama di `evaluate.py`)

**Daftar Simbol — tambah (dari persamaan baru di Bab II):**
- Notasi dari `eq:hop-accuracy`, `eq:path-coverage`, `eq:grounding`, `eq:rga` (sesuai Bab II final)

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH** kecuali untuk tambah `\input{Lampiran-X.tex}` di appendices block (dengan konfirmasi user terlebih dahulu)
- Frontmatter menggunakan "Saya" untuk Kata Pengantar dan Pernyataan Orisinalitas (exception Aturan C1)
- Daftar Simbol dan Singkatan: update manual, jangan auto-generate

---

## Konteks Phase 8

Phase ini menyelesaikan semua bagian non-bab: frontmatter, lampiran, dan daftar. Ini adalah sesi pembersihan akhir sebelum final review.

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `5 Abstrak.tex` | Rewrite dengan angka v13 + fix stack teknologi |
| `2 Lembar Pengesahan.tex` | Update tanggal sidang |
| `4 Pernyataan Penggunaan AI.tex` | Isi tabel AI usage yang actual |
| `6 Kata Pengantar.tex` | Update tanggal |
| `Lampiran-A.tex` | Update kode/URL GitHub |
| `Lampiran-B.tex` | Cek transkrip wawancara sudah lengkap |
| `Lampiran-C.tex` | Cek dataset 97 fixture sudah lengkap |
| `13 Daftar Simbol.tex` | Sinkronisasi semua simbol dari Bab I–VII |
| `14 Daftar Singkatan.tex` | Sinkronisasi semua singkatan dari Bab I–VII |
| `tables/*.tex` | Audit format (caption di atas, label, header lanjutan) |

---

## 1. Abstrak (`5 Abstrak.tex`)

### Masalah Saat Ini

Abstrak mengandung beberapa informasi yang sudah outdated:
- Skor: AnsQ 0,58, RetQ 0,65, ReaQ 0,87, Total 0,68 → **harus v13**
- Stack: "Groq LLaMA untuk pembuatan jawaban" → **GPT-4o-mini**
- Tidak ada menyebut 3 Klaim utama sebagai kontribusi

### Target Rewrite Abstrak

Struktur yang direkomendasikan (3 paragraf):

**Paragraf 1 — Masalah:**  
Transformasi cloud-native → Kubernetes standar de facto → kompleksitas YAML → LLM halusinasi → Vector RAG tidak cukup (63,4% exact match) → butuh GraphRAG

**Paragraf 2 — Sistem (T1 + T2):**
- T1: Graf deterministik dari swagger.json → 725 node, 18 edge types, 7 kategori
- T2: *Intent-adaptive depth traversal* (d=2/d=3) + validasi YAML 3 lapis berbasis KG
- Stack: GPT-4o-mini (Thinker + Speaker), Neo4j, LangGraph, SQLite

**Paragraf 3 — Perbandingan per-faktor (T3):**
- Perbandingan terhadap Vector RAG & Vanilla LLM pada dimensi AnsQ, RetQ, ReaQ + domain (Path Coverage, Hop Accuracy, RGA, *syntactic validity*)
- Faktor unggul/setara: **TBD dari re-run final** — jangan isi angka lama (0,6989, RetQ +0,26, dll.)
- Uji signifikansi per faktor kunci → CI disebut setelah data tersedia

### Kata Kunci

```
Kata kunci: \textit{Graph Retrieval-Augmented Generation}, \textit{knowledge graph}, 
Kubernetes, YAML, halusinasi LLM, \textit{intent-adaptive depth traversal}, 
\textit{Path Coverage}, \textit{Hop Accuracy}.
```

### Batas Panjang

Abstrak ideal: **250–400 kata**. Satu halaman penuh adalah terlalu panjang.

---

## 2. Lembar Pengesahan (`2 Lembar Pengesahan.tex`)

Update tanggal sesuai jadwal sidang. Cek:
- Nama pembimbing: Dr. Ir. Dimitri Mahayana, M.Eng.
- NIM: 18222001
- Tanggal: [diisi saat sidang dikonfirmasi]

---

## 3. Pernyataan Penggunaan AI (`4 Pernyataan Penggunaan AI.tex`)

Isi tabel sesuai penggunaan aktual AI dalam penelitian ini:

| AI Tool | Kegunaan | Bagian Dokumen |
|---------|----------|----------------|
| Claude (Anthropic) | Debugging kode Python, dokumentasi teknis, review LaTeX | Kode sumber, Bab IV-V |
| GPT-4o-mini | Komponen Thinker (ekstraksi intent) | Sistem GraphRAG |
| GPT-4o-mini | Komponen Speaker (generasi jawaban) | Sistem GraphRAG |
| text-embedding-3-small (OpenAI) | Embedding vector untuk retrieval | Knowledge Graph |

---

## 4. Kata Pengantar (`6 Kata Pengantar.tex`)

- Update tanggal di akhir ("Bandung, [bulan] 2026")
- Ucapan terima kasih ke: pembimbing, penguji, orang tua, rekan
- Gunakan "Saya" (exception C1 untuk frontmatter personal)

---

## 5. Lampiran

### Lampiran A — Kode Program

Saat ini: berisi kode modul utama dan URL GitHub.  
**Cek:** URL repository GitHub masih aktif dan publik.  
**Cek:** Modul yang dicantumkan masih akurat dengan implementasi v13.

Kandidat modul untuk Lampiran A:
- `src/ingestion/parser.py` — SwaggerGraphBuilder
- `src/chatbot/custom_retriever.py` — StatefulK8sRetriever  
- `src/validation/yaml_validator.py` — YAMLValidator
- `scripts/evaluate.py` — evaluator script

Jika kode > 10 baris inline, gunakan `\lstinputlisting` atau pindah ke `listings/` (Aturan G).

### Lampiran B — Transkrip Wawancara Pakar

Saat ini: berisi transkrip 3 narasumber DevOps/SRE.  
**Cek:** Profil narasumber sudah ter-anonimisasi sesuai etika penelitian.  
**Cek:** Kutipan yang digunakan di Bab VI (expert validation) konsisten dengan transkrip.

### Lampiran C — Detail Dataset Fixture

Saat ini: berisi daftar 97 fixture per kategori.  
**Cek:** Jumlah per kategori konsisten: conceptual(15), relationship(18), yaml_gen(15), followup(12), realworld(24), planning(5), troubleshooting(5), command(3) = 97.  
**Cek:** Format fixture (pertanyaan + ground truth) sudah ada.

### Lampiran Tambahan (Jika Perlu)

Jika ada konten yang perlu dipindah dari bab inti untuk menjaga ≤ 150 halaman:
- **Lampiran D:** Detail ablation per-fixture (dari boundary_condition_gain.csv)
- **Lampiran E:** Full evaluation results CSV references

⚠ **Untuk menambah lampiran:** Buat file `Lampiran-D.tex`, dst. DAN tambah `\input{Lampiran-D.tex}` di TA.tex di blok `\begin{appendices}...\end{appendices}` (lines 451–458). **Ini SATU pengecualian yang diizinkan untuk ubah TA.tex — konfirmasi ke user dulu.**

---

## 6. Daftar Simbol (`13 Daftar Simbol.tex`)

Scan Bab I–VII untuk semua simbol matematika. Wajib terdaftar:

| Notasi | Deskripsi | Pemakaian Pertama |
|--------|-----------|------------------|
| $d$ | Kedalaman traversal graf | Bab IV (tabel depth) |
| $\rho$ | Koefisien korelasi Spearman | Bab VI (boundary condition) |
| $p$ | *p-value* uji statistik | Bab VI (statistical test) |
| $\Delta$ | Selisih skor | Bab VI (ablation study) |
| $k$ | Parameter top-k retrieval | Bab VI (Precision@k, Recall@k, NDCG@k) |
| $i$ | Indeks fixture | Bab VI (RetQ-gain definition) |
| $n$ | Jumlah sampel | Bab VI (statistical test) |

Format entry di Daftar Simbol:
```latex
$\rho$ & Koefisien korelasi Spearman & Bab VI \\
```

---

## 7. Daftar Singkatan (`14 Daftar Singkatan.tex`)

Scan Bab I–VII untuk semua akronim. Wajib terdaftar (urutan alfabetis):

| Singkatan | Kepanjangan | Pemakaian Pertama |
|-----------|-------------|------------------|
| AnsQ | *Answer Quality* | Bab VI |
| CGG | *Citation-Grounded Generation* | Bab VI |
| RGA | *Retrieval-Grounded Accuracy* | Bab VI |
| CI | *Confidence Interval* | Bab VI |
| CNCF | *Cloud Native Computing Foundation* | Bab I |
| CRISP-DM | *Cross-Industry Standard Process for Data Mining* | Bab I |
| DAG | *Directed Acyclic Graph* | Bab V |
| GraphRAG | *Graph Retrieval-Augmented Generation* | Bab I |
| IaC | *Infrastructure as Code* | Bab II |
| JSON | *JavaScript Object Notation* | Bab III |
| K8s | Kubernetes | Bab I |
| KG | *Knowledge Graph* | Bab I |
| LLM | *Large Language Models* | Bab I |
| NDCG | *Normalized Discounted Cumulative Gain* | Bab VI |
| OpenAPI | *Open Application Programming Interface* Specification | Bab I |
| RAG | *Retrieval-Augmented Generation* | Bab I |
| RBAC | *Role-Based Access Control* | Bab II/VII |
| ReaQ | *Reasoning Quality* | Bab VI |
| RetQ | *Retrieval Quality* | Bab VI |
| SRE | *Site Reliability Engineering* | Bab VI |
| UUID | *Universally Unique Identifier* | Bab IV/V |
| YAML | *YAML Ain't Markup Language* | Bab I |

---

## 8. Audit Tabel

Semua tabel di `tables/tabel*.tex` harus memenuhi:
- `\caption{}` di **atas** tabel (sudah dikonfigurasi via floatsetup)
- `\label{tbl:...}` yang unik
- Header repeat untuk tabel multi-halaman dengan "(lanjutan)" di caption

Cek khusus tabel inline di Bab VI (tabel ablation, statistical test, boundary) — pindahkan ke `tables/` jika belum.

---

## Checklist Verifikasi Phase 8

### Abstrak
- [ ] Angka dari re-run final (TBD) — TIDAK ada 0,6989 atau angka v12/v13/v17 lama
- [ ] Speaker: GPT-4o-mini (bukan Groq LLaMA)
- [ ] T1 + T2 disebut sebagai kontribusi sistem; T3 = "penelitian ini membandingkan..."
- [ ] Validasi YAML = komponen T2 (bukan tujuan ketiga)
- [ ] Faktor unggul disebutkan setelah re-run (placeholder TBD)
- [ ] Kata kunci mencakup: GraphRAG, knowledge graph, Kubernetes, YAML, intent-adaptive, Path Coverage, Hop Accuracy

### Frontmatter
- [ ] Lembar Pengesahan: tanggal, nama pembimbing benar
- [ ] Pernyataan AI: tabel terisi dengan actual AI usage
- [ ] Kata Pengantar: tanggal terupdate

### Lampiran
- [ ] Lampiran A: URL GitHub valid; modul v13
- [ ] Lampiran B: 3 transkrip pakar; profil anonim
- [ ] Lampiran C: 97 fixture per kategori lengkap

### Daftar Simbol
- [ ] Semua simbol matematis di Bab I–VII terdaftar
- [ ] Tidak ada entry orphan (simbol di daftar yang tidak muncul di bab)
- [ ] Urutan: simbol Yunani → operator → variabel → metrik

### Daftar Singkatan
- [ ] Semua akronim di Bab I–VII terdaftar (lihat daftar di atas)
- [ ] Tidak ada entry orphan
- [ ] Urutan alfabetis
- [ ] Kolom "pemakaian pertama" terisi dengan nomor bab/halaman

### Tabel
- [ ] Semua tabel punya `\caption{}` di atas + `\label{tbl:...}`
- [ ] Tabel inline Bab VI dipindah ke `tables/` atau minimal punya label lengkap

---

## Catatan untuk Phase Selanjutnya

- **Phase 9** (Final): Compile penuh TA.tex, cek page count (≤ 150 halaman), mock dosen penguji review
