# FASE 8 — Compile Final & Verifikasi

> Baca bersama `CHARTER.md` + `STATUS.md`. Fase penutup Audit E2E.

## Objektif

Memastikan dokumen final compile bersih, setiap angka di tesis cocok dengan CSV sumber
(nol mismatch), dan menyiapkan pertahanan sidang (mock penguji). Urutan eksekusi berjenjang:
**Pilar A (compile) → Pilar B (cross-check) → Pilar C (mock penguji)**, dengan loop-back ke
A setiap kali B menemukan defect nyata yang dikonfirmasi dan diperbaiki. Pilar D (temuan git)
di luar gerbang ini, murni pelaporan.

---

## Pilar A — Compile Final

**Metodologi:** `xelatex → biber → xelatex → xelatex` dari `docs/TA-STI-template-1.0/`, PATH
di-scrub dari 2 entri rusak (`supabase`, dan baru ditemukan: `heroku-x64.exe` di
`Downloads` — MiKTeX gagal start tanpa filter ini). Visual skim halaman kunci via `pdftoppm`
bundel MiKTeX (poppler tak terpasang) + `pdftotext -layout` (baru dipakai sesi ini) untuk
ekstraksi teks penuh 192 halaman guna mapping halaman fisik dan input Pilar B.

**Hasil compile pertama (sebelum temuan):** 192 halaman, exit 0 di 3 pass, 0 baris fatal
`^! `, 0 undefined reference/citation, 0 multiply-defined label. Overfull hbox 96 total / 13
>10pt — **identik** dengan baseline Fase 7, nol regresi dari kerja Fase 7 yang belum
di-commit.

**Koreksi catatan lama:** memory `reference_latex_compile.md` menyatakan frontmatter memakai
"arabic kontinu dari 1" — **keliru**, dikonfirmasi visual: frontmatter memakai romawi kecil
(mis. halaman fisik 9 = Abstrak, footer "ix"). Mainmatter (Bab I dst.) mereset ke arabic dari
1 seperti biasa. Memory akan dikoreksi di akhir sesi.

### Temuan A-1 (KRITIS) — Catatan editorial bocor ke Daftar Pustaka

Saat skim visual Daftar Pustaka (halaman fisik 141, tercetak "113"), entri "Gu, Yi... 2024"
mencetak **verbatim** field `note={}` dari `.bib`:

> *"MidMed: Towards Mixed-Type Dialogues for Medical Consultation". Cited for Hop-Accuracy
> edge-recall formulation; confirm full citation from Ma et al. (...) reference list, arXiv
> preprint.*

Ini catatan editorial internal (bukan bagian sitasi akademik), dirender apa adanya oleh gaya
`chicago-authordate`. Root cause: `CHARTER.md` §Temuan sudah menolak `gu_2024` (paper MidMed,
dialog medis, tak relevan untuk graph edge-recall) dan mengharuskan penggantian ke
`manning_ir_2008` "di semua file" — namun **satu instance** di `Bab II - Studi.tex:282`
(definisi metrik Hop-Accuracy di bab studi literatur) terlewat. Diverifikasi: 4 lokasi lain
yang mendefinisikan rumus identik (Bab VI §48, §129, tabel29c, tabel31b) sudah benar pakai
`manning_ir_2008`.

**Fix diterapkan (dikonfirmasi user):**
- `Bab II - Studi.tex:282`: `\parencite{gu_2024}` → `\parencite{manning_ir_2008}`
- `daftar-pustaka.bib`: entri `gu_2024` (baris 108–114) dihapus total
- Recompile: 192 halaman, exit 0, 0 fatal, 0 undefined ref/citation. Overfull >10pt turun
  96→95 total, 13→12 kasus >10pt (efek samping positif — entri bermasalah adalah salah satu
  dari 5 kasus overflow bibliografi yang didokumentasikan sebagai residual di Fase 7).
- Verifikasi visual ulang halaman 141: entri "Gu, Yi..." hilang total, alur Abu-Salih→
  Cao→CNCF→Es→Gao→Gartner→**Han (GraphRAG)** mulus tanpa gap.

---

## Pilar B — Cross-check Angka Tesis vs CSV Final

**Metodologi:** `scripts/verify_thesis_numbers.py` (baru, ad hoc — bukan bagian pipeline
produksi) memuat CSV sumber (`eval_results_{graphrag,vector,llm}_final.csv`,
`ragas_results_{graphrag,vector}.csv`, `statistical_test_results.csv`,
`boundary_condition_gain.csv`, ablation A1–A7, depth 1/4/5), menghitung ulang tiap metrik
persis mengikuti konvensi tesis, lalu dibandingkan ke 63 klaim yang dienumerasi dari
`tables/*.tex` + prosa Bab VI/Abstrak/Bab VII/Bab II.

**Konvensi yang diverifikasi presisi (bukan diasumsikan):**
- `schema_compliance`: bukan hanya `type=='yaml_gen'` — juga fixture `realworld` yang
  menghasilkan YAML (GraphRAG n=28, Vector/LLM n=30), dikurangi RBAC exclusion
  (`serviceaccount_pod_binding`) → n=27/29/29 sesuai footnote tabel31.
- Hop Accuracy stratifikasi focused/closure: kolom **`depth_gt`** (= `len(expected_path)`,
  edge count, `evaluate.py:372`) — BUKAN kolom `gt_depth` (traversal depth, nilai 2–3 saja).
  Dua kolom terpisah di CSV yang sama, mudah tertukar (sempat jadi bug di iterasi pertama
  skrip verifikasi ini, dikoreksi sebelum hasil final).
- Ablation/depth-sweep CSV (A1–A7, depth 1/4/5) dibandingkan **apa adanya** (n=103, masih
  memuat `pim_trying_to_use_a_container`) terhadap baseline n=102 yang sudah dipangkas —
  pairing-N asimetris ini, bukan pemangkasan simetris, yang benar-benar mereproduksi angka
  tesis. Cocok dengan catatan STATUS.md 2026-07-04 ("delta/CI tidak berubah" = diverifikasi
  ulang stabil, bukan direkomputasi dari set yang dipangkas ulang).
- Spearman degree ρ: `boundary_condition.py:366` mengecualikan baris `graph_degree==0`
  (resource tak ditemukan di lookup Neo4j) sebelum korelasi → n=101, bukan n=102.
- Faithfulness 0,3055 (n=95): nilai beku, `ragas_results_graphrag.csv` saat ini n=96 (1
  fixture `kubectl_force_delete_pod` muncul belakangan). Sudah diadjudikasi CLARIFY→RESOLVED
  di `consistency_trace.md` (2026-06-28) — diverifikasi ulang di sini, diperlakukan sebagai
  ACCEPTED, bukan mismatch baru.

**Hasil awal:** 61/63 MATCH persis, 2 mismatch. Investigasi mendalam kedua mismatch:

### Temuan B-1 (bukan defect tesis) — Spearman ρ salah filter di skrip verifikasi
Skrip awal tidak mengecualikan `graph_degree==0`. Setelah difilter sesuai
`boundary_condition.py:366`: ρ=0,2454 (≈0,245), p=0,0134 (≈0,013), n=101 — **cocok persis**.
Bug di skrip verifikasi, bukan di tesis.

### Temuan B-2 (KRITIS, defect tesis nyata) — Tanda salah di tabel32.tex, ΔHopAcc ablasi A5
`tabel32.tex:23` mencetak ΔHopAcc A5 = `−0,0037`, padahal HopAcc absolut A5 (0,7599, sudah
benar) lebih besar dari baseline (0,7562, sudah benar) — secara matematis delta **harus**
positif. Diverifikasi 3 jalur independen (pandas/numpy/manual sum-per-n, presisi penuh tanpa
pembulatan dini): A5−Baseline = +0,0036956696 → +0,0037. Kontrol silang: baris A4 (skenario
sama, ablasi>baseline) tercetak benar dengan tanda positif (+0,1445), mengonfirmasi tabel
memakai konvensi Ablasi−Baseline secara konsisten di 20 sel lain — A5 satu-satunya anomali.
Narasi Bab VI §282 dan Bab VII §14 tentang A5 hanya membahas ΔRetQ, tidak pernah mengklaim
arah ΔHopAcc — jadi tidak ada teks lain yang perlu disentuh. `tabel36.tex` (p-value A5 HopAcc
= 0,841 n.s.) tidak encode arah, tidak terdampak.

**Temuan sekunder:** footnote `tabel32.tex:32` menulis rumus "Δ = Baseline − Ablasi", tapi
seluruh 21 sel delta (termasuk A5 setelah fix) konsisten dengan **Ablasi − Baseline**
(diverifikasi: A1 RetQ 0,4001−0,7089=−0,3088, cocok tercetak). Label rumus di footnote
terbalik dari data aktual — bug label, bukan bug angka.

**Fix diterapkan (dikonfirmasi user, dengan re-verifikasi presisi penuh atas permintaan
user sebelum eksekusi):**
- `tabel32.tex:23`: ΔHopAcc A5 `$-0{,}0037$` → `$+0{,}0037$`
- `tabel32.tex:32`: footnote "Δ = Baseline − Ablasi; nilai positif = ..." →
  "Δ = Ablasi − Baseline; nilai negatif = komponen berkontribusi positif (...)"
- Recompile: 192 halaman, exit 0, 0 fatal, 0 undefined ref/citation.

### Verifikasi struktural tambahan (domain, terkait Pilar C)
18 tipe edge dihitung ulang langsung dari `src/graph/queries.py` (bukan hanya dari LaTeX):
`BINDS_ROLE, BINDS_SERVICE_ACCOUNT, CLAIMS_VOLUME, CONTAINS_JOB_TEMPLATE,
CONTAINS_POD_TEMPLATE, EXTENDS, HAS_CONTAINER, HAS_PROPERTY, LOADS_CONFIGMAP,
MOUNTS_VOLUME, ONE_OF, ANY_OF, ROUTES_TO_SERVICE, SCALES_RESOURCE, SELECTS_POD, USES_SECRET,
USES_SERVICE_ACCOUNT, USES_STORAGE_CLASS` = tepat 18. Cocok klaim tesis. (725 node tidak
diulang — sudah diverifikasi tuntas di Fase 5/`consistency_trace.md`, `parser.py` tak
tersentuh sejak itu.)

### Hasil akhir Pilar B
**63/63 checks MATCH.** Nol mismatch tersisa setelah 2 fix di atas.

| Kategori klaim | Jumlah checks | Status |
|---|---|---|
| Headline AnsQ/RetQ/Faithfulness/HopAcc (3 sistem) | 18 | MATCH |
| Depth sensitivity (d=1,3,4,5) | 9 | MATCH |
| Ablation A1–A7 (ΔRetQ, ΔHopAcc) | 12 | MATCH (1 fix diterapkan) |
| Boundary RetQ-gain per kategori (8) + Spearman (2) | 10 | MATCH |
| Fixture category counts (8 kategori) | 8 | MATCH |
| Lain-lain (syntactic/schema compliance, faithfulness frozen) | 6 | MATCH |

Skrip verifikasi: `scripts/verify_thesis_numbers.py` (disimpan untuk referensi, bukan bagian
pipeline produksi, tidak di-commit — lihat Pilar D).

---

## Pilar C — Mock Penguji (dibobot domain, lensa STI)

Lihat `docs/AUDIT_E2E/mock_defense.md` (artefak terpisah).

---

## Pilar D — Temuan Git (flag saja, tidak diubah)

Lihat ringkasan di `STATUS.md` handoff notes.

---

## Ringkasan Fase 8

- **2 defect nyata ditemukan dan diperbaiki** (bukan di-tuning/fabrikasi): sitasi salah yang
  membocorkan catatan editorial ke Daftar Pustaka; tanda salah pada 1 sel tabel ablation.
- **1 bug metodologi label** (bukan angka) diperbaiki: footnote formula tabel32 dibalik dari
  konvensi datanya.
- **63/63 angka tesis lain sudah benar** — cross-check sistematis, bukan sampling.
- **Compile final: 192 halaman, exit 0, 0 fatal, 0 undefined ref/citation.**
- 1 koreksi memory (frontmatter romawi, bukan arabic — lihat `reference_latex_compile.md`).
