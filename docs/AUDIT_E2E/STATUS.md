# STATUS — Audit E2E TA GraphRAG-Kubernetes

> Pelacak progres lintas-sesi. **Update di akhir tiap sesi** (status + handoff notes). Baca bersama `CHARTER.md`.

## Ringkasan fase

| Fase | Judul | Status | Dok detail | Artefak |
|------|-------|--------|-----------|---------|
| -1 | Setup scaffolding | ✅ DONE (2026-06-09) | — | CHARTER, STATUS, STYLE_GUIDE, memory |
| 0 | Diagnosis forensik (read-only) | ✅ DONE (2026-06-09) | `phases/FASE_0.md` | `bug_register.md`, `metric_suitability.md`, `critical_review.md` |
| 1 | Perbaiki measurement (kode) | ⬜ TODO | `phases/FASE_1.md` | — |
| 2 | Re-kurasi GT fixture (data) | ⬜ TODO | `phases/FASE_2.md` | `fixture_fix_log.md` |
| 3 | Re-run evaluasi penuh | ⬜ TODO | `phases/FASE_3.md` | `_final` CSV baru |
| 4 | Update angka + Bab II evaluasi | ⬜ TODO | `phases/FASE_4.md` | `traceability_matrix.md` |
| 5 | Alignment Bab I & konsistensi | ⬜ TODO | `phases/FASE_5.md` | — |
| 6 | Audit bahasa | ⬜ TODO | `phases/FASE_6.md` | `language_violations.md` |
| 7 | Whitespace & keterbacaan PDF | ⬜ TODO | `phases/FASE_7.md` | — |
| 8 | Compile final & verifikasi | ⬜ TODO | `phases/FASE_8.md` | — |

Legend: ✅ done · 🔶 in-progress · ⬜ todo

## Urutan disarankan
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Fase 1 & 2 sama-sama prasyarat Fase 3 (re-run). Fase 4–7 setelah angka final stabil.

## Handoff notes (terbaru di atas)

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
