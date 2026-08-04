# FASE 1 — Perbaiki Measurement Apparatus (Kode)

> Status: ✅ DONE (2026-06-14)
> Prerequisite: Fase 0 (diagnosis) ✅ · Fase 2 (GT re-kurasi) ✅
> Next: Fase 3 (re-run evaluasi penuh dengan kode + GT yang sudah diperbaiki)

---

## Tujuan

Memperbaiki semua **RC=1 measurement bug** yang diidentifikasi Fase 0 sehingga angka yang dihasilkan Fase 3 valid secara metodologis. Tidak ada re-run di Fase 1 — hanya perbaikan kode + unit test hijau + import sanity.

**Guardrail integritas:** setiap perubahan = koreksi bug yang terbukti salah atau keputusan desain yang dikonfirmasi user. Nol tuning ambang demi melewati target 0,85.

---

## Keputusan desain terkunci (dikonfirmasi user di sesi ini)

| # | Keputusan | Rasional |
|---|-----------|----------|
| **F14 → Opsi A** | Rewire SCHEMA_DEPS_QUERY + HYBRID ke all-18-edge via `{all_edges}` parameter; ablation A7 (`has_property_only`) membuktikan T1 | T1 belum teruji dengan HAS_PROPERTY-only; ablation kontras = bukti kuantitatif |
| **F3 → edge-recall** | hop_accuracy = strict triplet-matching recall (Manning et al. 2008, recall applied to edge sets) | Formula lama (count-match len) adalah artefak; edge-recall adalah standar literatur |
| **F7' → rekonsiliasi (nol perubahan kode)** | Tiga k untuk tiga jalur berbeda; sweep empiris k∈{1,3,5,10} ditunda Fase 3 | Unifikasi kosmetik = menyesatkan; hanya dokumentasi yang diperlukan |
| **F15 → Symmetric** | GraphRAG vector-fallback embed pertanyaan asli (identik baseline) | Isolasi T1 bersih: satu-satunya beda GraphRAG vs Vector = traversal graf |

---

## Perubahan yang diterapkan

### F14 — Rewire konteks LLM ke 18 edge

**Bug:** `SCHEMA_DEPS_QUERY` dan `HYBRID_VECTOR_GRAPH_QUERY` hardcode `HAS_PROPERTY` — 14 edge semantik (SELECTS_POD, CONTAINS_POD_TEMPLATE, dll.) tidak pernah masuk konteks LLM. Klaim T1 tidak teruji.

**Fix:**
- `src/graph/queries.py`: `HAS_PROPERTY*1..{max_depth}` → `{all_edges}*1..{max_depth}` (call-time `.format()`, bukan load-time `.replace()`). Berlaku untuk SCHEMA_DEPS, HYBRID, dan PATH_EDGES queries.
- `src/chatbot/custom_retriever.py`: `retrieve_context` resolve `edge_types` dari `ablation_mode` — default `_ALL_EDGE_TYPES`; `ablation_mode=="has_property_only"` → `"HAS_PROPERTY"`. Semua private helper (`_schema_deps`, `_vector_deps`, `_build_reasoning_path`) menerima `edge_types`.
- `scripts/evaluate.py`: tambah `"has_property_only"` ke `_ABLATION_CHOICES`.
- `scripts/statistical_test.py`: tambah slot `"A7 (has_property_only)"` → `eval_results_ablation_A7.csv`.

**Bukti T1 (Fase 3):** jalankan default graphrag vs `--ablation has_property_only` → Δ RetQ/path_coverage/AnsQ. Laporkan jujur per-intent.

---

### F15 — Seed embedding simetris

**Bug/keputusan:** GraphRAG Phase-2 vector fallback embed keyword soup (`{primary} {related} Kubernetes`) sementara baseline embed pertanyaan asli. Perbedaan embedding = variabel pengganggu untuk T1.

**Fix:**
- `src/chatbot/custom_retriever.py:138`: `search_query = question.strip() if question and question.strip() else f"{primary} {' '.join(related)} Kubernetes"` — embed pertanyaan asli; keyword soup sebagai fallback defensive.
- `src/chatbot/graph_agent.py:108`: thread `question=state.get("question", "")` ke `retrieve_context`.
- Phase-1 exact-match tetap pakai entitas thinker (diablasi terpisah oleh A1/no_phase1).

---

### F1 — Vector baseline pure-dense

**Bug:** mode `vector` di `evaluate.py` menggunakan `SIMPLE_GRAPH_EXPAND_QUERY` yang punya 1-hop `OPTIONAL MATCH (root)-[:HAS_PROPERTY|EXTENDS|CONTAINS_POD_TEMPLATE]->(child)` — bukan pure-dense.

**Fix:**
- `src/graph/queries.py`: tambah `SIMPLE_VECTOR_QUERY` (pure `db.index.vector.queryNodes`, no OPTIONAL MATCH).
- `scripts/evaluate.py:604`: ganti query ke `SIMPLE_VECTOR_QUERY` (k=5 dipertahankan).
- `SIMPLE_GRAPH_EXPAND_QUERY` tetap ada untuk `GraphRetriever` production (tidak dihapus).

---

### F3 — HopAccuracy → edge-recall

**Bug:** formula lama `1.0 if len(reasoning_path)==len(expected_path) else 0.0` adalah artefak count-match; nilai 0,35 dalam hasil lama adalah kebetulan panjang.

**Fix (scripts/evaluate.py:385–393):**
```python
_exp_edges  = set(e.strip().lower() for e in expected_path)
_pred_edges = set(e.strip().lower() for e in reasoning_path)
hop_accuracy = len(_exp_edges & _pred_edges) / len(_exp_edges) if _exp_edges else 1.0
```

**Diagnostik tambahan:** `gt_depth` dan `n_roots` dikonsumsi dari GT fixture (Fase 2) dan dilaporkan sebagai kolom non-metrik di output CSV.

**Sitasi:** Manning et al. 2008 (recall applied to edge sets) — dicatat untuk prose Bab II/VI di Fase 4. ("Nguyen et al. 2024" ditolak: tidak ada di .bib, fabrikasi.)

---

### F6 — Docstring RetQ

**Bug:** docstring `compute_retq` klaim `(f1+ndcg+path_coverage)/3`; kode aktual = `(f1+ndcg)/2` + `path_coverage` dilaporkan terpisah.

**Fix:** docstring diperbarui sesuai kode.

---

### F7' — Rekonsiliasi top_k (nol perubahan kode)

**Situasi:** 3 nilai k untuk 3 jalur berbeda. Tidak ada yang salah; dokumentasi yang tidak sinkron.

**Fix:**
- Buat `docs/AUDIT_E2E/topk_selection.md`: dokumentasi peran tiap k + rasional.
- Update `README.md:247`: narasi baseline vektor diperbarui dari "GraphRetriever.search_knowledge()" ke "SIMPLE_VECTOR_QUERY k=5 (eval path)".
- Sweep empiris k∈{1,3,5,10} ditunda Fase 3.

---

### F8 — Ambang RGA didokumentasikan

**Bug/keputusan:** `0.5` di blok RGA gate tidak bernama dan tidak bersumber.

**Fix:** ekstrak ke konstanta `RGA_FAITHFULNESS_MIN`, `RGA_RELEVANCE_MIN`, `RGA_PATH_COVERAGE_MIN = 0.5` dengan komentar: midpoint konvensional, bukan dari Han 2024. Han 2024 dirujuk untuk konsep RGA gate, bukan nilai ambang.

---

### F12 — Schema validator → K8s 1.30

**Bug:** `kubernetes_validate.validate(data, "1.29", ...)` — tapi scope data adalah swagger.json K8s v1.30.

**Fix:** `"1.29"` → `"1.30"` di `src/validation/yaml_validator.py:45` dan `scripts/evaluate.py:206`.

---

### F10 — Dokumentasi Layer 3 ablation-only

**Perilaku benar by design.** L3 (YAML validation) hanya aktif di ablation. Tambah komentar penjelas di `evaluate.py`. Disclosure prose → Fase 4.

---

### F5 — Logging kegagalan RAGAS per-metrik

**Fix (`scripts/recompute_ragas.py`):** tambah `_skip_reasons` dict per fixture (reason: `"no_retrieval"` atau `"api_error_or_nan"`); setelah loop, log breakdown skip per metrik. Menjelaskan n-mismatch (88 vs 97) yang sebelumnya senyap.

---

### D5 — Flip bahasa speaker → Inggris

**Fix:**
- `src/chatbot/prompts.py:36`: "Respond in Indonesian unless requested otherwise." → "Respond in English unless the user explicitly requests another language."
- Semua sentinel string Inggris (`"No conversation history yet."`, `"No relevant Kubernetes schema found in the Knowledge Graph."`, OOD rejection).
- `src/chatbot/graph_agent.py`: `note_pattern` regex diperluas untuk menangkap varian bahasa Inggris + Indonesia; `_EMPTY_HISTORY` tuple diperbarui.

---

## Verifikasi

| Check | Hasil |
|-------|-------|
| `pytest tests/evaluation/test_metrics.py::TestComputeReaq -v` | ✅ 11/11 PASS |
| `python -c "import scripts.evaluate, src.graph.queries, src.chatbot.custom_retriever"` | ✅ OK |
| 16 failures lain di test_metrics.py | Pre-existing (TestFixtureDataIntegrity type='troubleshooting', TestSelectionGates) — unrelated to Fase 1 changes |

Smoke test dengan Neo4j online ditunda Fase 3 (tidak ada Neo4j di sesi ini).

---

## File yang diubah

| File | Perubahan |
|------|-----------|
| `src/graph/queries.py` | F14: `{all_edges}` placeholder; F1: SIMPLE_VECTOR_QUERY |
| `src/chatbot/custom_retriever.py` | F14: edge-set per ablation; F15: seed=question |
| `src/chatbot/graph_agent.py` | F15: thread question; D5: language strings |
| `src/chatbot/prompts.py` | D5: full English flip |
| `scripts/evaluate.py` | F1+F3+F6+F8+F10+F12+F14 |
| `scripts/statistical_test.py` | F14: slot A7 |
| `src/validation/yaml_validator.py` | F12: 1.30 |
| `scripts/recompute_ragas.py` | F5: per-metric skip logging |
| `tests/evaluation/test_metrics.py` | F3: TestComputeReaq edge-recall rewrite |
| `README.md` | F7': reconcile vector baseline narrative |
| `docs/AUDIT_E2E/topk_selection.md` | F7': baru |

---

## Handoff untuk Fase 3 (re-run)

1. **Checkpoint lama invalid** — F14 (edge-set) + D5 (bahasa) mengubah perilaku retrieval dan prompt. Re-run dari nol dengan kode baru + GT Fase 2. Snapshot pra-Fase-2 tersimpan di tag git `pre-fase2-fixtures`.

2. **Report before/after terpisah:**
   - Indonesia → Inggris (language flip D5)
   - GT lama → GT baru (Fase 2 re-kurasi, 103 fixture aktif)
   - HAS_PROPERTY-only → 18-edge (F14)

3. **Ablations baru di Fase 3:**
   - A7 (`has_property_only`) — kontras T1: 18-edge vs HAS_PROPERTY-only
   - A1 (`no_phase1`) — isolasi murni T1 (vector seed + 18-edge tanpa exact match)

4. **F16 (reliabilitas single-run):** keputuskan sebelum Fase 3 dimulai — run 1× vs 3× (mean±std), dan lock `temperature=0` bila Groq mendukung. Disclosure di Fase 4/6.

5. **Metrik berisiko intrinsik** (tidak dijamin ≥0,85 meski semua bug diperbaiki): AnsQ composite, RAGAS faithfulness, RAGAS ctx_precision/recall, RGA. Laporkan apa adanya.

---

## Handoff untuk Fase 4 (update prose)

- Sitasi Manning et al. 2008 di `.bib` + prose Bab II (hop_accuracy = recall applied to edge sets; "Nguyen et al. 2024" DITOLAK)
- Reframe hop_accuracy Bab VI (dari count-match ke strict triplet recall)
- Framing F14/T1: Bab IV (desain retrieval) + Bab VII (limitasi/kontribusi)
- F15 symmetry: Bab IV (peran thinker dalam retrieval) + Bab VI (pelaporan faktorial baseline/A1/full)
- F10 disclosure: "production AnsQ tidak mencakup L3 (YAML validation)"
- F8 disclosure: "ambang RGA 0.5 adalah midpoint konvensional, bukan dari Han 2024"
- F13 (validasi pakar n=4): klarifikasi ke user — bila tidak ada hasil, hapus/akui klaim
