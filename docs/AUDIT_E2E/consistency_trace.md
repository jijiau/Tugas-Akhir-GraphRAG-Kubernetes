# Consistency Trace — Bab I–VII (pra-Fase 7)

> Audit tracing konsistensi lintas-bab + verifikasi angka ke CSV ground-truth + kesesuaian klaim dengan kode.  
> Tanggal: 2026-06-28 | Audit E2E pra-Fase 7 | Sumber kebenaran: `data/eval_results_*_final.csv`, `statistical_test_results.csv`, `boundary_condition_gain.csv`, `ragas_results_*.csv`, `faithfulness_decomposition.csv`

---

## Ringkasan eksekutif

| Kategori | Jumlah |
|----------|--------|
| **MISMATCH** (perlu fix) | 4 |
| **CLARIFY** (keputusan user) | 1 |
| **CONSISTENT** (terverifikasi) | 34 |

Fix dikelompokkan: **G1** = angka salah (tabel-depth.tex), **G2** = klausa penjelas (celah node), **G3** = terminologi (follow-up→followup). CLARIFY ditangani sebelum G3.

---

## Temuan MISMATCH — Perlu Fix

### G1: Angka AnsQ di Tabel Depth Sensitivity

| ID | Lokasi | Klaim Tesis | Ground-truth (CSV) | Grup |
|----|--------|-------------|-------------------|------|
| M1 | `tables/tabel-depth.tex:11` — baris d=1 | AnsQ = **0,7602** | `eval_results_depth_1.csv`: mean=**0.7815** (n=103) | G1 |
| M2 | `tables/tabel-depth.tex:15` — baris d=4 | AnsQ = **0,7548** | `eval_results_depth_4.csv`: mean=**0.7828** (n=103) | G1 |
| M3 | `tables/tabel-depth.tex:19` — baris d=5 | AnsQ = **0,7611** | `eval_results_depth_5.csv`: mean=**0.7817** (n=103) | G1 |

**Akar penyebab:** Nilai 0,7602/0,7548/0,7611 berasal dari run lama (pra-Fase 3). Nilai RetQ dan HopAcc di baris yang sama sudah benar (0,3666/0,2574 d=1; 0,6113/0,9007 d=4; 0,5838/0,8760 d=5). Kolom AnsQ saja yang belum diupdate ke evaluasi final.

**Catatan:** Prosa Bab VI §245 TIDAK menyebutkan AnsQ untuk d=1/4/5 secara eksplisit — hanya RetQ dan HopAcc — jadi hanya tabel yang perlu difix.

---

### G2: Gap Node 730→725 Tanpa Klausa Penjelas

| ID | Lokasi | Situasi | Grup |
|----|--------|---------|------|
| M4 | `Bab III §63` + `Bab V §38` | Bab III: 730 definisi valid (183+547). Bab V: 725 node (183+542). Gap 5 node tidak dijelaskan. | G2 |

**Akar penyebab:** `src/ingestion/parser.py:39-55` mendefinisikan `IGNORE_LIST` dengan 5 entry tambahan (`FieldsV1`, `OwnerReference`, `Patch`, `StatusCause`, `io.k8s.apimachinery.pkg.version.Info`) yang merupakan tipe internal *apimachinery* tanpa relevansi YAML dan tanpa edge di graf. Entry ini ada di 730 definisi EDA, tapi di-skip saat ingestion → 730−5 = **725 node**. Bab III §63 sudah menjelaskan penyaringan 5 entri *noise* dari 735→730 (entry berbeda: tipe metadata lain). Total dua langkah penyaringan, hanya satu yang dijelaskan.

**Klausa penjelas yang diusulkan** (di `Bab V - Implementasi.tex` §38, setelah "542 node sub-resource"):

> Lima dari 730 definisi yang diidentifikasi pada analisis data (Subbab~\ref{subsec:eda}) tidak diikutsertakan dalam proses pembuatan node karena merupakan tipe utilitas internal \textit{apimachinery} (\texttt{FieldsV1}, \texttt{OwnerReference}, \texttt{Patch}, \texttt{StatusCause}, \texttt{Info}) yang tidak memiliki relevansi penulisan YAML dan tidak menghasilkan edge dalam \textit{knowledge graph}.

---

## Temuan CLARIFY — Keputusan User Diperlukan

| ID | Lokasi | Situasi |
|----|--------|---------|
| C1 | Abstrak, Bab VI §135/145/200/220/317, Bab VII §26, tabel29c/31/31c/31d | Tesis menggunakan faithfulness **0,3055 (n=95)** secara konsisten. CSV `ragas_results_graphrag.csv` menunjukkan **0.3039 (n=96)** — 1 fixture tambahan (`kubectl_force_delete_pod`, faith=0.0) yang muncul di CSV saat ini tetapi None/NaN ketika tesis ditulis. Δ+0,127 (dari paired stat test) **tetap valid** di kedua versi. |

**Opsi:**
- **Pertahankan 0,3055 (n=95)** — nilai saat komputasi dilakukan, tesis internal konsisten, delta valid. Tidak ada perubahan diperlukan. *(Rekomendasi: pertahankan, perbedaan 0.0016 tidak material)*
- **Update ke 0,3039 (n=96)** — cocok dengan CSV saat ini, tapi memerlukan perubahan di ±8 lokasi termasuk narasi n=95.

---

## Temuan CONSISTENT — Terverifikasi (tidak ada fix)

### Angka headline (CSV vs Tesis: semua cocok)

| Metrik | Nilai Tesis | CSV Ground-truth | Verdict |
|--------|------------|-----------------|---------|
| GraphRAG AnsQ | 0,8031 | 0.8031 (n=102) | ✅ |
| GraphRAG RetQ F1 | 0,7089 | 0.7089 (n=102) | ✅ |
| GraphRAG RetQ Precision | 0,8405 | 0.8405 | ✅ |
| GraphRAG RetQ Recall | 0,7258 | 0.7258 | ✅ |
| Vector RetQ F1 | 0,2419 | 0.2419 (n=103) | ✅ |
| Hop Accuracy all | 0,7562 (n=93) | 0.7562 (n=93) | ✅ |
| Hop Accuracy focused ≤15 | 0,9086 (n=50) | 0.9086 (n=50) | ✅ |
| Hop Accuracy closure >15 | 0,5791 (n=43) | 0.5791 (n=43) | ✅ |
| GraphRAG syntactic validity | 1,0000 (n=28) | 1.0000 (n=28) | ✅ |
| GraphRAG schema compliance | 0,8929 (n=28) | 0.8929 (n=28) | ✅ |
| Vector syntactic validity | 0,9333 | 0.9333 | ✅ |
| Vector schema compliance | 0,9333 | 0.9333 | ✅ |
| LLM AnsQ | 0,7464 | 0.7464 | ✅ |
| AnsQ GraphRAG vs Vector Δ | +0,005 | 0.0047 | ✅ |
| AnsQ GraphRAG vs Vector p_Holm | 0,067 | 0.0666 | ✅ |
| RetQ GraphRAG vs Vector Δ | +0,465 | 0.4652 | ✅ |
| Faithfulness Δ vs Vector | +0,127 | 0.127 (stat test paired) | ✅ |
| Faithfulness Vector | 0,1654 (n=81) | 0.1654 (n=81) | ✅ |

### Depth sensitivity (RetQ dan HopAcc benar, hanya AnsQ yang salah — sudah didaftarkan M1-M3)

| d | RetQ (tesis→CSV) | HopAcc (tesis→CSV) |
|---|---|---|
| d=1 | 0,3666 → 0.3666 ✅ | 0,2574 → 0.2574 ✅ |
| d=3 (A4) | 0,6593 → 0.6593 ✅ | 0,9007 → 0.9007 ✅ |
| d=4 | 0,6113 → 0.6113 ✅ | 0,9007 → 0.9007 ✅ |
| d=5 | 0,5838 → 0.5838 ✅ | 0,8760 → 0.876 ✅ |

### Ablation (semua Δ cocok, rounding ±0.001)

| Ablation | Δ RetQ (tesis) | Δ RetQ (CSV) | Δ HopAcc (tesis) | Δ HopAcc (CSV) |
|----------|---------------|-------------|-----------------|----------------|
| A1 | −0,309 | 0.3088 ✅ | — | — |
| A2 | −0,656 | 0.6562 ✅ | −0,700 | 0.7002 ✅ |
| A3 | −0,123 | 0.1232 ✅ | −0,147 | 0.1472 ✅ |
| A4 | −0,050 n.s. | 0.0496 ✅ | +0,145 | 0.1445 ✅ |
| A5 | −0,057 | 0.0565 ✅ | — | — |
| A6c | −0,011 n.s. | 0.011 ✅ | — | — |
| A7 | −0,152 | 0.1516 ✅ | −0,232 | 0.232 ✅ |

### Boundary conditions (semua cocok)

| Kategori | Tesis | CSV |
|----------|-------|-----|
| followup | +0,664 | 0.6642 ✅ |
| yaml_gen | +0,545 | 0.545 ✅ |
| planning | +0,541 | 0.5406 ✅ |
| relationship | +0,354 | 0.354 ✅ |
| Spearman degree ρ | +0,245 (p=0,013, n=101) | Verified ✅ |
| Spearman hops ρ | −0,082 (p=0,414, n=102) | Verified ✅ |

### Konsistensi antar-bab (semua CONSISTENT)

| Klaim | Status |
|-------|--------|
| 725 node (Abstrak/BabV/BabVII) | ✅ |
| 18 jenis edge (Abstrak/BabIII/IV/V/VI/VII) | ✅ |
| 7 kategori relasi (Abstrak/BabIV/V/VII) | ✅ |
| 102/103 fixture (Abstrak/BabVI/VII) | ✅ |
| Intent→depth d=2 explain+followup; d=3 lainnya | ✅ |
| K8s v1.30 konsisten di semua bab | ✅ |
| GPT-4o-mini thinker+speaker (cocok dengan kode) | ✅ |
| "Groq" tidak muncul di tesis (cocok dengan kode) | ✅ |
| AnsQ/RetQ/ReaQ kapital sebagai nama dimensi | ✅ |
| "Answer Semantic Similarity" (Fase 5 sudah difix) | ✅ |
| Panel pakar 3 (fixture validation) vs 4 (answer validation) — sudah dibedakan eksplisit | ✅ |
| Temperature 0,0 thinker / 0,1 speaker (Bab V); protokol "speaker 0,1 ketiga sistem" (Bab VI) — tidak kontradiksi | ✅ |
| tabel29.tex (orphan, nilai lama) — tidak di-\input, tidak muncul di dokumen kompilasi | ✅ |
| followup (all bab kecuali Bab I) | ✅ (Bab I menjadi G3) |

### Terminologi (CONSISTENT di semua bab kecuali satu)

| Istilah | Status |
|---------|--------|
| `\textit{followup}` (Bab V, VI, VII, tables) | ✅ |
| `\textit{follow-up}` di Bab I §61 | ❌ → **G3** |
| Edge type `\textit{CAPS_CASE}` di listings/tabel | ✅ |
| AnsQ/RetQ/ReaQ sebagai dimensi (bukan nama kolom CSV) | ✅ |
| *fixture* (konsisten, bukan "test case") | ✅ |
| swagger.json + v1.30 | ✅ |

---

## Ringkasan fix per grup

### G1 — Angka AnsQ tabel-depth.tex
**File:** `docs/TA-STI-template-1.0/tables/tabel-depth.tex`  
**Perubahan:**
- d=1: `0,7602` → `0,7815`
- d=4: `0,7548` → `0,7828`
- d=5: `0,7611` → `0,7817`

### G2 — Klausa penjelas gap node
**File:** `docs/TA-STI-template-1.0/Bab V - Implementasi.tex`  
**Perubahan:** Tambah 1 kalimat setelah "542 node sub-resource" di §38 menjelaskan mengapa 730 EDA → 725 node (5 tipe internal apimachinery di IGNORE_LIST).

### G3 — Terminologi follow-up → followup
**File:** `docs/TA-STI-template-1.0/Bab I - Pendahuluan.tex`  
**Perubahan:** §61 `\textit{follow-up}` → `\textit{followup}`

---

## Status fix

| ID | Verdict | Status |
|----|---------|--------|
| M1 | MISMATCH → G1 | ✅ FIXED (2026-06-28) |
| M2 | MISMATCH → G1 | ✅ FIXED (2026-06-28) |
| M3 | MISMATCH → G1 | ✅ FIXED (2026-06-28) |
| M4 | MISMATCH → G2 | ✅ FIXED (2026-06-28) |
| C1 | CLARIFY → RESOLVED: pertahankan 0,3055 (n=95) | ✅ RESOLVED (user decision 2026-06-28) |
| G3 | MISMATCH → G3 | ✅ FIXED (2026-06-28) |
