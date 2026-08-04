# FASE 7 — Whitespace & Keterbacaan PDF

> Baca bersama `CHARTER.md` + `STATUS.md`.

## Objektif

Perbaikan **lokal** tata letak PDF: overflow margin (`Overfull \hbox`), gap whitespace besar akibat float `[H]` yang terdorong ke halaman berikutnya, dan header "(lanjutan)" pada tabel multi-halaman. **Nol perubahan konten/angka/klaim.** `TA.tex` tetap read-only.

## Baseline (sebelum perbaikan)

- Compile bersih: 192 halaman, exit 0.
- `Overfull \hbox`: 242 total, 111 di antaranya >10pt (nyata, bukan kosmetik).
- Semua figur/tabel memakai spesifier `[H]` (kecuali 4 pengecualian `[htbp]` yang sudah ada).

## Jalur A — Overflow margin

**Metodologi:** parse `TA.log` per-baris via skrip PowerShell untuk memetakan tiap `Overfull \hbox` >10pt ke file:baris sumber. Dua bug dalam metodologi awal ditemukan dan dikoreksi saat proses:
1. Heuristik "file transient" (dibuka+ditutup di baris log yang sama) gagal ketika ada `[nomor-halaman]` di antara nama file dan tanda kurung tutup — menyebabkan atribusi salah ke file listing/tabel yang sebenarnya sudah tertutup. Dikoreksi dengan verifikasi silang teks snippet di log terhadap isi file kandidat.
2. Beberapa longtable (mis. `tables/tabel21.tex`) melaporkan nomor baris yang melebihi panjang filenya sendiri — ternyata proses pengukuran ulang lintas-halaman `longtable` membuat log sempat "kembali" ke konteks file luar (`Bab V - Implementasi.tex`). Diverifikasi via pembacaan konten mentah log di titik tersebut.

**Root cause dominan (≈90% kasus):** identifier/path teknis panjang dalam `\texttt{}`/`\textit{}` yang mengandung `_` atau `/` — karakter ini TIDAK otomatis jadi titik potong baris di LaTeX. Contoh: `src/ingestion/parser.py`, `x-kubernetes-group-version-kind`, `HAS_PROPERTY`, `deployment_vs_statefulset_comparison`. Fix: sisipkan `\allowbreak{}` setelah `_`/`-` bermakna, atau ganti `/` literal dengan `\slash` (macro LaTeX yang identik secara visual tapi mengizinkan potong baris). Kedua teknik ini **tidak mengubah karakter yang terlihat di PDF**, hanya menambah izin potong baris.

**Root cause kedua:** dua tabel (`Lampiran-Data.tex` skema edge, `Lampiran-B.tex` ringkasan fixture) punya jumlah lebar kolom `p{}` yang melebihi textwidth efektif (setelah dikurangi `\tabcolsep`) — diperbaiki dengan menyempitkan kolom yang longgar.

**Kasus keras kepala:** beberapa paragraf tetap overflow meski sudah diberi `\allowbreak{}`, karena algoritma Knuth-Plass kadang memilih membiarkan satu baris overflow ketimbang memakai titik potong yang tersedia (jika alternatifnya dianggap "lebih buruk" secara keseluruhan paragraf). Untuk kasus ini dipakai `\begin{sloppypar}...\end{sloppypar}` (idiom LaTeX standar, melonggarkan `\tolerance` hanya untuk paragraf tersebut).

**Hasil:** 111 → 13 kasus >10pt (242 → 96 total overfull).

## Jalur B — Header "(lanjutan)" tabel multi-halaman

Diverifikasi seluruh `longtable` di dokumen. Ditemukan `Lampiran-Data.tex` (tabel skema 18 tipe edge, memang terbukti terpotong ke beberapa halaman via `TA.log`) tidak punya baris "(lanjutan)" pada `\endhead`, tidak konsisten dengan pola yang sudah baku di semua longtable lain (`tabel21.tex` dkk). Ditambahkan header "(lanjutan)" + footer "bersambung ke halaman berikutnya", meniru pola existing persis. `13 Daftar Simbol.tex`/`14 Daftar Singkatan.tex` diverifikasi muat 1 halaman (tak ada page-break di dalamnya) — tidak perlu "(lanjutan)".

## Jalur C — Gap whitespace dari float `[H]`

**Metodologi:** render PDF ke PNG per-halaman via `pdftoppm` (bundel MiKTeX, dipanggil langsung — Read tool tidak mendeteksinya otomatis) lalu diperiksa visual. ~90/192 halaman diperiksa: seluruh Bab IV–VI (paling padat figur/tabel) + sampel representatif Bab II/III. Pola yang ditemukan: `\raggedbottom` + `floatrow` fraction settings di `TA.tex` sudah bekerja baik untuk mayoritas halaman — masalah hanya muncul saat sebuah figur/tabel `[H]` tidak muat sisa halaman dan terdorong **utuh** ke halaman berikutnya, menyisakan gap 35–55% di halaman sebelumnya.

**5 kandidat ditemukan dan diajukan ke user (HARD GATE, wajib approval sebelum eksekusi):**

| # | Lokasi | Elemen | Keputusan user |
|---|--------|--------|-----------------|
| 1 | `Bab IV - Perancangan.tex:289` | Gambar IV.5 (`Seq-High.png`) | ✅ Diterapkan `[H]`→`[htbp]` |
| 2 | `Bab IV - Perancangan.tex:379` | Tabel IV.5 (`tabel-perbandingan-sistem.tex`) | Tidak diubah langsung — dicek efek samping dari #1 |
| 3 | `Bab VI - Evaluasi.tex:81` | Tabel VI.3 (`tabel31.tex`) | ❌ Tidak diterapkan (keputusan user) |
| 4 | `Bab VI - Evaluasi.tex:149` | Tabel VI.8 (`tabel29c.tex`) | ❌ Tidak diterapkan (keputusan user) |
| 5 | `Bab VI - Evaluasi.tex:208` | Gambar VI.6 (`eval_faith_vs_ansq_scatter.png`) | ❌ Tidak diterapkan (keputusan user) |

**Hasil #1:** setelah `[htbp]` diterapkan pada item #1 dan recompile, gap #1 hilang (halaman terisi penuh) **dan** gap #2 ikut hilang sebagai efek samping reflow — Tabel IV.5 kini muat di halaman yang sama dengan paragraf pengantarnya, tanpa perlu mengubah float-nya sendiri. Dikonfirmasi via render ulang PNG kedua halaman terkait. Item #3–5 sengaja dibiarkan `[H]` sesuai keputusan eksplisit user.

**Item ke-6 (susulan, ditemukan user pasca-laporan awal, KEMUDIAN DIBATALKAN):** halaman 59 (tercetak) masih menyisakan gap ~55% — ini SEBENARNYA sudah teridentifikasi saat inspeksi visual awal (dicatat sebagai "~40% blank" untuk area V.2/V.2.1) tapi kelewat masuk ke tabel 5-kandidat yang diajukan (oversight saat merangkum, bukan temuan baru). Root cause identik: Gambar V.2 (`Pass1.png`, `Bab V - Implementasi.tex:46`) terdorong utuh ke halaman berikutnya. Diajukan terpisah ke user setelah ditemukan → disetujui → `[H]`→`[htbp]` diterapkan → gap hilang, **tapi memunculkan regresi baru**: Tabel V.2 (`tables/tabel-kategori-edge.tex`, `table[H]` biasa — bukan `longtable`, tidak bisa pecah antar-halaman) yang mengikuti Gambar V.2 kehabisan ruang di halaman yang sama dan **overflow melewati margin bawah** (nomor halaman tertindih teks tabel, baris terakhir terpotong). Terlihat jelas via render ulang PNG. User diberi 2 opsi (ubah tabel juga ke `[htbp]`, atau revert Gambar V.2) → **user pilih revert**. Gambar V.2 dikembalikan ke `[H]` (diverifikasi via `git diff` = nol perubahan bersih untuk figur ini). Gap halaman 59 kembali muncul (diterima sebagai residual, sama seperti item #3–5) tetapi tanpa risiko regresi. Pelajaran: mengubah `[H]`→`[htbp]` pada SATU float bisa mendorong float `[H]` berikutnya ke situasi tanpa ruang cukup — perlu cek float TEPAT SESUDAHNYA juga, bukan cuma float yang diubah.

## Residual (didokumentasikan, bukan diabaikan)

13 kasus overflow >10pt tersisa, semua di luar kemampuan Fase 7 untuk diperbaiki bersih tanpa melanggar guardrail:
- **5 kasus** di daftar pustaka (`\printbibliography`, `TA.tex:478`) — justified text badness pada judul jurnal panjang. `TA.tex` read-only mencegah fix global (`\sloppy` sebelum `\printbibliography`); mengedit field `.bib` untuk alasan tipografi murni dianggap berisiko tanpa konfirmasi terpisah (menyentuh data bibliografi).
- **3 kasus** caption di List-of-Figures/Tables/Listings — lebar kolom daftar ini diatur oleh mekanisme `tocloft`/`\listoffigures` bawaan di `TA.tex` (read-only); caption sudah benar di badan dokumen, hanya versi ringkas di daftar yang sedikit sempit.
- **4 kasus** "blank content" artefak rounding batas tabel (`tabel27.tex`, `tabel29b.tex`, `Lampiran-E.tex`) — tidak ada teks terlihat yang overflow, murni noise pengukuran kotak tabel, tidak berdampak visual.

## Verifikasi akhir

- Compile bersih (`xelatex → biber → xelatex → xelatex`, PATH di-scrub dari `supabase`): 192 halaman, exit 0, nol baris `! ` fatal.
- Overflow >10pt: 111 → 13 (89% reduksi); total overfull 242 → 96 (60% reduksi).
- `git diff` per-file diverifikasi manual: seluruh perubahan berupa `\allowbreak{}`, `\slash`, `\begin{sloppypar}`/`\end{sloppypar}`, lebar kolom `p{}`, atau spesifier float (`[H]`→`[htbp]`) — nol perubahan angka, kalimat, atau klaim teknis. Kasus ekstrem: `Lampiran-C.tex` (306 baris berubah, seluruhnya diverifikasi via skrip diff-pairing hanya berbeda oleh sisipan `\allowbreak{}`).
- Inspeksi visual PNG sebelum/sesudah untuk kedua halaman yang terkait perubahan float (#1 dan #2).

## File tersentuh

`13 Daftar Simbol.tex`, `14 Daftar Singkatan.tex`, `4 Pernyataan Penggunaan AI.tex`, `5 Abstrak.tex`, `Bab II - Studi.tex`, `Bab III - Analisis.tex`, `Bab IV - Perancangan.tex`, `Bab V - Implementasi.tex`, `Bab VI - Evaluasi.tex`, `Lampiran-B.tex`, `Lampiran-C.tex`, `Lampiran-Data.tex`, `tables/tabel33.tex`, `tables/tabel33b.tex`. (`tables/tabel-kategori-edge.tex` sempat diusulkan untuk item #6 tapi TIDAK disentuh — user pilih revert alih-alih ubah tabel ini.)

## Next

**Fase 8** — Compile final & verifikasi (mock penguji, cross-check angka tesis vs CSV final, nol mismatch).
