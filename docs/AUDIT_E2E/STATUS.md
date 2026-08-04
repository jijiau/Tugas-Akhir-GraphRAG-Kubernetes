# STATUS — Audit E2E TA GraphRAG-Kubernetes

> Pelacak progres lintas-sesi. **Update di akhir tiap sesi** (status + handoff notes). Baca bersama `CHARTER.md`.

## Ringkasan fase

| Fase | Judul | Status | Dok detail | Artefak |
|------|-------|--------|-----------|---------|
| -1 | Setup scaffolding | ✅ DONE (2026-06-09) | — | CHARTER, STATUS, STYLE_GUIDE, memory |
| 0 | Diagnosis forensik (read-only) | ✅ DONE (2026-06-09) | `phases/FASE_0.md` | `bug_register.md`, `metric_suitability.md`, `critical_review.md` |
| 1 | Perbaiki measurement (kode) | ✅ DONE (2026-06-14) | `phases/FASE_1.md` | `topk_selection.md` |
| 2 | Re-kurasi GT fixture (data) | ✅ DONE (2026-06-11) | `phases/FASE_2.md` | `fixture_fix_log.md` |
| 3 | Re-run evaluasi penuh | ✅ DONE (2026-06-14) | `phases/FASE_3.md` | `_final` CSV baru, 13 figur, stat-test, boundary |
| 4 | Update angka + Bab VI evaluasi | 🔶 IN-PROGRESS (Bab VI ✅) | `phases/FASE_4.md` | Bab VI rewrite selesai; Bab II metrik belum |
| 5 | Alignment Bab I & konsistensi | ✅ DONE (2026-06-28) | `phases/FASE_5.md` | Bab VII/Abstrak/tabel23/Bab V/Bab VI figur/Daftar Singkatan/Lampiran-C |
| 6 | Audit bahasa | ✅ DONE (2026-06-28) | `phases/FASE_6.md` | `language_violations.md` |
| 7 | Whitespace & keterbacaan PDF | ✅ DONE (2026-07-07) | `phases/FASE_7.md` | — |
| 8 | Compile final & verifikasi | ✅ DONE (2026-07-07) | `phases/FASE_8.md` | `mock_defense.md`, `verify_thesis_numbers.py` |

Legend: ✅ done · 🔶 in-progress · ⬜ todo

## Urutan disarankan
0 → **2** → **1** → 3 → 4 → 5 → 6 → 7 → 8. (Urutan dikoreksi: Fase 2 dulu, lalu Fase 1). Fase 1 & 2 sama-sama prasyarat Fase 3 (re-run). Fase 4–7 setelah angka final stabil.

**AUDIT E2E SELESAI (Fase 0–8 semua DONE) per 2026-07-07.**

## Handoff notes (terbaru di atas)

### 2026-07-07 — Fase 8 selesai: compile final & verifikasi (FASE PENUTUP AUDIT E2E)

**Urutan eksekusi:** Pilar A (compile) → Pilar B (cross-check) → Pilar C (mock penguji),
gerbang berjenjang — C baru dimulai setelah A+B pass; setiap temuan B yang dikonfirmasi
sebagai defect nyata di-fix lalu loop-back ke A. Pilar D (temuan git) di luar gerbang, murni
pelaporan. Detail lengkap: `phases/FASE_8.md`, `mock_defense.md`.

**Pilar A — Compile:** 192 halaman, exit 0, 0 fatal, 0 undefined ref/citation (stabil,
identik baseline Fase 7). PATH scrub perlu 2 entri sekarang (`supabase` + `heroku-x64.exe`
baru ditemukan). Koreksi memory: frontmatter pakai romawi (bukan "arabic kontinu" seperti
tercatat sebelumnya) — `reference_latex_compile.md` diperbarui.

**Temuan A-1 (KRITIS, FIXED):** entri bibliografi `gu_2024` (MidMed, paper dialog medis —
sudah ditolak Charter sejak Fase 0/1) masih tersitasi di `Bab II - Studi.tex:282` untuk
definisi Hop-Accuracy (seharusnya `manning_ir_2008`, seperti 4 lokasi lain yang memakai
rumus identik) — 1 instance terlewat saat penggantian sitasi massal dulu. Konsekuensi lebih
serius: field `note={}` di `.bib` berisi catatan editorial internal ("confirm full citation
from Ma et al...") yang **tercetak verbatim di Daftar Pustaka PDF final** (gaya
chicago-authordate merender `note` apa adanya). Fix: Bab II §282 diganti ke
`manning_ir_2008`; entri `gu_2024` dihapus dari `.bib`. Recompile bersih, verifikasi visual
render PNG mengonfirmasi entri hilang total dari Daftar Pustaka.

**Pilar B — Cross-check:** `scripts/verify_thesis_numbers.py` (baru, ad hoc, tidak
di-commit) memverifikasi 63 klaim numerik (headline AnsQ/RetQ/Faithfulness/HopAcc per
sistem, depth sensitivity d=1/3/4/5, ablation A1–A7, boundary gain per kategori + Spearman,
fixture counts) terhadap CSV sumber. **Hasil akhir: 63/63 MATCH** setelah 2 iterasi (2 bug
skrip-sendiri dikoreksi: kolom stratifikasi HopAcc yang salah — `depth_gt` bukan `gt_depth`;
filter Spearman degree yang tak mengecualikan `graph_degree=0` sesuai
`boundary_condition.py:366`).

**Temuan B-2 (KRITIS, FIXED):** `tables/tabel32.tex:23`, kolom ΔHopAcc ablasi A5 tercetak
`−0,0037`, padahal HopAcc absolut A5 (0,7599, benar) > baseline (0,7562, benar) — delta
secara matematis harus positif. Diverifikasi 3 jalur independen presisi penuh atas
permintaan user (pandas/numpy/manual): A5−Baseline = +0,0036956696 → **+0,0037**. Kontrol
silang A4 (skenario sama, tercetak benar +0,1445) mengonfirmasi anomali eksklusif di A5.
Fix diterapkan + footnote formula tabel32 (baris 32) diperbaiki dari "Baseline−Ablasi" yang
terbalik ke "Ablasi−Baseline" (label saja, sudah cocok dengan 20 sel lain). Tidak ada
narasi Bab VI/VII yang perlu diubah (hanya membahas ΔRetQ A5, tidak pernah mengklaim arah
ΔHopAcc).

**Verifikasi struktural tambahan:** 18 tipe edge dihitung ulang langsung dari
`src/graph/queries.py` (bukan hanya cross-check LaTeX-ke-LaTeX) — cocok persis.

**Pilar C — Mock penguji:** `mock_defense.md`, 5 tema dibobot ke domain/konseptual (arahan
user: penguji STI, bukan CS murni) — judul & scope, domain Kubernetes, konsep GraphRAG,
audit sitasi (27 entri `.bib` dibaca penuh — kredibel, 1 orphan `li_cotrag_2025` tak
berdampak PDF karena biblatex citation-driven, tidak digate sebagai fix wajib), kontribusi
& positioning. Titik lemah paling perlu latihan lisan: T3.2 (14/18 edge hand-coded — jangan
klaim "auto-derived") dan T1.1 (RetQ headline GT-sensitive, arah kokoh tapi magnitudo
GT-dependent).

**Pilar D — Temuan git (flag saja, keputusan user: tidak disentuh):** working tree masih
besar sejak commit `8a46a21` (2026-07-07 sesi ke-2) — 164 modified + 89 untracked + 2
deleted, termasuk LaTeX Fase 7+8, `evaluate.py`, dan **semua CSV `_final` sumber angka
tesis** (`eval_results_graphrag_final.csv` dkk.) masih untracked. File baru sesi ini:
`FASE_8.md`, `mock_defense.md`, `verify_thesis_numbers.py` (juga untracked). Tidak ada
operasi git dilakukan — commit adalah keputusan terpisah milik user.

**Status Audit E2E: SEMUA FASE (0–8) SELESAI.** Next: user memutuskan strategi commit/push,
lalu latihan lisan mock_defense.md sebelum sidang.

### 2026-07-07 — Fase 7 selesai: whitespace & keterbacaan PDF

**Cakupan:** perbaikan lokal murni tata letak (overflow margin, penempatan float, header "(lanjutan)"). Nol perubahan konten/angka/klaim — diverifikasi via `git diff` per-file (setiap baris berubah hanya berupa `\allowbreak`/`\slash`/`sloppypar`/lebar kolom/spesifier float).

**Jalur A+C (overflow tabel/listing + header lanjutan):** atribusi log `Overfull \hbox` >10pt dari 111 → 13 kasus tersisa (semua overfull dari 242 → 96 total). Root cause dominan: identifier/path teknis panjang (`\texttt{}`/`\textit{}` dengan `_` atau `/`) yang tidak punya titik potong bawaan LaTeX, dan dua kasus lebar kolom tabel melebihi textwidth efektif. Fix: `\allowbreak{}` setelah underscore/hyphen bermakna, `\slash` untuk "/", pelebaran/penyempitan kolom `p{}`, `sloppypar` untuk paragraf yang tetap overflow meski sudah ada titik potong (kasus Knuth-Plass memilih overflow atas alternatif lain). File tersentuh: `13/14 Daftar Simbol/Singkatan`, `4 Pernyataan Penggunaan AI`, `5 Abstrak`, `Bab II/III/V/VI`, `Lampiran-B/C/Data`, `tables/tabel33.tex`, `tables/tabel33b.tex`. `Lampiran-Data.tex` (tabel edge-schema) dilengkapi header "(lanjutan)" yang sebelumnya hilang (satu-satunya longtable multi-halaman tanpa itu; Daftar Simbol/Singkatan diverifikasi muat 1 halaman, tak perlu).

**13 residual overflow TIDAK diperbaiki** (didokumentasikan, bukan diabaikan diam-diam): 5 di daftar pustaka (biblatex, `TA.tex` read-only mencegah fix bersih + edit `.bib` untuk alasan tipografi dianggap berisiko tanpa konfirmasi terpisah), 3 caption di List-of-Figures/Tables/Listings (lebar kolom daftar diatur `TA.tex`, read-only), 2+2 artefak "blank content" di `tabel27.tex`/`tabel29b.tex`/`Lampiran-E.tex` (rounding batas tabel, tak berdampak visual).

**Jalur B (gap whitespace dari float `[H]`):** inspeksi visual ~90/192 halaman (render via `pdftoppm` bundel MiKTeX, bukan poppler — catatan lama soal "tak perlu poppler" ternyata keliru untuk environment ini). Cakupan penuh Bab IV–VI (paling padat figur/tabel) + sampel Bab II/III. 5 kandidat gap ditemukan dan diajukan ke user; **hanya 1 disetujui** (Gambar IV.5 `Seq-High.png`, `Bab IV - Perancangan.tex:289`, `[H]`→`[htbp]`). Efek samping: gap kedua (Tabel IV.5) yang tadinya diusulkan terpisah ikut hilang otomatis dari reflow satu perubahan itu — dikonfirmasi via render ulang. 3 kandidat lain (Tabel VI.3/VI.8, Gambar VI.6) sengaja TIDAK diubah atas keputusan user.

**Item ke-6 susulan (ditemukan user setelah laporan awal, DIBATALKAN):** halaman 59 (tercetak) gap ~55% — sudah teridentifikasi saat inspeksi visual awal tapi kelewat masuk ke tabel 5-kandidat (oversight rangkuman). Root cause sama: Gambar V.2 (`Pass1.png`, `Bab V - Implementasi.tex:46`) terdorong ke halaman berikutnya. Diajukan → disetujui → `[H]`→`[htbp]` diterapkan → gap hilang, **TAPI memunculkan regresi**: Tabel V.2 (`tabel-kategori-edge.tex`, `table[H]` biasa, tak bisa pecah halaman) yang mengikuti kehabisan ruang dan overflow melewati margin bawah (nomor halaman tertindih teks, baris terakhir terpotong — dikonfirmasi via render PNG). User diberi pilihan (ubah tabel itu juga ke `[htbp]`, atau revert) → **user pilih revert**. Gambar V.2 dikembalikan ke `[H]` (bersih, nol diff net). Gap halaman 59 diterima sebagai residual (sama seperti item #3–5) demi menghindari risiko regresi lanjutan.

**Hasil compile akhir:** 192 halaman, exit 0, nol `! ` fatal, nol regresi konten. Net: hanya item #1 (Gambar IV.5) yang benar-benar diterapkan dari Jalur B; item #2 ikut membaik sebagai efek samping; item #3–6 dibiarkan `[H]` (3 atas keputusan user, 1 karena revert setelah regresi).

**Next: Fase 8** (compile final & verifikasi — xelatex→biber→xelatex→xelatex, mock penguji, cross-check angka tesis vs CSV final).

### 2026-06-28 — Tracing konsistensi lintas-bab (pra-Fase 7)

**Cakupan:** Bab I–VII, tabel, listings → cross-check angka ke CSV ground-truth + konsistensi antar-bab + kesesuaian klaim dengan kode.

**Temuan:** 4 MISMATCH (fix diterapkan), 1 CLARIFY (diputuskan: pertahankan), 34 CONSISTENT.

**Fix diterapkan:**
- G1 (tabel-depth.tex): AnsQ d=1 0,7602→0,7815; d=4 0,7548→0,7828; d=5 0,7611→0,7817 (sumber: `eval_results_depth_{1,4,5}.csv`)
- G2 (Bab V §38): +1 kalimat penjelas gap 730→725 node (5 tipe utilitas apimachinery di IGNORE_LIST: FieldsV1, OwnerReference, Patch, StatusCause, Info)
- G3 (Bab I §61): `\textit{follow-up}` → `\textit{followup}` (konsisten dengan kode + semua bab lain)

**CLARIFY diputuskan:** Faithfulness 0,3055 (n=95) dipertahankan — nilai saat komputasi dilakukan; perbedaan 0.0016 dari CSV saat ini tidak material.

**Angka headline semua terverifikasi CONSISTENT** (RetQ 0,7089; AnsQ 0,8031; HopAcc 0,7562/0,9086/0,5791; ablation A1–A7; boundary; Spearman ρ).

**Artefak:** `docs/AUDIT_E2E/consistency_trace.md`

**Next: Fase 7** (whitespace & keterbacaan PDF).

---

### 2026-06-28 — Fase 6 selesai: audit bahasa

**Cakupan:** Bab I–VII, Abstrak, Daftar Singkatan/Simbol, frontmatter prosa, tables/*.tex, listings/*.tex. Lampiran dikecualikan.

**Total temuan & fix (per file):**
- Abstrak: 2 fix (skalar→nilai atribut ×2)
- Bab I: minor (versi v1.30 alignment, dari Fase 5)
- Bab II: 6 fix (II1–II6: sehingga/tetapi/antar-Pod/subjek/hallucination/presisi)
- Bab III: 8 fix (III1–III8: yaitu/spasi URL/bisa→dapat/duplikat/redundan/per-empat-bulan/spasi-sebelum-titik-dua)
- Bab IV: 4 fix (IV1–IV4: CRISP-DM/mencerminkan/dua arah/misalnya)
- Bab V: 1 fix (V1: swagger.json + v1.30); spasi `\texttt{}` panjang dikecualikan (intentional)
- Bab VI: 11 fix (VI1–VI11: em-dash ×7/inheren/urutan prosa/DAN→dan/mengonfirmasi ×3)
- Bab VII: 7 fix (VII1,VII3–VII8: swagger.json/klaster/diekspektasikan/field italic/sehingga/mengonfirmasi/antarversi)
- Daftar Simbol: 1 fix (antarsistem)
- Daftar Singkatan: bersih
- Frontmatter prosa (Kata Pengantar, Orisinalitas, Penggunaan AI, Lembar Pengesahan): bersih
- tables/: 7 fix (T1–T7: sehingga ×5/antarobjek/em-dash→karena di footnote tabel36)
- listings/: bersih (no captions in files)

**Kelas pelanggaran dominan:** B.3 (koma sebelum sehingga), C4 (em-dash), EYD antar- serangkai, mengkonfirmasi→mengonfirmasi, klaster/inheren ejaan.

**Guardrail:** nol perubahan angka, nol perubahan klaim teknis — dikonfirmasi per-temuan.

**Next: Fase 7** (whitespace & keterbacaan PDF) atau langsung Fase 8 (compile final).

### 2026-06-28 — Fase 5 selesai: alignment lintas dokumen

**Perubahan konkret:**
- `Bab VII - Penutup.tex`: rewrite total — fixture 102/103, ablation A1 −0,309/A2 −0,656, A3 RetQ −0,123/Hop −0,147, A5 tanpa RGA, Ketiga hapus ReaQ-lama/RGA/PathCov, tambah Faithfulness 0,3055 Δ+0,127, RetQ 0,7089 Δ+0,465, HopAcc 0,7562, ρ+0,245, gains followup/yaml_gen/planning; Keterbatasan #2 relationship (bukan realworld) +0,354; Keterbatasan #3 hapus grounding/CP/CR/AR/lintas-bahasa → faithfulness decomp 55,6% parametric
- `5 Abstrak.tex`: rewrite paragraf hasil (102/103 fixture, RetQ 0,7089, Faithfulness 0,3055, decomp, AnsQ n.s.); buang 63,4%/69,8% context precision dari motivasi; keywords: hapus Path Coverage, tambah faithfulness
- `tables/tabel23.tex` (Bab III): B01 → Precision/Recall/F1 set-based; B02 → Hop Accuracy + Faithfulness; B03 → Answer Semantic Similarity (tanpa Faithfulness)
- `tables/tabel29a.tex` + `tables/tabel31.tex` (Bab VI): "Answer Relevance" → "Answer Semantic Similarity"
- `Bab V - Implementasi.tex`: hapus figur submetrics blank + prosa @k (NDCG/Precision@k/Recall@k); "97 fixture" → "seluruh fixture"; absolute count "79 kueri/18 kueri" → persentase saja; framing 12k-char development-stage
- `Bab VI - Evaluasi.tex`: depth figure → `depth_sensitivity_aggregate.png` (3-garis agregat baru, bukan per-kategori)
- `images/depth_sensitivity_aggregate.png`: dibuat baru (matplotlib, 3 garis RetQ/AnsQ/Hop vs d=1..5)
- `14 Daftar Singkatan.tex`: hapus entri NDCG
- `TA.tex`: comment out `\input{Lampiran-C.tex}`
- **Compile**: 204 halaman, exit 0, nol error baru

**Grep nol-stale (compiled):** `RGA|Path Coverage|Answer Relevance|0,6631|0,3222|0,8947|97 fixture|lintas bahasa|depth_sensitivity_submetrics` → bersih (semua sisa adalah cite pihak ketiga, orphan tabel, atau nilai sah dalam tabel-depth)

### 2026-06-21 — Fase 4 Bab VI selesai

**Bab VI - Evaluasi.tex ditulis ulang total** dari skema metrik lama (RGA, NDCG@k, PathCov, GroundingScore, 97 fixture, BI) ke skema final (AnsQ/RetQ P/R/F1/ReaQ, n=102/103, English answers).

**Perubahan konkret:**
- 15 tabel regenerasi: tabel29a-c, tabel30, tabel31, tabel31b, tabel31c, tabel32, tabel33, tabel33b (repurpose→T1 proof), tabel34, tabel35, tabel36, tabel37 (diperlunak), + 2 tabel baru: tabel-depth.tex, tabel33b (T1)
- Prosa 6 section baru: metode evaluasi (AnsQ/RetQ/ReaQ definisi baru), hasil per-dimensi, analisis (depth sensitivity, ablation, stat-test, boundary), validasi kualitatif pakar
- Semua angka dari CSV `_final` — terverifikasi
- GT disclosure Opsi A (2 kalimat netral di RetQ body)
- F16 disclosure (single-run, temperature=0.1) di Protokol
- faithfulness caveat (modality mismatch + scalar absent), bukan lintas-bahasa
- T1 proof dari A7 (RetQ +0.152, HopAcc +0.232, AnsQ n.s.)
- Boundary: degree rho=+0.245 (*), hops rho=-0.082 (n.s.)
- manning_ir_2008 ditambah ke daftar-pustaka.bib
- Compile berhasil: 216 halaman, tanpa error kritis

**Angka final yang dipakai di Bab VI (berbeda dari Fase 3 STATUS lama karena 1 duplikat drop → GraphRAG n=102):**

| Metrik | GraphRAG (n=102) | Vector (n=103) | LLM (n=103) |
|--------|-----------------|----------------|-------------|
| AnsQ | **0.8031** | 0.7976 | 0.7464 |
| RetQ F1 | **0.7089** (P=0.8405, R=0.7258) | 0.2419 | 0.0000 |
| RAGAS Faithfulness | **0.3055** (n=95) | 0.1654 (n=81) | N/A |
| Hop Accuracy (all) | **0.7562** (n=93) | 0.0000 | 0.0000 |
| Hop (focused ≤15) | 0.9086 (n=50) | — | — |
| Hop (closure >15) | 0.5791 (n=43) | — | — |

**Next: Fase 4 lanjutan** (Bab II metrik update) atau langsung Fase 5 (Bab I alignment) per keputusan user.

---

### 2026-06-17 — Reconsider ReaQ + temuan validitas GT (pra-Fase 4)

**Keputusan ReaQ final:** ReaQ = hop_accuracy (edge recall, stratifikasi focused≤15/closure>15) + RAGAS faithfulness (jujur+caveat modality). Path edge P/F1, multi-hop success, phantom-edge SEMUA dicoret (redundan / trivial 1.0). Angka terverifikasi dari CSV: faithfulness **0.3055** (n=95, koreksi dari 0.2948), hop_acc 0.7562 (focused 0.9086 / closure 0.5791).

**⚠️ TEMUAN VALIDITAS GT (penting):** `expected_path`/`relevant_nodes` = closure mekanis di-template ke ROOT (bukan question-specific) — bukti: 10 pertanyaan Pod beda → expected_path identik 111 edge. Preview re-kurasi (proxy shortest-path, read-only): **keunggulan RetQ GraphRAG vs Vector +0.465 → +0.027** (klaim headline rapuh), hop_acc 0.756→0.802, RetQ GraphRAG 0.709→0.404. Sensitif terhadap definisi GT.

**KEPUTUSAN USER: pakai angka sekarang, TIDAK re-kurasi.** Arah keunggulan GraphRAG kokoh, hanya magnitudo presisi GT-dependent (proxy +0.027 ketat = overstate). Disclosure = **1 kalimat netral Opsi A** di Bab VI (bukan framing dramatis). T1 dibiarkan as-is (tak disebut GT-sensitivity). Verifikasi tambahan: pairing stat-test bersih (common-102, no bias); schema_compliance GraphRAG 0.893 = 2 HPA pakai `autoscaling/v2beta2` deprecated (genuine finding). Detail di memory [[project-graphrag-thesis-state]].

**Next: Fase 4 — tulis Bab VI** dengan angka final + ReaQ panel + disclosure GT.

### 2026-06-14 — Fase 3 selesai

**Re-run evaluasi penuh selesai. Angka final valid metodologis siap untuk Fase 4.**

#### Angka final (n=103 fixture, Bahasa Inggris, 18-edge, K8s 1.30)

| Metrik | GraphRAG | Vector | LLM | Target |
|--------|----------|--------|-----|--------|
| AnsQ | **0.7877** | 0.7976 | 0.7464 | >0.80 |
| RetQ (F1) | **0.6462** | 0.2419 | 0.0000 | >0.80 |
|   Precision | 0.7644 | 0.5018 | 0.0000 | — |
|   Recall | 0.6656 | 0.2275 | 0.0000 | — |
| ReaQ (RAGAS) | **0.3039** (n=96) | 0.1654 (n=81) | N/A | >0.80 |
| HopAccuracy | **0.7513** (n=94) | 0.0000 | 0.0000 | >0.80 |
| YAML Syntactic | 0.9333 (n=30) | 0.9333 | 0.8333 | >0.80 ✅ |
| YAML Schema | 0.8333 (n=30) | **0.9333** | 0.7667 | >0.80 ✅ |
| Answer Relevance | 0.7618 | 0.7499 | 0.7173 | — |

#### Perbandingan before/after (3 sumbu perubahan)

> ⚠️ Catatan: 3 sumbu perubahan terjadi **bersamaan** (bundled, bukan isolasi penuh). Isolasi sumbu (c)/T1 tersedia secara bersih via A7 vs baseline dalam rezim baru.

**Sumbu (a)+(b) bundled: Indonesia→Inggris + GT lama (97 fx) → GT baru (103 fx, rekurasi penuh)**

| Metrik | Baseline (ID, 97 fx) | Final (EN, 103 fx) | Δ | Keterangan |
|--------|---------------------|-------------------|---|------------|
| GraphRAG AnsQ | 0.5771 | 0.7877 | +0.2106 | D5 (EN prompt) + GT baru |
| GraphRAG RetQ | 0.6631 | 0.6462 | −0.0169 | GT lebih ketat |
| GraphRAG ReaQ | 0.7602 | 0.3039 | −0.4563 | Lihat integrity note |
| GraphRAG HopAcc | 0.3505 | 0.7513 | +0.4008 | F3 formula fix + F14 |
| Vector AnsQ | 0.5916 | 0.7976 | +0.2060 | D5 lift |
| Vector RetQ | 0.3677 | 0.2419 | −0.1258 | GT lebih ketat |
| LLM AnsQ | 0.5956 | 0.7464 | +0.1508 | D5 lift |

**Sumbu (c) bersih — T1 proof: A7 (HAS_PROPERTY-only) vs GraphRAG baseline (18-edge), rezim baru**

| Metrik | 18-edge (baseline) | HAS_PROP only (A7) | Δ | Sig |
|--------|-------------------|-------------------|---|-----|
| AnsQ | 0.7877 | 0.7854 | +0.0023 | n.s. |
| RetQ (F1) | 0.6462 | 0.5573 | +0.0888 | p<0.001 *** |
| HopAccuracy | 0.7513 | 0.5242 | +0.2272 | p<0.001 *** |

T1 terbukti: 18-edge semantics meningkatkan RetQ (+8.9 pp) dan HopAccuracy (+22.7 pp) secara signifikan vs HAS_PROPERTY-only.

#### Uji statistik utama (GraphRAG vs Vector/LLM, Wilcoxon + bootstrap 1000 iter, Holm-corrected, n=103)

- GraphRAG vs Vector — RetQ: Δ=+0.404, p<0.001 ***; ReaQ: Δ=+0.127, p<0.001 ***; AnsQ: Δ=−0.010, n.s.
- GraphRAG vs LLM — AnsQ: Δ=+0.041, p<0.001 ***; RetQ: Δ=+0.646, p<0.001 ***

#### Integrity report — metrik tetap <0.80 (dilaporkan apa adanya)

| Metrik | Nilai | Kelas RC | Akar penyebab |
|--------|-------|----------|---------------|
| AnsQ = 0.7877 | 0.7877 | RC1+RC3 | AnsQ composite digerakkan answer_relevance=0.7618 (cosine sim embedding). Ceiling natural cosine sim; GraphRAG verbosity vs GT concise answer. Bukan threshold bug. |
| RetQ (F1) = 0.6462 | 0.6462 | RC3 | Recall=0.6656 lebih rendah dari Precision=0.7644. KG retrieval genuinely tidak selalu mencakup semua relevant_nodes GT (genuine gap). F1 depressed by lower recall. |
| ReaQ (RAGAS) = 0.3039 | 0.3039 | RC1+RC3 | Drop besar dari baseline 0.7602. Kemungkinan: (a) baseline lama mengukur `answer_relevancy` bukan faithfulness claim-level; (b) LLM judge RAGAS ketat — setiap klaim tidak terdukung konteks = unfaithful. GraphRAG sering mengisi general K8s knowledge di luar retrieved context → rendah secara intrinsik. Vector bahkan lebih rendah (0.1654). Bukan bug pengukuran. |
| HopAccuracy = 0.7513 | 0.7513 | RC3 | Mendekati target >0.80 tapi belum tercapai. Edge recall 75%; ~25% expected_path edge tidak ditemukan (depth atau edge-type mismatch). |

**Note khusus ReaQ:** Drop dari 0.7602 → 0.3039 bukan regresi — baseline lama kemungkinan besar menggunakan metric berbeda (answer_relevancy bukan faithfulness). Metric baru adalah claim-level faithfulness (RAGAS 0.4.x) yang lebih ketat dan sesuai definisi proposal tesis.

**Note YAML Schema:** GraphRAG 0.8333 < Vector 0.9333 bukan bug. GraphRAG menghasilkan `autoscaling/v2beta2` (deprecated K8s 1.26) untuk HPA fixtures karena context 18-edge mengandung referensi deprecated API. Genuine finding: richer context bisa menyebabkan over-specification ke deprecated API.

#### Artefak Fase 3

**Data baru:**
- `data/eval_results_{graphrag,vector,llm}_final.csv` — 103 baris masing-masing
- `data/eval_results_ablation_A{1,2,3,4,5,6c,7}.csv` — 7 ablation
- `data/eval_results_depth_{1,4,5}.csv` — depth sweep tambahan
- `data/ragas_results_{graphrag,vector,all}.csv` — faithfulness per fixture
- `data/statistical_test_results.csv` — Wilcoxon + bootstrap + Holm
- `data/boundary_condition_gain.csv` — Spearman hops/degree vs RetQ-gain
- `data/_archive_pre_fase3/` — snapshot CSV lama (sebelum re-run)

**Figur baru (13 total = 5 regen + 8 baru):**
- Regen: `depth_sensitivity_retq.png`, `depth_sensitivity_submetrics.png`, `boundary_retq_gain_by_type.png`, `boundary_hops_vs_gain.png`, `boundary_degree_vs_gain.png`
- Baru: `eval_systems_4metrics.png`, `eval_ablation_impact.png`, `eval_t1_has_property_vs_18edge.png`, `eval_by_intent.png`, `eval_prf_by_system.png`, `eval_ragas_faithfulness_dist.png`, `eval_significance_forest.png`, `eval_yaml_validity.png`

#### Handoff ke Fase 4

Pekerjaan Fase 4 (update LaTeX + angka):
1. Ganti semua angka evaluasi di `Bab VI - Evaluasi.tex` dengan angka final di atas
2. Masukkan 13 figur baru — filter mana yang dipakai saat menulis
3. Tulis narasi: (a) before/after 3 sumbu, (b) T1 evidence dari A7, (c) integrity note untuk ReaQ/AnsQ
4. Update tabel ablation (A1–A7 + depth sweep) dengan angka baru
5. Update `traceability_matrix.md` (T1–T4 claims vs metrik)
6. **F16 disclosure (wajib):** "single run; speaker temp 0.1 (mendekati deterministik); keyakinan statistik dari Wilcoxon+bootstrap n=103"

---

### 2026-06-14 — Fase 1 selesai

**Semua RC=1 measurement bug diperbaiki. Kode siap untuk re-run Fase 3.**

**Perubahan utama:**
- **F14:** SCHEMA_DEPS_QUERY + HYBRID_VECTOR_GRAPH_QUERY + PATH_EDGES_QUERY diparameterisasi via `{all_edges}` — default 18 edge (fix); ablation A7 (`has_property_only`) membuktikan T1 (Fase 3).
- **F15 (Symmetric):** GraphRAG Phase-2 vector fallback embed pertanyaan asli — identik baseline. Isolasi T1 bersih.
- **F1:** `SIMPLE_VECTOR_QUERY` (pure dense, no graph expansion) menggantikan `SIMPLE_GRAPH_EXPAND_QUERY` untuk mode vector di evaluate.py.
- **F3:** hop_accuracy → edge-level recall (Manning et al. 2008, recall applied to edge sets); diagnostik `gt_depth`/`n_roots` dikonsumsi dari GT Fase 2.
- **F12:** kubernetes_validate 1.29 → 1.30.
- **D5:** Speaker prompt + semua sentinel string diflip ke Inggris (eval penuh Inggris).
- **F7':** Nol perubahan kode; `topk_selection.md` dibuat; README:247 direkonsiliasi.
- **F5, F6, F8, F10:** logging RAGAS per-metrik, docstring RetQ, konstanta RGA, komentar L3.

**Verifikasi:**
- `pytest tests/evaluation/test_metrics.py::TestComputeReaq` → 11/11 PASS
- Import sanity → OK
- 16 pre-existing failures (TestFixtureDataIntegrity type='troubleshooting', TestSelectionGates) — unrelated to Fase 1

**Prasyarat Fase 3:**
1. Checkpoint eval lama invalid (F14+D5 mengubah perilaku) — re-run dari nol
2. Ablation baru: A7 (`has_property_only`) untuk bukti T1; A1 (`no_phase1`) untuk isolasi murni
3. Keputuskan F16 (single-run vs 3× mean±std + temperature=0) SEBELUM mulai Fase 3
4. Report before/after terpisah: Indonesia→Inggris + GT lama→baru + HAS_PROPERTY→18-edge

**Artefak baru:**
- `docs/AUDIT_E2E/topk_selection.md`
- `docs/AUDIT_E2E/phases/FASE_1.md`

---

### 2026-06-12 — Fase 2 post-critique cleanup

**Devil's advocate critique on all 103 active fixtures. 14 fixtures amended.**

**Group A (scope violation — OOS clause):** `plan_cronjob_batch` (notification OOS), `hpa_custom_metrics_yaml` (Prometheus OOS), `deployment_vs_statefulset_comparison` (design guidance removed).

**Group B (runtime framing):** `namespace_quota_relation` — CRITICAL FIX: resource Namespace->ResourceQuota, GT re-derived (rel 7->6); old GT had internal inconsistency (expected_path didn't traverse ResourceQuota but key_nodes had it). `cronjob_job_pod` + `service_selector` — Q/A reframing only.

**Group C (KG-meta):** `anyof_intorstring` — removed "represented in the knowledge graph" from Q.

**Group D (structural bug):** 5 ConfigMap/Secret leaf fixtures: `multi_hop` false (were True, ep=0 — pointless deep traversal).

**Group E (resource/GT):** `precodespec_containers_image_nginx_imagepul` — resource Pod->Container, rel 87->37 (tighter, correct). Two other Pod-root fixtures kept as-is (PodSpec root expands GT further due to deeper hub).

**Post-critique validation:** 3030/3030 VALID, 0 phantoms, 0 violations.

---

### 2026-06-11 — Fase 2 selesai

**GT fixture re-kurasi selesai. Semua exit criteria terpenuhi.**

**Ringkasan perubahan:**
- Semua 97 fixture diterjemahkan ke Inggris (`question`/`answer`/`context`; `lang:"en"`); YAML & node-name verbatim.
- 8 kategori divalidasi manual (Rubrik A1–D2) + GT di-recuate via `recurate_fixtures.py`.
- 14 realworld fixture di-drop (OOS: Tekton×2, ArgoCD, Kubeflow, EKS, GKE, Istio, Podman, kubectl-behavior×3, AdmissionControllers, auth, Python-client) — `selection_score=0`, file dipertahankan.
- 6 fixture direwrite penuh ke in-scope schema (3 relationship + 6 realworld).
- 2 KG-topology bug diperbaiki: `anyof_intorstring` (root ContainerPort→EnvFromSource), `secret_usage` (root Secret→PodSpec).
- **83 fixture aktif** (97 total − 14 drops). Kemudian ditambah 20 fixture baru (10 conceptual + 10 yaml_gen) → **103 fixture aktif total** (117 total).

**Hasil validasi akhir (`validate_dataset.py`, Neo4j online, 2026-06-11):**
- 3096/3096 expected_path edges VALID (0 NOT_IN_GRAPH) — naik dari 2702 setelah penambahan 20 fixture
- 0 phantom relevant_nodes · 0 phantom key_nodes · 0 key⊄relevant
- 33/33 YAML syntactic PASS · 32/33 schema PASS

**GT field changes:** `relevant_nodes`, `expected_path`, `key_nodes`, `gt_depth` semua ditulis ulang via engine (context-driven minimal subgraph). Detail per-fixture di `fixture_fix_log.md`.

**Artefak baru:**
- `tests/fixtures/**/*.json` — semua fixture diperbarui
- `data/gt_node_validation.csv` — B4/B5 check output
- `docs/AUDIT_E2E/fixture_validation_checklist.md` — rubrik + status per kategori

**Prasyarat untuk Fase 1 (kode):**
1. Konsumsi `gt_depth` + `n_roots` untuk F3 (HopAccuracy formula fix)
2. Flip prompt speaker `prompts.py:36` → Inggris (eval penuh Inggris)
3. Isu terbuka: keadilan embed F14/F15 (genuine mechanism deficiency)

**Untuk Fase 3 (re-run):**
- Snapshot pra-mutasi tersimpan di tag git `pre-fase2-fixtures`
- Baseline Indonesia dari `_final` CSV lama (STATUS catatan angka di bawah)
- Wajib lapor before/after (Indonesia→Inggris + GT-lama→GT-baru) secara terpisah

### 2026-06-09 — Fase 0 selesai
- Artefak dihasilkan: `bug_register.md` (16 temuan F1–F16 + F13), `metric_suitability.md` (semua metrik dinilai), `critical_review.md` (10 ancaman validitas).
- **Tidak ada perubahan kode/data/tesis.** Stats pass Python read-only saja.
- Target diperbarui: **>0,85 semua metrik** (dari >0,80/mayoritas ≥0,85).
- Framing dikoreksi: 3 root-cause class; KG sendiri diidentifikasi sebagai genuine mechanism deficiency (F14, F15).

**Temuan kritis Fase 0:**
1. **F14 (KRITIS):** Context path hanya HAS_PROPERTY — 14 edge semantik tidak masuk konteks LLM. Klaim T1 belum terbukti. AnsQ GraphRAG < kedua baseline (genuine RC=3). **Keputusan user diperlukan: Opsi A (fix SCHEMA_DEPS_QUERY ke all-18-edge) vs Opsi B (sempitkan klaim T1).**
2. **F2 (6 fixture out-of-scope):** command×3 + troubleshooting×3 — runtime kubectl, zero-curation GT. Re-scope atau re-kurasi Fase 2.
3. **F3 (HopAccuracy artefak):** d_gt = len(expected_path) ~75-112 bukan depth 1–5. Pasca-fix jadi tautologi → pertimbangkan ganti formula.
4. **F7′ (top_k tiga nilai):** prod seed=1, GraphRetriever=3, eval vector=5. Perlu sweep + dokumentasi Fase 1.
5. **F4 (node GT hilang):** AccessMode + SecretType tidak ada di swagger definitions; StorageClass FQN salah.

**Metrik berisiko intrinsik (tidak dijamin ≥0,85 meski semua bug diperbaiki):**
- AnsQ composite (GraphRAG < baseline; tergantung F14 decision)
- RAGAS faithfulness (LLM judge ketat; intrinsik sulit)
- RAGAS ctx_precision/recall (tergantung F14)
- RGA (binary, sensitif threshold)

**Langkah berikut Fase 1:**
- Konfirmasi keputusan F14 (Opsi A vs B) ke user *sebelum* eksekusi
- Perbaiki F1 (vector baseline pure-dense), F3 (HopAccuracy formula/replace), F5 (RAGAS n logging), F6 (docstring), F7′ (top_k sweep+konsistensi), F8 (RGA threshold justifikasi), F12 (validator versi)
- Buat `docs/AUDIT_E2E/topk_selection.md` (sweep k, pilih domain-terbaik, dokumentasikan)
- Fase 2 paralel/setelah: re-kurasi 6 fixture out-of-scope, fix 3 node GT missing

### 2026-06-09 — Fase -1 selesai
- Scaffolding dibuat: `CHARTER.md`, `STATUS.md`, `STYLE_GUIDE.md`, `memory/audit-e2e-charter.md` (+ pointer di `MEMORY.md`).
- Belum ada perubahan kode/data/tesis.

## Catatan angka baseline (untuk perbandingan setelah re-run)
GraphRAG `_final`: AnsQ 0,5771 · RetQ 0,6631 · ReaQ 0,7602 · PathCov 0,8515 · HopAcc 0,3505 · RGA 0,4536 · YAML syntactic 0,8947 (n=19) · schema 0,7895.
Vector `_final`: AnsQ 0,5916 · RetQ 0,3677 · ReaQ 0,6615 · HopAcc 0,0 · RGA 0,2784.
LLM `_final`: AnsQ 0,5956 · RetQ 0,0 · ReaQ 0,5981 · HopAcc 0,0722 · RGA 0,0206.
RAGAS by mode: faithfulness 0,1838 (n=49) · answer_relevancy 0,6191 (n=95) · ctx_precision 0,3190 (n=62) · ctx_recall 0,3813 (n=62).
