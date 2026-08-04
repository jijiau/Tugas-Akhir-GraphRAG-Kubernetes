# Phase 5 — Bab VI: Update Empiris dan Sinkronisasi v13

**Status:** PENDING  
**Prasyarat:** Phase 1 selesai  
**Referensi Aturan Bahasa:** [Plan Utama](../../.claude/plans/act-seperti-dosen-penguji-zippy-kahn.md) — bagian "Aturan Bahasa"

---

## ⚠ REVISI BESAR (Mei 2026) — BACA DULU, BANYAK ISI DI BAWAH USANG

Phase 5 berubah total. Bab VI sekarang = **rumah Tujuan ke-3 (Perbandingan)**, disajikan **per-faktor tanpa skor Total berbobot**.

**Yang berlaku:**
1. **HAPUS `eq:total_score`** & semua narasi "skor komposit/Total berbobot". Bobot 0,40/0,35/0,25 dibuang. **Pertahankan** skor per-dimensi (AnsQ/RetQ/ReaQ) & per-domain (Path Coverage, Hop Accuracy, RGA, *syntactic validity*).
2. **Struktur utama Bab VI = tabel perbandingan per-faktor 3 sistem** (GraphRAG, Vector RAG, Vanilla LLM). Bab ini menjawab langsung T3.
3. **SEMUA ANGKA DI BAWAH (v12/v13/0,6989 dst.) USANG.** `evaluate.py` final belum dijalankan; CSV lama (termasuk v17) masih metrik lama. **Wajib re-run 3 sistem** dulu, baru isi angka.
4. **Metrik final:** RetQ=(F1+NDCG+Path Coverage)/3; ReaQ=(Hop Accuracy+Grounding)/2; AnsQ apa adanya; precision/recall & *hallucination* = diagnostik/dibuang. Definisi di Bab II.
5. **Jangan pra-tulis pemenang:** faktor tempat GraphRAG unggul/setara/lemah = temuan empiris dari re-run, disimpulkan di Bab VII.
6. Ablation/depth-sensitivity/boundary tetap, reposisi sebagai pendukung klaim per-faktor; uji signifikansi (Wilcoxon+bootstrap) & 95% CI per faktor kunci (RetQ, Path Coverage, Hop Accuracy) dari data re-run.
7. Visual ringkas: bar/radar per-dimensi, bukan satu angka headline.

Tabel "Perubahan Angka v12→v13" & sejenisnya di bawah HANYA arsip. Abaikan angkanya.

---

## ⚠ CONSTRAINT GLOBAL (WAJIB)

- **TA.tex TIDAK BOLEH DIUBAH**
- Persona: "Penelitian ini..." (Aturan C1)
- Desimal: koma bukan titik — `0,6989` bukan `0.6989` (Aturan A7)
- Range: en-dash — `1--5` di LaTeX → "1–5" di output (Aturan C6)
- Tidak ada kalimat mulai dengan angka (Aturan A13)

---

## Konteks Phase 5

**Kabar baik:** Bab VI sudah sangat lengkap — ablation study, depth sensitivity, statistical test, dan boundary condition analysis sudah ada dan berstruktur baik. Tidak perlu tambah section baru.

**Yang perlu dilakukan Phase 5:**
1. Update angka v12 → v13 di section hasil evaluasi utama
2. Fix label tabel ablation (masih bilang "v12" sebagai baseline)
3. Sinkronisasi angka v13 di abstrak dan tabel perbandingan
4. Audit format LaTeX (tabel inline di Bab VI harus pindah ke `tables/` untuk konsistensi)
5. Audit bahasa dan cross-reference

---

## File yang Dimodifikasi

| File | Perubahan |
|------|-----------|
| `Bab VI - Evaluasi.tex` | Update angka v12→v13; fix tabel label; audit format |
| `tables/tabel29.tex` | Update nilai v13 (dimension scores) |
| `tables/tabel30.tex` | Update nilai v13 (per-category scores) |
| `tables/tabel31.tex` | Update nilai v13 (baseline comparison) |

---

## Perubahan Angka v12 → v13 — ⚠ USANG (angka diganti hasil re-run final; arsip saja)

### Tabel Skor Utama (tabel29 — Dimension Scores)

| Dimensi | v12 (lama) | v13 (baru) |
|---------|-----------|-----------|
| AnsQ | 0,5743 | **0,5904** |
| RetQ | 0,6851 | **0,6801** |
| ReaQ | 0,8994 | **0,8989** |
| **Total** | **0,6943** | **0,6989** |

### Tabel Perbandingan Baseline (tabel31)

| Sistem | v12 (lama) | v13 (baru) |
|--------|-----------|-----------|
| GraphRAG Total | 0,6943 | **0,6989** |
| Vector RAG Total | 0,6111 | 0,6111 (tidak berubah) |
| Vanilla LLM Total | 0,4015 | 0,4015 (tidak berubah) |

> **Catatan:** v13 hanya mengubah prompts.py (aturan faithfulness untuk YAML stateful). Baseline Vector RAG dan Vanilla LLM tidak perlu di-re-run; angka tetap sama.

### Tabel Statistical Test (tabel dalam Bab VI)

Update baris "Total" dari 0,6943 → **0,6989**, delta dari +0,0832 → **+0,0878**.

### Ablation Study Table (tabel dalam Bab VI)

⚠ Caption tabel ablation di baris 127 menyebut "baseline GraphRAG (v12)". Update ke:
- **Option A:** Ubah ke "(v13)" jika ablation dijalankan ulang dengan baseline v13
- **Option B:** Pertahankan "(v12)" dan tambah footnote: "Ablasi dijalankan terhadap v12 sebagai baseline stabil sebelum penyesuaian prompts v13"

> **Rekomendasi Option B** — ablation study A1-A6c memang dijalankan dengan v12, bukan v13. Lebih honest secara akademis untuk menyebutkan hal ini dengan footnote.

---

## Section yang Perlu Diperbarui Teksnya

### Section 6.3.1 — Skor Keseluruhan (baris ~60-64)

Ubah:
```
...menghasilkan total skor komposit \textbf{0,6943}...
```
Menjadi:
```
...menghasilkan total skor komposit \textbf{0,6989}...
```

Dan update angka-angka terkait dalam paragraf:
- AnsQ: 0,5743 → 0,5904
- RetQ: 0,6851 → 0,6801 (turun sedikit, perlu dijelaskan: dalam batas noise stokastisitas LLM)
- ReaQ: 0,8994 → 0,8989

Tambahkan kalimat penjelas:
> "Peningkatan AnsQ dari v12 ke v13 ($\Delta = +0{,}0162$) terutama didorong oleh penambahan aturan konsistensi nama dan sumber daya pendamping wajib pada prompts sistem Speaker, yang merespons temuan bahwa konfigurasi database stateful membutuhkan resource pendamping seperti *PersistentVolumeClaim*."

### Section 6.4 — Pembahasan (baris ~84-90)

Update semua angka v12 → v13:
- "total skor komposit 0,6943" → **0,6989**
- AnsQ, RetQ, ReaQ sesuai tabel di atas

### Section 6.5 — Perbandingan Baseline (baris ~98-116)

Subsection "Total Skor Komposit" (baris ~114-116):
- "GraphRAG memperoleh total skor komposit tertinggi (0,6943)" → **(0,6989)**
- Delta AnsQ: "−0,0236" → perlu hitung ulang: 0,5904 − 0,5979 = **−0,0075**

---

## Tabel Inline di Bab VI → Pindah ke tables/

Bab VI saat ini punya 5 tabel yang ditulis **inline** (bukan via `\input{}`):
- Tabel ablation results (baris ~125-142)
- Tabel ablation significance (baris ~208-225)
- Tabel retq-gain per type (baris ~255-273)
- Tabel Spearman factors (baris ~300-314)
- Tabel statistical test (baris ~184-202)

**Konvensi template:** tabel kompleks sebaiknya di `tables/tabel*.tex` via `\input{}`.  
**Rekomendasi:** Pindah ke `tables/tabel32.tex` – `tabel36.tex` dan `\input{}` di Bab VI.

> **Jika tidak sempat di Phase 5:** Pastikan minimal semua tabel inline punya `\caption{}` dan `\label{tbl:...}` yang valid untuk masuk ke Daftar Tabel.

---

## Audit Gambar Bab VI

Gambar yang sudah ada (dipastikan tersedia di `images/`):

| Label | File | Section |
|-------|------|---------|
| `fig:depth-sensitivity` | `depth_sensitivity_retq.png` | 6.ablation.subsec |
| `fig:depth-submetrics` | `depth_sensitivity_submetrics.png` | 6.ablation.subsec |
| `fig:boundary-retq-gain-by-type` | `boundary_retq_gain_by_type.png` | 6.boundary |
| `fig:boundary-hops-vs-gain` | `boundary_hops_vs_gain.png` | 6.boundary |
| `fig:boundary-degree-vs-gain` | `boundary_degree_vs_gain.png` | 6.boundary |

Semua file sudah ada di `docs/TA-STI-template-1.0/images/` ✓. Tidak perlu buat gambar baru.

Cek: apakah caption gambar sudah menggunakan `\captionsetup{justification=centering}` sesuai template?

---

## Audit Format Equation

Bab VI punya 2 persamaan:
1. `eq:total_score` — Total Score formula (baris ~28-31)
2. `eq:retq-gain` — RetQ-gain definition (baris ~236-239)

Verifikasi: apakah kedua persamaan sudah punya `\eqcaption{}` sesuai Aturan D3? Jika belum, tambahkan agar masuk ke Daftar Persamaan.

---

## Checklist Verifikasi Phase 5

### Angka (REVISI)
- [ ] Angka GraphRAG/Vector/Vanilla diambil dari re-run `evaluate.py` final (BUKAN v12/v13/v17 lama)
- [ ] Tidak ada skor Total berbobot di Bab VI; skor per-dimensi & per-domain disajikan per-faktor
- [ ] Delta per-faktor (RetQ, Path Coverage, Hop Accuracy, *syntactic validity*) dihitung dari re-run
- [ ] Uji signifikansi (Wilcoxon + bootstrap) & 95% CI per faktor kunci
- [ ] Tidak ada pemenang yang dipra-tulis; faktor unggul/setara = temuan empiris
- [ ] Ablation baseline: caption menyebut "(v12)" + footnote penjelasan

### Format
- [ ] Tidak ada angka desimal titik (0.6943 → 0,6943)
- [ ] Semua tabel inline punya `\caption{}` + `\label{tbl:...}`
- [ ] Semua gambar punya `\captionsetup{justification=centering}` + `\caption{}` + `\label{fig:...}`
- [ ] `eq:total_score` DIHAPUS (tanpa Total berbobot); persamaan metrik lain (mis. `eq:retq-gain`) punya `\eqcaption{}`
- [ ] Cross-reference `\ref{sec:ablation-study}`, `\ref{subsec:depth-sensitivity}`, `\ref{sec:statistical-test}` masih valid

### Bahasa
- [ ] Persona "Penelitian ini..." konsisten
- [ ] Tidak ada kalimat mulai dengan angka
- [ ] Tidak ada "dimana"/"di mana" sebagai relative pronoun
- [ ] Hedging tepat: "menunjukkan", "mengindikasikan" (bukan "membuktikan secara mutlak")

---

## Catatan untuk Phase Selanjutnya

- **Phase 6** (Bab VII): Update angka 0,6943 → 0,6989 di kesimpulan; pertahankan 3 paragraf per T1/T2/T3
- **Phase 8** (Abstrak): Update angka v13 di Abstrak juga
