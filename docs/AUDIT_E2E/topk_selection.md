# top-k Selection — Roles, Rationale, and Deferred Sweep

> Created: Fase 1 (2026-06-14). Part of F7' reconciliation (zero code change; documentation only).

## Three k values in the codebase — why they differ

There are three distinct top-k knobs in the codebase. They live in separate retrieval paths and serve different purposes. **Unifying them would be cosmetically tidy but methodologically misleading.**

| Knob | Location | Value | Path | Controls |
|------|----------|-------|------|----------|
| HYBRID seed k | `queries.py:HYBRID_VECTOR_GRAPH_QUERY` | **1** | GraphRAG production (Phase-2 vector fallback in `custom_retriever._vector_deps`) | Which single root node seeds multi-hop traversal |
| GraphRetriever k | `src/retrieval/graph_retriever.py:15` | **3** | `run_baseline.py` / integration tests only | Cosine-only baseline (not in `evaluate.py`) |
| eval vector k | `scripts/evaluate.py:604` | **5** | `--mode vector` in evaluation pipeline | The only k that directly moves thesis metrics |

---

## Knob 1 — HYBRID seed k = 1

**Code:** `HYBRID_VECTOR_GRAPH_QUERY` (queries.py line 122) uses `CALL db.index.vector.queryNodes(..., 1, $embedding)` — hardcoded 1, not parameterized.

**Consumer:** `custom_retriever._vector_deps` returns `dict(rows[0])`. The consumer picks only the top-1 row regardless of k, so raising the seed k to 3 or 5 would be a no-op without a multi-root rework (iterating multiple seeds, merging context and paths, deduplicating).

**Rationale:** Breadth of retrieved context comes from multi-hop traversal depth (1–3), not from seeding multiple root nodes. A single seed + depth-3 graph traversal already brings in hundreds of schema nodes. Multiple seeds would risk merging unrelated resource branches and inflating context irrelevantly.

**What a multi-root seed would give:** running `k=3` seeds and merging would be an explicit extension with its own tradeoffs — it is not obviously better and would confound the GraphRAG-vs-Vector comparison by adding an extra dimension. If explored, it belongs to a dedicated ablation, not a silent k change.

**Deferred to:** Fase 3 (empirical verification with Neo4j online) — if a multi-root seed sweep is desired, frame it as an explicit ablation with controlled intent types.

---

## Knob 2 — GraphRetriever k = 3

**Code:** `src/retrieval/graph_retriever.py:15` — `def search_knowledge(self, query: str, top_k: int = 3)`.

**Consumer:** `scripts/run_baseline.py:47` and integration tests. **This path is NOT used by `scripts/evaluate.py`** — it is only used by the interactive baseline runner and tests.

**Impact on thesis metrics:** Zero. The evaluation pipeline (`evaluate.py`) uses an inline `SIMPLE_VECTOR_QUERY` (k=5), not `GraphRetriever.search_knowledge`. This k value therefore does not affect any reported number.

**Action:** No code change. Documented here so the discrepancy between README (which references GraphRetriever) and evaluate.py is explicit.

---

## Knob 3 — eval vector k = 5 (the authoritative eval knob)

**Code:** `scripts/evaluate.py:604` — `_db.execute_query(SIMPLE_VECTOR_QUERY, {"embedding": embedding, "top_k": 5})`.

**Query:** `SIMPLE_VECTOR_QUERY` (queries.py) — pure dense top-k vector retrieval with **no** graph expansion (`OPTIONAL MATCH` absent). This was fixed in F1 from the previous `SIMPLE_GRAPH_EXPAND_QUERY` (which had a 1-hop `HAS_PROPERTY|EXTENDS|CONTAINS_POD_TEMPLATE` expansion, making the "vector" baseline partially graph-based).

**This is the only k that directly moves thesis metrics.** The choice k=5 is a standard information retrieval default (top-5 recall). Empirical sweep k∈{1,3,5,10} is deferred to Fase 3 to select the domain-optimal value with real numbers.

**Deferred sweep:** Fase 3 will run `--mode vector` with k∈{1,3,5,10} and pick the k that maximizes RetQ on the held-out eval set. The selected k will be reported as a hyperparameter in Bab V.

---

## README reconciliation (F7')

`README.md` (line ~247) described the `vector` baseline as:
> `vector` — `GraphRetriever.search_knowledge()` (cosine similarity only)

This is **inaccurate for the evaluation path.** The evaluation uses `SIMPLE_VECTOR_QUERY` (k=5, pure dense) via `evaluate.py`, not `GraphRetriever`. README has been updated to reflect this.

`GraphRetriever.search_knowledge()` (k=3) is used only by `run_baseline.py` — the interactive chatbot baseline runner. It also wraps the now-corrected `SIMPLE_GRAPH_EXPAND_QUERY` (which still has 1-hop expansion). If the interactive baseline also needs a pure-dense vector path, that is a separate future task.

---

## Summary

| Decision | Rationale |
|----------|-----------|
| Keep HYBRID seed=1 | Consumer is single-root; raising k is a no-op without multi-root rework |
| Keep GraphRetriever k=3 | Not in eval path; no thesis metric impact |
| Keep eval vector k=5 | Standard IR default; sweep deferred to Fase 3 with real numbers |
| Eval vector = SIMPLE_VECTOR_QUERY | Pure dense (F1 fix); former SIMPLE_GRAPH_EXPAND_QUERY was a hybrid |
| No unification | Three knobs serve three distinct roles; cosmetic unification would obscure the architecture |
