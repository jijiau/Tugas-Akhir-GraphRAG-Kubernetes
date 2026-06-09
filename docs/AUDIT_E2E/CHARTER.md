# CHARTER — Audit & Alignment End-to-End TA GraphRAG-Kubernetes

> **Sumber kebenaran tunggal** untuk audit menyeluruh TA ini. Setiap sesi kerja audit WAJIB membaca file ini + `STATUS.md` lebih dulu. Dokumen ini stabil (jarang berubah); progres dilacak di `STATUS.md`; detail per-fase di `phases/FASE_X.md`; aturan bahasa di `STYLE_GUIDE.md`.

## Cara pakai (per sesi)
1. Buka chat baru → memory auto-load → ucap: **"Detailkan & kerjakan Fase X audit E2E"**.
2. Claude baca blok Fase X di Charter ini + `STATUS.md` → masuk plan mode → tulis `phases/FASE_X.md` rinci → user review/ubah.
3. Eksekusi HANYA fase itu, konfirmasi tiap perubahan.
4. Akhir sesi: update `STATUS.md` (status + handoff notes) + memory bila ada fakta durable + commit.

---

## Konteks & Tujuan

TA "Implementasi GraphRAG untuk Meningkatkan Presisi Retrieval dan Validitas Sintaksis pada Konfigurasi Kubernetes" (Jihan Aurelia, ITB). Audit menyeluruh 9 poin agar proyek selaras end-to-end, **tanpa hallucination** (semua klaim terbukti kuantitatif).

**/goal:** lantai keras **> 0,85 untuk SEMUA metrik evaluasi** *(diperbarui 2026-06-09 sesuai instruksi user)*.

**Framing yang dikoreksi (Fase 0, 2026-06-09):** hipotesis lama "angka rendah = measurement rusak" **ditolak sebagai asumsi**. Setiap skor rendah harus diatribusikan ke salah satu dari tiga kelas: (1) bug measurement, (2) bug gold-standard, atau (3) **defisiensi KG/mekanisme yang nyata**. Target >0,85 hanya sah tercapai sejauh kelas 1–2 dominan. Di mana kelas 3 yang nyata, angka tetap dilaporkan apa adanya di Bab VII — tidak di-tuning. Lihat `critical_review.md` untuk detail.

**Scope data (locked):** KG HANYA dari blok `definitions` swagger.json K8s v1.30. Tidak ada klaster aktif, tidak ada runtime `kubectl`. Tujuan (T1/T2/T3) & Rumusan Masalah **dikunci**. Studi literatur dikunci **kecuali sub-bab evaluasi**.

---

## ⚠ INTEGRITY GUARDRAIL (mengikat di semua fase)
1. Setiap perbaikan WAJIB koreksi bug yang **bisa dibuktikan salah** (melanggar literatur / struktur graf / scope definitions). Bukan tuning ambang demi melewati 0,80/0,85.
2. Target > 0,80 (mayoritas ≥ 0,85) = **hasil yang diharapkan** dari measurement benar, BUKAN target dipaksakan. Jika setelah koreksi jujur ada metrik tetap < 0,80, **laporkan apa adanya** + akar penyebab, diskusikan opsi sah; jangan fabrikasi.
3. `TA.tex` READ-ONLY (template Kaprodi). Perubahan hanya di `Bab *.tex`, `Lampiran-*.tex`, frontmatter, `tables/`, `listings/`, `images/`, `.bib`.
4. **Setiap perubahan dikonfirmasi user sebelum dieksekusi.**
5. Gaya bahasa ikut `docs/AUDIT_E2E/STYLE_GUIDE.md` (mandiri). JANGAN tarik aturan dari `CONTEXT_PRIMER.md`/`PHASE_7` agar konteks tak tercampur.

---

## Temuan terverifikasi (bukti langsung dari kode/data)

| ID | Temuan | Bukti | Dampak |
|----|--------|-------|--------|
| **F1** | Vector RAG tidak valid — vektor + ekspansi graf 1-hop | `graph_retriever.py:15-39`, `queries.py:141-147`, `evaluate.py:550-580` | Perbandingan GraphRAG-vs-Vector tidak sahih |
| **F2** | Ground-truth fixture terlalu lebar — dump seluruh subgraf seed | `tests/fixtures/command/kubectl_force_delete_pod.json`; mean n_relevant=24,8 / n_edges=28,4 | Menekan recall/F1/path_coverage/faithfulness artifisial |
| **F3** | "Hop Accuracy" salah label — `d_gt=len(expected_path)` ≈28,4 (bukan depth 1–5) | `evaluate.py:391-393`; tabel29c | HopAcc 0,3505 artefak (v18 def beda = 0,9072) |
| **F4** | Fixture out-of-scope — `command` jawab runtime `kubectl delete --force` | `kubectl_force_delete_pod.json:9` | Mencemari validitas domain |
| **F5** | RAGAS rusak/tak lengkap — faithfulness 0,18 (n=49), ctx_precision 0,32 (n=62) | `data/ragas_summary_by_mode.csv` | Angka RAGAS jauh di bawah |
| **F6** | Docstring `evaluate.py` basi (formula `/3` lama) | `evaluate.py:18-21` vs `:341,:416` | Bug komentar (kode benar) |
| **F7** | `top_k` tak konsisten — 3 (graph_retriever) vs 5 (evaluate vector) | `evaluate.py:561`, `graph_retriever.py:15` | Hardcode tanpa justifikasi |
| **F8** | Threshold RGA `0.5` hardcode | `evaluate.py:435,450-453` | Verifikasi sitasi GraphRAG-Bench Han 2024 di `.bib` |
| **F9** | ✅ DIAUDIT — 14 dari 18 edge hand-coded (Pass 3 `parser.py:324-371`); 4 struktural deterministik (HAS_PROPERTY/EXTENDS/ONE_OF/ANY_OF) | `src/ingestion/parser.py:228-371` | Klaim "auto-derived" tidak tepat; tesis harus menyebut hand-coded |
| **F10** | ✅ DIAUDIT — validator 3-lapis sehat; L3 hanya aktif saat ablation | `src/validation/yaml_validator.py:30-68`; `evaluate.py:240` | L3 tidak masuk production AnsQ |
| **F11** | ✅ DIAUDIT — intent 5 kategori LLM; statistik Wilcoxon+bootstrap+Holm-Bonferroni one-tailed; metodologi sehat | `prompts.py:15-20`; `statistical_test.py:119-183` | — |
| **F14** | **KRITIS (baru)** — KG 18-edge ter-dekopling dari generasi: context path HAS_PROPERTY-only, `PATH_EDGES_QUERY` all-18-edge hanya untuk display/metrik | `queries.py:26,110-113,85-103`; `graph_agent.py:102-109` | Klaim T1 tak terbukti; ceiling path_coverage ~87%; AnsQ < baseline |
| **F7′** | **Diperbarui** — 3 nilai top_k: prod seed=1, GraphRetriever=3, eval vector=5 | `queries.py:110`; `graph_retriever.py:15`; `evaluate.py:561` | Seed=1 cap recall; perlu sweep + dokumentasi |
| **F12** | **Baru** — schema validator memakai K8s 1.29 bukan 1.30 | `yaml_validator.py:45` | schema_compliance 0,7895 mungkin under-estimated |
| **F15** | **Baru** — embedding English-generic + keyword-soup query vs pertanyaan asli | `vector_index.py:15`; `custom_retriever.py:117` | Defisiensi retrieval nyata |
| **F13** | **Status pakar belum dikonfirmasi** — materi ada, hasil n=4 belum terlihat | `docs/validation/` | Klaim validasi eksternal pending |
| OK1 | Angka tesis konsisten dgn kode & `_final` CSV (tidak ada fabrikasi) | `data/eval_results_graphrag_final.csv` | — |
| OK2 | Depth mapping punya rasional struktural + ablation | `custom_retriever.py:33-39` | Defensible |
| OK3 | Batasan Masalah Bab I selaras scope | Bab I | Selaras |

**Baseline `_final` (sebelum perbaikan):** GraphRAG AnsQ 0,5771 / RetQ 0,6631 / ReaQ 0,7602 / PathCov 0,8515 / HopAcc 0,3505 / RGA 0,4536; YAML syntactic 0,8947 (n=19), schema 0,7895; RAGAS faithfulness 0,2125 (n=88), ctx_precision 0,3169, ctx_recall 0,3799. Hanya PathCov & YAML syntactic ≥0,85. **AnsQ GraphRAG < kedua baseline** (defisiensi genuine).

---

## Fase 0–8 (benih: objektif, file, exit criteria)

Detail granular tiap fase ditulis di `phases/FASE_X.md` saat sesi fase itu (lihat "Cara pakai").

### FASE 0 — Diagnosis forensik (READ-ONLY) → Bug Register
- **Objektif:** enumerasi SEMUA bug penekan metrik + estimasi dampak, sebelum sentuh kode.
- **Cakupan:** sweep 97 fixture (batch ~12/agen Haiku); audit mekanisme graf (`graph_agent.py`, `custom_retriever.py`); F9 (ingestion/parser, 18 edge); F10 (validator YAML); F11 (intent + statistik); RAGAS; status validasi pakar (n=4).
- **Deliverable:** `bug_register.md` + `metric_suitability.md` (per metrik: tujuan mana / sitasi / cocok scope / pertahankan-buang).
- **Exit:** tiap temuan ber-`file:line` + kuantifikasi dampak; tak ada perubahan kode/data.

### FASE 1 — Perbaiki measurement apparatus (kode) — *konfirmasi*
- **Objektif:** F1 Vector RAG → `SIMPLE_VECTOR_QUERY` pure top-k (tanpa ekspansi); F3 Hop Accuracy → depth 1–5 vs `gt_depth`; F6 docstring; F7 satukan top_k; F8 ambang RGA + sitasi; F5 RAGAS.
- **File:** `evaluate.py`, `queries.py`, `graph_retriever.py`, `tests/evaluation/test_metrics.py`, skrip RAGAS.
- **Exit:** `pytest test_metrics.py` hijau; Vector pure-dense; Hop Accuracy range 1–5.

### FASE 2 — Re-kurasi ground-truth fixture (data) — *konfirmasi*
- **Objektif:** kurasi `relevant_nodes`/`expected_path`/`key_nodes` ke kebutuhan nyata pertanyaan (dari `definitions` saja) + `gt_depth`; reklasifikasi `command` out-of-scope (F4).
- **File:** `tests/fixtures/**/*.json`, `scripts/validate_dataset.py`, `data/definitions.json`.
- **Deliverable:** `fixture_fix_log.md`. **Exit:** skrip validasi GT vs Neo4j lulus.

### FASE 3 — Re-run evaluasi penuh — *konfirmasi*
- **Objektif:** re-run 3 sistem + 9 ablation + depth sensitivity + RAGAS + uji statistik + boundary → `_final` CSV baru.
- **Exit:** selesai tanpa `error_flag`; cek metrik vs 0,80/0,85, lapor jujur.

### FASE 4 — Update angka tesis + sub-bab evaluasi Bab II (concern #4 & #1) — *konfirmasi*
- **Objektif:** update semua angka (Bab VI, Abstrak, Bab VII, tabel29-37); tulis ulang sub-bab evaluasi Bab II dari `metric_suitability.md`; **Matriks Traceability Tujuan↔Metrik↔Sitasi**.
- **Deliverable:** `traceability_matrix.md`. **Exit:** rantai Bab I→Bab II→Bab VI tak putus.

### FASE 5 — Alignment Bab I & konsistensi lintas-dokumen (concern #1) — *konfirmasi*
- **Objektif:** objektif/klaim selaras pasca-perubahan; nol pra-klaim keunggulan di Bab I–V; konsistensi istilah/scope.

### FASE 6 — Audit bahasa (concern #8) — *konfirmasi*
- **Objektif:** workflow per-bab (Haiku) berbasis `STYLE_GUIDE.md`. **Deliverable:** `language_violations.md`.

### FASE 7 — Whitespace & keterbacaan PDF (concern #9) — *konfirmasi*
- **Objektif:** perbaikan LOKAL (float `[H]`/`[htbp]`, `\includegraphics` width, `\resizebox`, `\vspace`, tabel `(lanjutan)`). Prioritas keterbacaan gambar & tabel. TA.tex tetap read-only.

### FASE 8 — Compile final & verifikasi
- `xelatex → biber → xelatex → xelatex`; mock penguji; cek silang angka tesis vs CSV final (nol mismatch).

---

## Teknik context window (wajib tiap fase)
1. Offload pembacaan berat ke subagent (maks 3–4 serentak; hindari limit sesi) → kembalikan ringkasan terstruktur.
2. Persist temuan ke artefak (`bug_register.md`, `metric_suitability.md`, `fixture_fix_log.md`, `traceability_matrix.md`, `language_violations.md`); fase berikut baca artefak, bukan kode mentah.
3. Baca slice (Grep → Read offset/limit), bukan whole-file.
4. Checkpoint ke `STATUS.md` sebelum context penuh.

## Catatan penting
- Limit sesi pernah kena saat 9 agen serentak (1,02 jt token). **Batasi 3–4 agen/batch.**
- Re-run penuh mahal/lama (97 fixture × banyak konfig); pakai checkpoint (`evaluate.py` sudah dukung resume).
- Perubahan GT fixture mengubah SEMUA metrik turunan → tabel & uji statistik wajib regen serempak.
- AnsQ answer_relevance (cosine) & RAGAS answer_relevancy bisa sulit ≥0,85 (bergantung kualitas jawaban referensi) → bila kurang, lapor jujur; kandidat perbaikan = pertajam jawaban referensi, bukan tuning ambang.

## Pointer
- Progres & handoff: `STATUS.md`
- Aturan bahasa: `STYLE_GUIDE.md`
- Detail fase: `phases/FASE_X.md`
- Plan asli (read-only): `~/.claude/plans/ultracode-audit-end-to-end-dari-luminous-spring.md`
