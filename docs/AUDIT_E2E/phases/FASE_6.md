# FASE 6 — Audit Bahasa

> Baca bersama `CHARTER.md` + `STATUS.md` + `STYLE_GUIDE.md`.

## Objektif

Menyisir seluruh dokumen ter-compile (kecuali Lampiran) untuk pelanggaran kaidah bahasa Indonesia akademik ITB dan mengangkat kualitas prosa ke level penulis ilmiah teknis profesional domain GraphRAG/LLM/Kubernetes. **Nol perubahan angka/klaim teknis.** Tiap perbaikan di-approve before → after sebelum di-apply.

## Cakupan file

- Bab I–VII (`Bab *.tex`)
- `5 Abstrak.tex`, `13 Daftar Simbol.tex`, `14 Daftar Singkatan.tex`
- Frontmatter prosa: `6 Kata Pengantar.tex`, `3 Pernyataan Orisinalitas.tex`, `4 Pernyataan Penggunaan AI.tex`, `2 Lembar Pengesahan.tex` (light pass; Kata Pengantar & Orisinalitas boleh "Saya")
- `tables/*.tex` — caption & catatan prosa (bukan angka/sel data)
- `listings/*.tex` — caption saja
- **DIKECUALIKAN:** Lampiran A/B/C/D/E, Daftar Isi/Gambar/Tabel/Persamaan/Listing (auto-generate)

## Kelas pelanggaran

| # | Kelas | Aturan |
|---|-------|--------|
| C1 | Pemisah desimal koma (`0{,}85` di math mode) | STYLE_GUIDE B.1 |
| C2 | Terminologi & italic konsisten (AnsQ/RetQ/ReaQ; edge *CAPS\_CASE*; istilah asing italic; *fixture*; resource K8s italic) | STYLE_GUIDE C |
| C3 | `di mana` sebagai relative pronoun | STYLE_GUIDE B.6 |
| C4 | Em-dash `---`/`—` di body → rewrite kontekstual | STYLE_GUIDE B.11 |
| C5 | Ejaan/konsistensi PUEBI; `sehingga`/`sedangkan` tak di awal kalimat; `di` depan dipisah; subjek hadir setelah keterangan; kalimat tak mulai angka | STYLE_GUIDE B.2–9 |
| C6 | Sitasi CMS `\parencite`/`\textcite`; nol kurung-ganda; nol orphan | STYLE_GUIDE D |
| C7 | Kalimat >50 kata → pertimbangkan pecah | STYLE_GUIDE F |
| C8 | Kohesi antar-paragraf (topic sentence, transisi, tak loncat topik) | STYLE_GUIDE F |
| C9 | Pasif berantai; nominalisasi berlebih; filler | STYLE_GUIDE F |
| C10 | Versi K8s `v1.30`; range angka en-dash `--`; referensi gambar/tabel bernomor | STYLE_GUIDE C, E |
| C11 | **Kualitas prosa**: diksi tepat, alur logis, ringkas, natural; angkat ke level penulis ilmiah teknis profesional; tanpa ubah makna/angka/klaim | arahan user + STYLE_GUIDE F |

## Progress per file

| File | Scan | Fix | Catatan |
|------|------|-----|---------|
| 5 Abstrak.tex | ✅ | ✅ | 2 fix: "skalar" → "nilai atribut" (×2) |
| Bab I | ✅ | ✅ | 2 fix: kluster → klaster (×2) |
| Bab II | ✅ | ✅ | 7 fix: sehingga/tetapi/antar-Pod/subjek/hallucination/presisi/klaster |
| Bab III | ✅ | ✅ | 8 fix: yaitu/spasi-URL/bisa→dapat/duplikat/redundan/per-empat-bulan/spasi-titik-dua |
| Bab IV | ✅ | ✅ | 4 fix: CRISP-DM/mencerminkan/dua-arah/misalnya |
| Bab V | ✅ | ✅ | 1 fix: swagger.json + v1.30; spasi \texttt{} panjang intentional |
| Bab VI | ✅ | ✅ | 23 fix: em-dash (×17), sehingga (×4), inheran, prompts.py, DAN, mengonfirmasi (×3) |
| Bab VII | ✅ | ✅ | 8 fix: swagger.json/klaster (×2)/diekspektasikan/field-italic/sehingga (×2)/mengonfirmasi/antarversi |
| Daftar Singkatan/Simbol | ✅ | ✅ | 1 fix: antarsistem; Daftar Singkatan bersih |
| Frontmatter prosa | ✅ | ✅ | Bersih (Kata Pengantar/Orisinalitas/AI/Lembar Pengesahan) |
| tables/*.tex | ✅ | ✅ | 8 fix: sehingga (×6), antarobjek, em-dash→karena (tabel36), em-dash-def (tabel29b) |
| listings/*.tex | ✅ | ✅ | Bersih (no captions in files) |

## Verifikasi pasca-fix (2026-06-28)

Grep nol-stale dijalankan atas semua file in-scope. Semua instance yang tersisa adalah:
- `% ---` komentar LaTeX → bukan body text
- `---` di sel data tabel (N/A marker) → out of scope per scoping rule
- Lampiran-C/E → dikecualikan sejak awal

**Status: BERSIH.** Nol pelanggaran bahasa tersisa di file in-scope.
