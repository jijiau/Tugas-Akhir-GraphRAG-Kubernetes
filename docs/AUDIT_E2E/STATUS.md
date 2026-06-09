# STATUS — Audit E2E TA GraphRAG-Kubernetes

> Pelacak progres lintas-sesi. **Update di akhir tiap sesi** (status + handoff notes). Baca bersama `CHARTER.md`.

## Ringkasan fase

| Fase | Judul | Status | Dok detail | Artefak |
|------|-------|--------|-----------|---------|
| -1 | Setup scaffolding | ✅ DONE (2026-06-09) | — | CHARTER, STATUS, STYLE_GUIDE, memory |
| 0 | Diagnosis forensik (read-only) | ⬜ TODO | `phases/FASE_0.md` | `bug_register.md`, `metric_suitability.md` |
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

### 2026-06-09 — Fase -1 selesai
- Scaffolding dibuat: `CHARTER.md`, `STATUS.md`, `STYLE_GUIDE.md`, `memory/audit-e2e-charter.md` (+ pointer di `MEMORY.md`).
- Belum ada perubahan kode/data/tesis.
- **Langkah berikut:** buka sesi baru → "Detailkan & kerjakan Fase 0 audit E2E". Fase 0 read-only (diagnosis), hasilkan `bug_register.md` + `metric_suitability.md`.
- Reminder: maks 3–4 subagent serentak (limit sesi pernah kena di 9 agen). Neo4j sudah menyala & bisa diakses.

## Catatan angka baseline (untuk perbandingan setelah re-run)
GraphRAG `_final`: AnsQ 0,5771 · RetQ 0,6631 · ReaQ 0,7602 · PathCov 0,8515 · HopAcc 0,3505 · RGA 0,4536 · YAML syntactic 0,8947 (n=19) · schema 0,7895.
Vector `_final`: AnsQ 0,5916 · RetQ 0,3677 · ReaQ 0,6615 · HopAcc 0,0 · RGA 0,2784.
LLM `_final`: AnsQ 0,5956 · RetQ 0,0 · ReaQ 0,5981 · HopAcc 0,0722 · RGA 0,0206.
RAGAS by mode: faithfulness 0,1838 (n=49) · answer_relevancy 0,6191 (n=95) · ctx_precision 0,3190 (n=62) · ctx_recall 0,3813 (n=62).
