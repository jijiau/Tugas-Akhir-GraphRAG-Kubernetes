# STYLE_GUIDE — Pedoman Gaya Bahasa (mandiri & reusable)

> Dokumen mandiri & lengkap untuk Audit E2E TA GraphRAG-Kubernetes. **Satu-satunya** rujukan gaya bahasa untuk semua fase penulisan/penyuntingan dokumen tesis (Fase 4/5/6). Ditulis ulang khusus; TIDAK menarik konteks dari MD lain (mis. `CONTEXT_PRIMER.md`/`PHASE_7`). Target: bahasa Indonesia akademik baku + istilah teknis terapan yang benar. Berlaku untuk semua file `.tex` bab inti, frontmatter, lampiran, caption, dan tabel.

## A. Persona & sudut pandang
- Gunakan **"Penelitian ini ..."** (mis. "Penelitian ini mengusulkan sistem GraphRAG ...").
- Hindari "Penulis ...", "Saya/Kami ...", dan pasif tanpa pelaku ("Diusulkan sistem ...").
- Pengecualian: **Kata Pengantar** & **Pernyataan Orisinalitas** → gunakan "Saya".

## B. Kaidah tata bahasa Indonesia (hard rules)
| # | Aturan | ✅ Benar | ❌ Salah |
|---|--------|---------|---------|
| 1 | Pemisah desimal = **koma**; di math mode `0{,}85` | "skor 0,85"; "$p<0{,}001$" | "0.85"; "$p<0.001$" |
| 2 | "sehingga"/"sedangkan" hanya intrakalimat, tak di awal kalimat | "X sehingga Y." | "Sehingga Y." |
| 3 | "sedangkan" didahului koma; "sehingga" TIDAK | "X, sedangkan Y." / "X sehingga Y." | "X sedangkan Y." / "X, sehingga Y." |
| 4 | "karena" TIDAK didahului koma | "X karena Y." | "X, karena Y." |
| 5 | "di" kata depan dipisah; awalan verba serangkai | "di atas", "di bawah", "dianalisis", "digunakan" | "diatas", "di analisis" |
| 6 | Tanpa "di mana"/"dimana" sebagai relative pronoun | "sistem yang menyimpan data"; "ruang tempat rapat" | "sistem di mana data disimpan" |
| 7 | Istilah baku KBBI | analisis, aktivitas, kinerja, kualitas, repositori, kueri, dependensi, orkestrasi, kontainer, halusinasi, metodologi | analisa, aktifitas, kwalitas, query (non-italic), existing |
| 8 | Subjek wajib ada setelah keterangan depan | "Penelitian ini menggunakan ..." | "Dalam penelitian ini menggunakan ..." |
| 9 | Jangan mulai kalimat dengan angka | "Sebanyak 97 \textit{fixture} ..."; "Graf memiliki 725 node ..." | "97 \textit{fixture} ..."; "725 node ..." |
| 10 | "tiap-tiap"/"setiap" alih-alih "masing-masing X" | "setiap komponen", "tiap-tiap intent" | "masing-masing komponen" |
| 11 | Em-dash DILARANG di body (`—`, `---`) → titik / koma+konjungsi | "... antar-eksekusi, berbeda dengan LLM yang stokastik." | "... antar-eksekusi—berbeda ..." |
| 12 | Range angka pakai en-dash `--` (output "–") | "kedalaman 1--5"; "derajat 3--7" | "kedalaman 1-5" |

## C. Terminologi & italic (konsisten di SELURUH dokumen, bukan hanya first mention)
| Entitas | Format | Contoh |
|---------|--------|--------|
| Edge type | `\textit{CAPS\_CASE}` | \textit{HAS\_PROPERTY}, \textit{EXTENDS}, \textit{SELECTS\_POD} |
| Node pipeline LangGraph | `\textit{lowercase}` | \textit{thinker}, \textit{speaker}, \textit{retriever}, \textit{saver}, \textit{memory} |
| Nama class | `\textit{PascalCase}` | \textit{StatefulK8sRetriever}, \textit{YAMLValidator} |
| Intent type | `\textit{snake\_case}` | \textit{generate\_yaml}, \textit{trace\_relationship}, \textit{planning} |
| Resource K8s | italic | \textit{Pod}, \textit{Deployment}, \textit{StatefulSet}, \textit{ConfigMap} |
| Dimensi metrik | KAPITAL tanpa italic | AnsQ, RetQ, ReaQ |
| Nama metrik domain | italic | \textit{Path Coverage}, \textit{Hop Accuracy}, \textit{Grounding Score} |
| RGA | akronim, tanpa italic | RGA |
| Istilah asing teknis | **italic English** | \textit{retrieval}, \textit{embedding}, \textit{pipeline}, \textit{traversal}, \textit{knowledge graph}, \textit{node}, \textit{edge}, \textit{intent}, \textit{multi-hop}, \textit{fallback}, \textit{baseline}, \textit{ground truth}, \textit{reasoning path}, \textit{ablation study} |
| Baku Indonesia | tanpa italic | analisis, evaluasi, implementasi, arsitektur, kinerja, halusinasi, kontainer, orkestrasi, dependensi, signifikan |
| Proper noun | tanpa italic | Kubernetes, Neo4j, LangGraph, GPT-4o-mini, Python, YAML, JSON, OpenAPI |
| Akronim | kepanjangan italic + (singkatan) di first mention, lalu singkatan | \textit{Retrieval-Augmented Generation} (RAG); berikutnya: RAG — wajib masuk Daftar Singkatan |
| Versi K8s | "v1.30" | bukan "1.30" / "versi 1.30" |
| Kedalaman traversal | "kedalaman 1--5" atau `$d \in \{1,2,3,4,5\}$` | bukan "depth 1-5" |

## D. Sitasi (Chicago via biblatex)
- Parentetik (default): `\parencite{key}` → "(Wan 2025)".
- Naratif / posisi subjek: `\textcite{key}` → "Wan (2025)". DILARANG "(Wan 2025) mengusulkan ...".
- Multi-sumber: `\parencite{key1, key2}`.
- Setiap citekey yang dipakai WAJIB ada entry di `.bib` (nol orphan); nol entry tak terpakai.

## E. Referensi gambar/tabel/persamaan
- Rujuk langsung & bernomor: "Gambar IV.2 menunjukkan ..."; "Tabel VI.3 merangkum ..."; bukan "gambar di bawah ini".
- Nomor tanpa spasi & tanpa titik akhir: "Gambar IV.2 Deskripsi" (bukan "Gambar IV. 2.").
- Persamaan disebut "Persamaan II.4" (bukan "Gambar"); keterangan natural ditulis di LUAR `equation`.
- Tabel multi-halaman: tambah "(lanjutan)" + ulang header.

## F. Struktur paragraf, tone, anti-pattern
- Paragraf 3–6 kalimat, satu ide pokok, topic sentence di awal; variasikan pembuka (jangan 5× berturut "Penelitian ini ...").
- Tone akademik & terukur: "menunjukkan", "mengindikasikan", "mencapai \textit{p}<0,001"; hindari "membuktikan mutlak", "sangat signifikan", "revolusioner", kata alarmis.
- Bold minimal: hanya label Klaim 1/2/3 di Bab I & VII dan 1–2 frasa highlight di Abstrak.
- Hindari: pasif berantai >3, nominalisasi berlebih ("pengimplementasian dilakukan" → "diimplementasikan"), filler ("pada dasarnya", "perlu diingat bahwa"), redundansi ("berdasarkan dari" → "berdasarkan"), bullet menyamar ("A dan B dan C dan D" → `\begin{enumerate}`), cross-ref menggantung (`\ref{}` tanpa `\label{}`).

## G. LaTeX auto-list (agar entitas masuk daftar masing-masing)
- Gambar: `figure[H]` + `\centering` + `\includegraphics` + `\caption{}` + `\label{fig:...}`.
- Tabel: `table[H]` + `\caption{}` (di ATAS) + `\label{tbl:...}` + `tabular`.
- Persamaan: `equation` + `\eqcaption{Nama}` (command dari TA.tex) + `\label{eq:...}`.
- Algoritma: `algorithm[H]` + `\caption{}` + `\label{alg:...}` + `algorithmic` (Daftar Algoritma; untuk pseudocode formal bernomor baris).
- Listing kode/pseudocode/JSON >10 baris: `\input{listings/...}` (bukan dump inline). Opsi `lstlisting`: `[language=<Python|JSON>, caption={...}, label={lst:...}, frame=single, captionpos=t]`. Caption otomatis **kiri-atas** (global TA.tex: `capposition=top` + `justification=raggedright`, `singlelinecheck=false`); nama label render "\textit{Listing}". Caption berbahasa Indonesia, istilah teknis italic, nama simbol kode pakai `\texttt{}`. Contoh nyata: `listings/depth-by-intent.tex`. (Daftar Listing; untuk snippet kode/konfig/JSON apa adanya.)
- Simbol/akronim baru → tambah entry ke `13 Daftar Simbol.tex` / `14 Daftar Singkatan.tex` saat itu juga.
- Caption berbahasa Indonesia; istilah teknis tetap italic English.

## H. Batasan teknis (penulisan)
- `TA.tex` READ-ONLY; nol perubahan `\usepackage`/`\geometry`/margin/global.
- Target total ≤ 150 halaman; bila lebih, pindahkan konten ke Lampiran.
