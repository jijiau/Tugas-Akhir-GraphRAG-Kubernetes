# Paper IEEE Access — GraphRAG Kubernetes

Ringkasan dari laporan TA `docs/18222001-JIHAN AURELIA-LaporanTA.pdf`, format IEEE Access, dua
versi bahasa. Deliverable akhir ada di `docs/`:

- `18222001_Jihan Aurelia_Paper_ID.pdf` (Bahasa Indonesia) — **4 halaman**
- `18222001_Jihan Aurelia_Paper_EN.pdf` (Bahasa Inggris) — **6 halaman**

Keduanya sah terhadap batas 4–6 halaman, tetapi **panjangnya sengaja berbeda**. Versi EN
diperluas di sesi terpisah atas permintaan eksplisit user untuk memakai kuota halaman penuh;
versi ID sengaja dibiarkan seperti semula dan tidak disentuh saat perluasan itu. Jadi versi EN
memuat empat subbab (Related Work, Traversal Depth Sensitivity, Boundary Conditions, dekomposisi
klaim *faithfulness* yang lebih rinci) yang **tidak ada** padanannya di versi ID. Kalau versi ID
suatu saat perlu diperluas menyusul, materi sumbernya sama seperti yang dipakai di EN (lihat
bagian "Materi yang hanya ada di versi Inggris" di bawah).

Penulis versi EN: **Jihan Aurelia, Dimitri Mahayana, dan Naufal Irsyadi** (tiga penulis).
Penulis versi ID masih dua (Jihan Aurelia dan Dimitri Mahayana) — Naufal belum ditambahkan di
sana karena belum dikonfirmasi user. Biografi di akhir dokumen versi EN **hanya mencantumkan
Jihan Aurelia** (dengan foto profil dari `docs/TA-STI-template-1.0/images/profile.png`, di-*crop*
ke rasio 4:5 agar pas dengan kotak foto biografi IEEE Access yang berukuran tetap 1×1,25 inci);
keputusan ini berasal dari permintaan eksplisit user, bukan default kaidah IEEE Access (yang
biasanya mewajibkan biografi tiap penulis). Versi ID masih memakai biografi lama (Jihan Aurelia
dan Dimitri Mahayana, tanpa foto) karena perubahan biografi ini belum diminta untuk versi ID.

## Cara compile ulang

```powershell
$env:PATH = (($env:PATH -split ';') | Where-Object { $_ -notmatch 'supabase|heroku' }) -join ';'
foreach ($d in 'paper_id','paper_en') {
    pdflatex -interaction=nonstopmode $d
    bibtex $d
    pdflatex -interaction=nonstopmode $d
    pdflatex -interaction=nonstopmode $d
}
```

Filter PATH di atas wajib — entri `supabase`/`heroku` di PATH sistem memblokir MiKTeX (lihat
memori `reference_latex_compile`). Paper ini pakai **pdflatex + bibtex** (bukan xelatex + biber
seperti TA), karena `ieeeaccess.cls` (lihat di bawah) hanya tersedia lewat mirror pihak ketiga
yang dites dengan toolchain BibTeX klasik.

## `ieeeaccess.cls` tidak ada di CTAN

Diunduh dari mirror `Larry955/Latex-Paper-Templates` di GitHub (beserta `logo.png`,
`notaglinelogo.png`, `bullet.png`). `IEEEtran.cls` (kelas induk) tersedia normal lewat MiKTeX,
tapi repositori paket default MiKTeX (`mirror.unpad.ac.id`) sempat menolak (403) — kalau
`mpm --install=ieeetran` gagal, ganti mirror dulu:
```powershell
mpm --set-repository="https://ctan.math.illinois.edu/systems/win32/miktex/tm/packages/"
```

Font resmi IEEE Access (Formata, Giovanni) tidak ikut di mirror ini — compile tetap jalan,
LaTeX cuma mengganti ke font default dengan warning, bukan error.

## Bug kelas yang ditemukan (dan cara kerjanya di sini)

Mirror `ieeeaccess.cls` yang dipakai punya tiga bug/gotcha nyata, semuanya sudah ditambal di
preamble kedua `paper_*.tex` — **jangan dihapus** kalau meng-copy preamble ke dokumen lain:

1. **`\usepackage{graphicx}` wajib ditambahkan manual.** Kelas ini hanya memuat `graphics.sty`
   polos (lewat dependensi `color`), padahal kode internalnya sendiri memakai sintaks
   `\includegraphics[width=...]` bergaya key-value yang cuma dipahami `graphicx`. Tanpa baris
   ini, compile gagal total di `\begin{abstract}` (macro `\Gin@iii` error).
2. **`\newcounter{biography}` dan flag `\newif\if@biographyTOCentrynotmade` tidak pernah
   dideklarasikan** oleh kelas maupun `IEEEtran.cls`, padahal dipakai di lingkungan
   `biographynophoto`. Dideklarasikan manual di preamble.
3. **`\xfigwd` (dipakai `\@makecaption` untuk memilih gaya caption gambar) tidak pernah diisi**
   kecuali lewat makro `\Figure` bawaan kelas yang tidak dipakai di sini (dipakai `figure`/
   `figure*` biasa). **Set selalu ke `0pt` tepat sebelum tiap `\caption`** — ini memaksa cabang
   caption pendek yang membungkus dengan benar mengikuti `\hsize` konteks saat itu. **Jangan**
   pakai cabang "lebar" (`\xfigwd` besar): cabang itu memakai tabular satu baris tanpa
   pembatas lebar sehingga caption panjang meluber diam-diam melewati margin halaman tanpa
   error apa pun — baru ketahuan dari `Overfull \hbox (133pt too wide) in paragraph` di log,
   bukan dari kegagalan compile. Ditemukan pertama kali di caption Gambar 1 versi EN.
4. **`\EOD` wajib diletakkan di akhir paragraf terakhir dokumen** (di sini: akhir biografi
   kedua) — simbol bullet putar 90° khas IEEE Access. Tanpa ini, `\end{document}` gagal dengan
   `Class ieeeaccess Error: You have not used the command \EOD`.

## Penyimpangan gaya yang disengaja

Versi ID pakai **desimal koma** (0,7089), bukan titik seperti kaidah IEEE Access asli. Ini
disengaja: dokumen ID bukan artikel IEEE Access yang sah (IEEE Access berbahasa Inggris),
melainkan artefak kampus yang meniru tata letaknya, dan koma dipakai supaya angkanya bisa diadu
langsung dengan Bab VI/VII laporan TA oleh penguji. Versi EN pakai titik sesuai kaidah asli.

## Struktur paper

### Versi ID (4 halaman, 5 seksi)

Karena batas 4–6 halaman jauh lebih ketat dari artikel IEEE Access biasa (lazim 10–15 halaman),
struktur dipadatkan dari rencana awal: *Related Work* dilebur jadi satu paragraf di Pendahuluan
(bukan seksi sendiri), *Results* dan *Discussion* digabung. Delapan gambar di TA dipadatkan jadi
2 (arsitektur sistem + dampak ablasi), tujuh tabel dipadatkan jadi 2 (perbandingan tiga sistem +
ablation study).

### Versi EN (6 halaman, 6 seksi)

Diperluas dari versi 4 halaman di sesi terpisah, memakai kuota halaman penuh. *Related Work*
dipisah jadi seksi tersendiri (I. Introduction, **II. Related Work**, III. System Design,
IV. Evaluation Setup, V. Results and Discussion, VI. Conclusion), dan seksi V punya dua subbab
tambahan plus satu subbab yang diperluas:

- **V-C Traversal Depth Sensitivity** — TABLE III + **Fig. 3** (baru), skor lengkap $d{=}1..5$
- **V-D Boundary Conditions** — TABLE IV (baru), RetQ-gain per kategori *fixture* + korelasi Spearman
- **V-E Discussion: Faithfulness** — diperluas dengan dekomposisi 818 klaim (*supported*/
  *modality*/*partial*/*absent*), bukan sekadar disebut "~56%" seperti di versi ID
- §IV juga diperluas: distribusi $n$ per kategori *fixture*, dan satu paragraf validasi pakar
  atas jawaban sistem (skor *Retrieval Trace* dan skenario relasi)

Hasil akhir versi EN: **3 gambar, 4 tabel, 21 referensi** (versi ID: 2 gambar, 2 tabel,
21 referensi — TABLE III/IV dan Fig. 3 **tidak punya padanan versi Indonesia**).

Kedua versi memakai referensi yang sama (`refs.bib`, 21 entri, dipangkas dari 27 entri TA).

### Gambar arsitektur (Fig. 1, kedua versi)

**Digambar ulang dari nol** sebagai diagram D2 ringkas dan mendatar — `c4_architecture.png` asli
di TA berukuran 4269×7233 piksel (potret, untuk satu halaman A4 utuh) sehingga tidak muat di
anggaran halaman paper ini. Sumber D2 ada di `diagrams/` (`fig1_architecture_id.d2`,
`fig1_architecture_en.d2`), dirender lewat Kroki (D2→SVG) + Chrome headless (SVG→PNG 600 dpi),
dipotong whitespace pakai PIL. Gambar ablasi (Fig. 2) dipakai apa adanya dari
`docs/TA-STI-template-1.0/images/eval_ablation_impact.png` (sudah berlabel Inggris).

### Fig. 3 (Traversal Depth Sensitivity, hanya versi EN)

`docs/TA-STI-template-1.0/images/depth_sensitivity_aggregate.png` **tidak bisa dipakai**: seluruh
labelnya Bahasa Indonesia (judul, sumbu, anotasi "default (d = 2)"), resolusinya cuma 150 dpi,
dan skrip pembuatnya sudah hilang dari `scripts/` (`grep depth_sensitivity_aggregate` di seluruh
`scripts/` nihil). Digambar ulang dari nol via skrip matplotlib sekali pakai (disimpan di
scratchpad sesi, bukan di repo), memakai 15 angka TABLE III yang di-*hardcode* dari
`docs/TA-STI-template-1.0/tables/tabel-depth.tex` dan sudah diverifikasi cocok dengan
`18222001-JIHAN AURELIA-LaporanTA.pdf` baris 3970–3981. Hasilnya `figures/en/fig3_depth.png`,
300 dpi. Tidak ada varian ID.

## Padanan label ablasi (TA vs. paper, kedua versi)

Dua label di TABLE II ditulis ulang lebih deskriptif dan **tidak identik teks dengan TA**,
meski merujuk konfigurasi yang sama persis:

| TA (`tabel32.tex`) | Paper | Alasan |
|---|---|---|
| `A1 no_phase1` | `A1 no_exact_match` | Fase 1 pada TA memang tahap *exact match*; label paper menjelaskan komponennya, bukan nomor fasenya |
| `A7 HAS_PROP only` | `A7 1 edge type` (ID: `1 tipe edge`) | Konfigurasi ini menyisakan tepat 1 tipe *edge* (`HAS_PROPERTY`) menggantikan 18 tipe *baseline* |

Angka pada kedua baris (ΔAnsQ, ΔRetQ, ΔHopAcc) sama persis dengan TA; hanya label kolom pertama
yang ditulis ulang.

## Berkas

```
paper_id.tex, paper_en.tex     — dokumen utama
table1_id.tex, table1_en.tex   — TABLE I (perbandingan 3 sistem), per bahasa (desimal beda)
table2_id.tex, table2_en.tex   — TABLE II (ablation study), per bahasa
table3_en.tex, table4_en.tex   — TABLE III (depth) & IV (boundary), HANYA versi EN
refs.bib                       — 21 entri, dipakai bersama kedua versi
ieeeaccess.cls + *.png         — kelas + aset, diunduh dari mirror GitHub
figures/id/                    — Fig. 1 & Fig. 2 versi ID
figures/en/                    — Fig. 1, Fig. 2 & Fig. 3 versi EN
diagrams/                      — sumber .d2 dan .svg untuk Fig. 1 (kedua versi)
```

## Catatan integritas

Seluruh angka di paper ini diambil apa adanya dari Bab VI/VII laporan TA (RetQ F1, AnsQ, hop
accuracy, faithfulness, hasil ablation A1–A7, sensitivitas kedalaman $d{=}1..5$, RetQ-gain per
kategori, korelasi Spearman, dekomposisi 818 klaim, skor validasi pakar) — tidak ada eksperimen
baru dan tidak ada angka yang dihitung ulang. Setiap angka tambahan yang masuk saat perluasan ke
6 halaman sudah diaudit satu per satu terhadap teks `18222001-JIHAN AURELIA-LaporanTA.pdf`
(diekstrak via `pdftotext -layout`), bukan hanya terhadap berkas `.tex` perantara di
`docs/TA-STI-template-1.0/tables/`.

Temuan negatif tetap dilaporkan apa adanya: AnsQ GraphRAG tidak berbeda signifikan dari Vector
RAG ($p_{\text{Holm}}=0{,}067$ / $0.067$), faithfulness (0,31 / 0.31) mencerminkan desain
*open-book* sistem bukan kegagalan retrieval, dan (di versi EN) kedalaman traversal per-*fixture*
ternyata **bukan** prediktor keunggulan yang signifikan ($\rho=-0.082$, $p=0.414$).
