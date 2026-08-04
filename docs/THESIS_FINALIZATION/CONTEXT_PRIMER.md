# Context Primer — Finalisasi Dokumen TA GraphRAG Kubernetes

> **Cara pakai:** Paste isi file ini di awal prompt chat baru sebelum mulai mengerjakan fase apapun.  
> Berisi: info proyek, constraint global, dan seluruh aturan penulisan.

---

## ⚠ REVISI MID-IMPLEMENTASI (Mei 2026) — BACA DULU

Arah berubah di tengah jalan; sebagian isi di bawah sudah usang. Ringkas perubahan:
1. **Struktur Tujuan baru:** T1 (bangun KG) · T2 (bangun sistem GraphRAG, **validasi YAML melebur ke sini**) · **T3 = Membandingkan** GraphRAG vs Vector RAG vs Vanilla LLM (rumah di Bab VI). Lihat tabel Tujuan yang sudah direvisi.
2. **Evaluasi per-faktor, tanpa skor Total berbobot.** Dimensi (AnsQ/RetQ/ReaQ) & metrik domain (Path Coverage, Hop Accuracy, RGA) ditotal per bagian; `eq:total_score` & bobot 0,40/0,35/0,25 dibuang.
3. **Metrik diganti & semua definisi dikonsolidasi di Bab II.** RetQ=(F1+NDCG+Path Coverage)/3; ReaQ=(Hop Accuracy+Grounding)/2; *hallucination* dibuang.
4. **Semua angka evaluasi = TBD** sampai `evaluate.py` final di-rerun untuk 3 sistem (v17 pun masih metrik lama).
5. **Hipotesis bukan klaim:** keunggulan presisi *retrieval*/validitas YAML dijawab empiris di Bab VI/VII, jangan diasumsikan di muka.

Detail lengkap: `.claude/plans/act-seperti-orang-yang-smooth-pearl.md`.

---

## Identitas Proyek

**Judul:** Implementasi *Graph Retrieval-Augmented Generation* untuk Meningkatkan Presisi *Retrieval* dan Validitas Sintaksis pada Konfigurasi Kubernetes  
**Penulis:** Jihan Aurelia (18222001), ITB STEI — Sistem dan Teknologi Informasi  
**Pembimbing:** Dr. Ir. Dimitri Mahayana, M.Eng.  
**Template:** TA-STI-template-1.0 (Kaprodi: IGB Baskara Nugraha)  
**Working dir:** `c:\Users\Jihan Aurelia\Documents\SMT8\Tugas-Akhir-GraphRAG-Kubernetes\`

---

## Stack Teknologi Sistem (v13 — Final)

| Komponen | Teknologi |
|----------|-----------|
| Knowledge Graph | Neo4j (725 node, 18 jenis *edge*, 7 kategori relasi) |
| Thinker LLM | GPT-4o-mini, temp=0,0 |
| Speaker LLM | GPT-4o-mini, temp=0,1 (**bukan** Groq) |
| Memory | SQLite |
| Orchestration | LangGraph 5-node (*memory → thinker → retriever → speaker → saver*) |
| UI | Streamlit (`main.py`) |
| Embeddings | text-embedding-3-small (OpenAI, 1536-dim) |
| YAML Validation | PyYAML + kubernetes-validate + Neo4j (3 lapis) |
| Dataset | 97 *fixture* uji, 8 kategori |

---

## Tiga Tujuan Penelitian (T1/T2/T3) — REVISI

| Label | Tujuan | Rumah di bab |
|-------|--------|-------|
| **T1** | **Membangun** *knowledge graph* deterministik dari spesifikasi OpenAPI Kubernetes (`swagger.json`) | Bab IV/V |
| **T2** | **Mengembangkan** sistem GraphRAG: *retrieval* *intent-adaptive depth* + validasi YAML tiga lapis berbasis *knowledge graph* (validasi YAML **melebur** ke sini) | Bab IV/V |
| **T3** | **Membandingkan** kinerja GraphRAG terhadap Vector RAG & Vanilla LLM untuk mengidentifikasi faktor-faktor keunggulannya | Bab VI |

**Sinkronisasi:** T1→Bab IV/V · T2→Bab IV/V · **T3→Bab VI** · Kesimpulan Bab VII = 3 paragraf (T1/T2/T3).
⚠ Hipotesis (presisi *retrieval* + validitas YAML) dijawab empiris di Bab VI/VII, bukan diasumsikan. Risiko Kaprodi atas kata "Membandingkan": konfirmasi pembimbing; fallback verb artefak tersedia di plan revisi.

---

## Hasil Evaluasi — MENUNGGU RE-RUN (semua angka TBD)

⚠ Metrik sudah diganti (lihat bagian metrik) dan `evaluate.py` final **belum dijalankan**. Seluruh CSV lama (termasuk v17) masih formula lama → **jangan dipakai**. Angka final keluar setelah re-run 3 sistem (GraphRAG, Vector RAG, Vanilla LLM) dengan `evaluate.py` final.

Yang dilaporkan = **perbandingan per-faktor** (bukan satu skor Total berbobot):
- Dimensi: AnsQ, RetQ, ReaQ (masing-masing ditotal dari sub-metriknya, tanpa bobot antar-dimensi)
- Domain-spesifik: Path Coverage, Hop Accuracy, RGA, *syntactic validity* YAML
- Uji signifikansi (Wilcoxon + bootstrap) & 95% CI dihitung per faktor kunci setelah re-run.
- Faktor tempat GraphRAG unggul/setara/lemah = **temuan empiris**, ditetapkan setelah re-run (bukan diasumsikan).

---

## ⚠ CONSTRAINT GLOBAL — WAJIB DI SEMUA FASE

### 1. `TA.tex` TIDAK BOLEH DIUBAH

File `docs/TA-STI-template-1.0/TA.tex` adalah template resmi Kaprodi ITB. **READ-ONLY.**

Larangan absolut:
- ❌ Ubah `\usepackage`, `\geometry`, `\setmainfont`
- ❌ Ubah captionsetup, floatsetup, biblatex/biber settings
- ❌ Ubah margin, spasi, atau format global
- ❌ Tambah `\input{}` baru kecuali lampiran baru di blok `\begin{appendices}` (konfirmasi user dulu)

Semua pekerjaan terjadi di: `Bab I-VII.tex`, `Lampiran-*.tex`, frontmatter `.tex`, `tables/`, `images/`

### 2. Compile Sequence (READ-ONLY pada TA.tex)

```
xelatex TA.tex → biber TA → xelatex TA.tex → xelatex TA.tex
```

---

## Aturan Bahasa — House Style Guide

### A. Hard Rules ITB (Non-negotiable)

| # | Aturan | ✅ Benar | ❌ Salah |
|---|--------|---------|---------|
| 1 | "sehingga"/"sedangkan" hanya intrakalimat, tidak di awal | "X sehingga Y." | "Sehingga Y." |
| 2 | "sedangkan" didahului koma; "sehingga" TIDAK | "X, sedangkan Y." / "X sehingga Y." | "X sedangkan Y." / "X, sehingga Y." |
| 3 | "di" kata depan dipisah; awalan verba serangkai | "di atas", "dianalisis" | "diatas", "di analisis" |
| 4 | Istilah baku KBBI | analisis, aktivitas, kinerja | analisa, aktifitas |
| 5 | Tidak ada "di mana"/"dimana" sebagai relative pronoun | "sistem yang menyimpan data" | "sistem di mana data disimpan" |
| 6 | "masing-masing" setelah kata yang diterangkan | "tiap-tiap algoritma" | "masing-masing algoritma" |
| 7 | Pemisah desimal: **koma** | "0,6989", "$p < 0{,}001$" | "0.6989", "$p < 0.001$" |
| 8 | Subjek wajib ada setelah keterangan | "Penelitian ini menggunakan..." | "Dalam penelitian ini menggunakan..." |
| 9 | Sitasi Chicago: `\parencite{}` atau `\textcite{}` | `(Wan 2025)` / `Wan (2025)` | format APA/IEEE manual |
| 10 | Referensi langsung ke Gambar/Tabel/Persamaan | "Gambar IV.2 menunjukkan..." | "gambar di bawah ini" |
| 11 | Nomor Gambar/Tabel tanpa spasi, tanpa titik akhir | "Gambar IV.2 Deskripsi" | "Gambar IV. 2." |
| 12 | List pakai nomor/huruf, hindari bullet • | (a), (b) atau 1, 2, 3 | • item |
| 13 | Jangan mulai kalimat dengan angka | "Sebanyak 97 *fixture*..." | "97 *fixture*..." |
| 14 | Tabel multi-halaman: "(lanjutan)" + repeat header | "Tabel III.5 Judul (lanjutan)" | header tidak diulang |
| 15 | Equation: bahasa natural di luar, bukan di dalam | tulis keterangan di luar `equation` | `d = 1/x jika x ≠ 0` dalam equation |
| 16 | Persamaan bukan "Gambar" | "Persamaan II.4" | "Gambar III.4 Persamaan" |
| 17 | "karena" **tidak** didahului koma | "X karena Y." | "X, karena Y." |

### B. Terminologi Proyek (Konsisten di Seluruh Dokumen)

| Entitas | Format | Contoh |
|---------|--------|--------|
| Edge type | `\textit{CAPS\_CASE}` | *HAS\_PROPERTY*, *EXTENDS*, *REFERENCES* |
| Node pipeline LangGraph | `\textit{lowercase}` | *thinker*, *speaker*, *retriever*, *saver*, *memory* |
| Class name | `\textit{PascalCase}` | *StatefulK8sRetriever*, *SwaggerGraphBuilder*, *YAMLValidator* |
| Intent type | `\textit{snake\_case}` | *generate\_yaml*, *trace\_relationship*, *planning*, *explain* |
| Dataset uji | "*fixture*" | "97 *fixture* uji" — **bukan** "test case" |
| Sistem ini | "sistem GraphRAG" atau "GraphRAG" (konsisten per bab) | — |
| Dimensi metrik | KAPITAL tanpa italic | AnsQ, RetQ, ReaQ |
| Resource K8s | italic kapital | *Pod*, *Deployment*, *StatefulSet*, *ConfigMap* |
| Versi K8s | "v1.30" | bukan "1.30" atau "versi 1.30" |
| Kedalaman traversal | "$d \in \{1, 2, 3, 4, 5\}$" atau "kedalaman 1–5" | bukan "depth 1-5" |
| 3 Kontribusi | "Klaim 1/2/3" atau "kontribusi pertama/kedua/ketiga" | konsisten per konteks |

### C. Style Decisions

#### C1. Persona Penulis: "Penelitian ini..."

```
✅ "Penelitian ini mengusulkan sistem GraphRAG..."
✅ "Penelitian ini menggunakan dataset 97 fixture..."
❌ "Penulis mengusulkan..." (third person)
❌ "Saya/Kami mengusulkan..." (first person)
❌ "Diusulkan sistem..." (pasif tanpa pelaku)
```

**Exception:** Kata Pengantar dan Pernyataan Orisinalitas → gunakan "Saya"

#### C2. Kebijakan Istilah Asing (Starter List)

**Prinsip:** teknis English yang lazim → italic English; non-teknis atau baku KBBI → Indonesia.

| Istilah | Keputusan |
|---------|-----------|
| *retrieval*, *embedding*, *pipeline*, *traversal* | **English italic** |
| *reasoning*, *reasoning path*, *trace*, *path* | **English italic** |
| *knowledge graph*, *node*, *edge*, *intent* | **English italic** |
| *multi-hop*, *fallback*, *seed node*, *ablation study* | **English italic** |
| *baseline*, *ground truth*, *runtime*, *production-grade* | **English italic** |
| *cloud-native*, *fine-tuning*, *prompt* | **English italic** |
| halusinasi, kontainer, orkestrasi, dependensi | **Indonesia** (baku) |
| analisis, evaluasi, implementasi, arsitektur, kinerja | **Indonesia** (baku) |
| kueri, metodologi, signifikan, repositori | **Indonesia** (baku) |
| RAG, LLM, KG, GraphRAG | **Akronim** (kepanjangan italic di first mention) |
| Kubernetes, Neo4j, LangGraph, GPT-4o-mini, Python | **Proper noun** (tidak italic) |
| YAML, JSON, OpenAPI | **Proper noun** (tidak italic) |

**Untuk istilah ambiguous:** konfirmasi ke user sebelum menetapkan.

**Aturan italic:**
- Gunakan `\textit{X}` untuk semua istilah asing yang dipertahankan English
- Konsisten di seluruh bab (tidak hanya first mention)
- Proper noun dan akronim: tidak italic

#### C3. Format Singkatan & Akronim

- **First mention:** kepanjangan italic + (singkatan) → `\textit{Retrieval-Augmented Generation} (RAG)`
- **Selanjutnya:** singkatan saja → `RAG`
- **Wajib masuk** Daftar Singkatan

#### C4. Struktur Paragraf

- 3–6 kalimat per paragraf; satu ide pokok
- Topic sentence di awal
- Transisi antar paragraf: "Selanjutnya", "Di sisi lain", "Berdasarkan hal tersebut"
- Hindari paragraf 1 kalimat (kecuali emphasis kritis)
- Paragraf > 8 kalimat: pecah jadi 2

#### C5. Tone & Hedging

| ✅ Pakai | ❌ Hindari |
|---------|-----------|
| "menunjukkan", "mengindikasikan" | "membuktikan secara mutlak", "menjamin" |
| "berhasil ... dengan skor 0,69" | "sangat berhasil", "luar biasa" |
| "mencapai signifikansi $p<0{,}001$" | "sangat signifikan" |
| "unggul $\Delta=+0{,}26$" | "jauh lebih unggul", "revolusioner" |
| "menjadi sumber utama X", "tantangan Y" | "epidemi X", "krisis Y" — kata dramatis/alarmis |

#### C6. Range Angka: En-dash

- Di LaTeX: `1--5` → output "1–5"
- Set matematis: `$d \in \{1, 2, 3, 4, 5\}$`
- Bukan hyphen: `1-5` ❌

#### C7. Bold dalam Paragraf

Minimal. Hanya untuk:
- Label 3 Klaim di Bab I & VII: "**Pertama**, ...", "**Kedua**, ...", "**Ketiga**, ..."
- Highlight kontribusi kritis di abstrak (maks 1–2 frasa per paragraf)

#### C8. Footnote

Dihindari. Side-note teknis → masuk body paragraf atau Lampiran.

#### C12. Em-dash: Dilarang di Body Text

Em-dash Unicode (`—`, U+2014) dan LaTeX `---` **tidak boleh muncul** di body paragraf manapun.

Ganti dengan salah satu:
- Titik + kalimat baru (pilihan utama)
- Koma + konjungsi ("sehingga...", "berbeda dengan...", "karena...")

```
✅ "... konsisten antar-eksekusi, berbeda dengan pendekatan LLM yang stokastik."
✅ "... langsung dari representasi graf. Mekanisme ini berfungsi sebagai..."
❌ "... konsisten antar-eksekusi—berbeda dengan pendekatan LLM yang stokastik."
❌ "... dari representasi graf—menyediakan alternatif validasi..."
```

Catatan: `---` di dalam baris komentar LaTeX (`%`) tidak render ke PDF dan boleh dibiarkan.

#### C9. Format Sitasi

```latex
% Parentetik (default):
\parencite{wan2025empowering}    → (Wan 2025)
\parencite{pan2024unifying}      → (Pan 2024)

% Naratif:
\textcite{wan2025empowering}     → Wan (2025)

% Multi-source:
\parencite{wan2025empowering, pan2024unifying}

% SALAH — parentetik tidak boleh di posisi subjek:
❌ "(Wan 2025) mengusulkan..."
✅ "Wan (2025) mengusulkan..."  ← pakai \textcite{}
```

#### C10. Caption Gambar/Tabel

Bahasa Indonesia; istilah teknis tetap italic English:
```latex
\caption{Diagram arsitektur sistem \textit{GraphRAG} Kubernetes}
\caption{Konfigurasi parameter \textit{LangGraph Agent Pipeline}}
```

#### C11. Anti-Pattern yang Harus Dihindari

| Anti-pattern | Contoh Salah | Perbaikan |
|--------------|-------------|-----------|
| Pasif berantai > 3 | "dikumpulkan, dianalisis, divalidasi, disimpan" | Pecah / satu jadi aktif |
| Nominalisasi berlebihan | "pengimplementasian dilakukan" | "diimplementasikan" |
| Frasa filler | "pada dasarnya", "perlu diingat bahwa" | Hapus langsung |
| Redundansi | "hasil daripada penelitian", "berdasarkan dari" | "hasil penelitian", "berdasarkan" |
| Cross-ref dangling | `\ref{fig:xxx}` tanpa `\label{fig:xxx}` | Tambah label atau hapus ref |
| Pembuka paragraf monoton | 5× berturut "Penelitian ini..." | Variasi: "Berdasarkan...", "Hasil menunjukkan..." |
| Bullet disguise | "menggunakan A dan B dan C dan D" | Ubah ke `\begin{enumerate}` |
| Modifier ambigu | "tiga kontribusi yang dapat diverifikasi" (oleh siapa? bagaimana?) | Hapus modifier atau jabarkan konkret |
| Jargon tanpa definisi | "aturan berbasis tipe" tanpa penjelasan mekanisme | Jelaskan eksplisit: "setiap tipe → *node*, setiap `$ref` → *edge*" |

### D. LaTeX: Aturan Auto-List

Setiap entitas HARUS ditulis dengan command berikut agar masuk ke daftar masing-masing:

#### D1. Gambar → Daftar Gambar
```latex
\begin{figure}[H]
    \centering
    \captionsetup{justification=centering}
    \includegraphics[width=0.85\textwidth]{images/namafile.png}
    \caption{Deskripsi gambar}
    \label{fig:nama-label}
\end{figure}
```

#### D2. Tabel → Daftar Tabel
```latex
\begin{table}[H]
    \caption{Deskripsi tabel}   % ← di ATAS
    \label{tbl:nama-label}
    \centering
    \begin{tabular}{...}
    ...
    \end{tabular}
\end{table}
```

#### D3. Persamaan → Daftar Persamaan
```latex
\begin{equation}
    \text{Path Coverage} = \frac{|E_{\text{retrieved}} \cap E_{\text{relevant}}|}{|E_{\text{relevant}}|}
    \eqcaption{Nama Persamaan}   % ← custom command dari TA.tex
    \label{eq:nama-label}
\end{equation}
% Catatan: skor Total berbobot (eq:total_score) sudah DIHAPUS — evaluasi per-faktor.
```

#### D4. Algoritma → Daftar Algoritma
```latex
\begin{algorithm}[H]
    \caption{Nama Algoritma}
    \label{alg:nama-label}
    \begin{algorithmic}[1]
        ...
    \end{algorithmic}
\end{algorithm}
```

#### D5. Listing/Kode → Daftar Listing
```latex
\begin{lstlisting}[language=Python, caption={Deskripsi kode}, label={lst:nama-label}]
def fungsi():
    pass
\end{lstlisting}
```

#### D6–D7. Daftar Simbol & Singkatan
- Update manual di `13 Daftar Simbol.tex` dan `14 Daftar Singkatan.tex`
- Setiap simbol/akronim baru di bab manapun → tambah entry segera

### E. Bibliography (.bib) Protocol

File: `docs/TA-STI-template-1.0/daftar-pustaka.bib`

**Format entry:**
```bibtex
@article{wan2025empowering,
  author  = {Wan, ... and ...},
  title   = {Empowering ...},
  journal = {Nama Jurnal},
  year    = {2025},
  doi     = {10.xxxx/...}
}

@misc{citekey,
  author = {Author},
  title  = {Title},
  year   = {2025},
  url    = {https://...},
  note   = {diakses pada 2026-05-28}
}
```

**Citekey convention:** `{lastname}{year}{firstword}` — contoh: `wan2025empowering`

**Wajib:** Setiap citekey yang dipakai harus ada entry-nya. Tidak ada orphan.

### F. Page Count

Target total TA.pdf: **≤ 150 halaman**. Jika lebih, pindahkan konten ke Lampiran.

### G. Folder untuk Kode & Algoritma Panjang

```
docs/TA-STI-template-1.0/
├── listings/        ← kode Python/JSON/YAML > 10 baris
├── algorithms/      ← pseudocode panjang
└── tables/          ← tabel kompleks (via \input{})
```

Di bab inti: `\input{listings/nama-file.tex}` — bukan dump kode langsung.

---

## Struktur 9 Fase Finalisasi

```
Phase 1 (Struktur) → Phase 2 (Bab I) → Phase 3 (Bab II-III) → Phase 4 (Bab IV-V)
                                                                       ↓
Phase 9 (Final) ← Phase 8 (Frontmatter) ← Phase 7 (Bahasa) ← Phase 6 (Bab VII) ← Phase 5 (Bab VI)
```

| Phase | File MD Instruksi | Scope Singkat |
|-------|-------------------|---------------|
| 1 | `PHASE_1_FOUNDATIONAL_RESTRUCTURE.md` | Bab I: Tujuan baru (T3=Membandingkan) + RM; struktur Bab IV/V tetap |
| 2 | `PHASE_2_BAB1_REFRAMING.md` | Tambah Sistematika Penulisan; reframe Latar Belakang 3 Klaim |
| 3 | `PHASE_3_BAB2_3_AUDIT.md` | Konsolidasi semua metrik ke Bab II (pindah metrik domain dari Bab III); buang pembobotan |
| 4 | `PHASE_4_BAB4_5_DETAIL_DIAGRAMS.md` | Bab IV/V konten substantif; fix Groq; diagram audit |
| 5 | `PHASE_5_BAB6_EMPIRICAL.md` | Bab VI per-faktor (rumah T3); hapus eq:total_score; re-run 3 sistem; angka TBD |
| 6 | `PHASE_6_BAB7_REFRAMING.md` | Kesimpulan per-faktor (T1/T2/T3 baru); faktor pemenang TBD; Keterbatasan |
| 7 | `PHASE_7_LANGUAGE_CITATION_AUDIT.md` | Grep audit 16 hard rules + anti-pattern seluruh bab |
| 8 | `PHASE_8_FRONTMATTER_APPENDICES.md` | Abstrak v13; frontmatter; lampiran; Daftar Simbol/Singkatan |
| 9 | `PHASE_9_FINAL_REVIEW.md` | Compile test; mock penguji 13 pertanyaan; sidang companion |

**Semua Phase MD ada di:** `docs/THESIS_FINALIZATION/`

---

## File-File Kritis

| Kategori | File | Boleh Ubah? |
|----------|------|------------|
| Template | `docs/TA-STI-template-1.0/TA.tex` | ❌ **TIDAK** |
| Bab inti | `Bab I–VII .tex` | ✅ |
| Frontmatter | `1–6 Halaman*.tex`, `5 Abstrak.tex` | ✅ |
| Lampiran | `Lampiran-A/B/C.tex` | ✅ |
| Tabel | `tables/tabel*.tex` | ✅ |
| Gambar | `images/*.png` | ✅ |
| Bibliography | `daftar-pustaka.bib` | ✅ (tambah entry saja) |
| Daftar | `13 Daftar Simbol.tex`, `14 Daftar Singkatan.tex` | ✅ |
