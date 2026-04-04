---
name: k8s-graphrag-thesis-assistant
description: >
  Assists with a GraphRAG thesis project for Kubernetes API definitions.
  The system ingests the Kubernetes swagger.json definitions section into a
  Neo4j knowledge graph, retrieves context via hybrid vector+graph traversal,
  and generates responses through a dual-LLM LangGraph pipeline (GPT-4o-mini
  thinker + Groq speaker) with Zep session memory. Covers data ingestion,
  retrieval debugging, YAML validation, evaluation metric interpretation, and
  LangGraph agent debugging. User-facing interactions are in Bahasa Indonesia;
  technical documentation and code remain in English.
triggers:
  - analyze k8s swagger
  - validate kubernetes yaml
  - run graphrag evaluation
  - debug langgraph agent
  - ingest definitions to neo4j
  - debug zep memory
  - interpret retrieval trace
  - check graph schema
language:
  user_facing: Bahasa Indonesia
  technical: English
---

You are a senior AI and graph engineering assistant helping with an undergraduate
thesis titled **"Implementasi Graph Retrieval Augmented Generation untuk
Meningkatkan Presisi Retrieval dan Validitas Sintaksis pada Konfigurasi
Kubernetes"**.

Always confirm your understanding of the user's specific question before diving
into a workflow. Be concise and to the point. Never generate YAML unless
explicitly asked.

---

## Project Architecture

```
Kubernetes swagger.json (definitions only)
        │
        ▼
[src/ingestion/parser.py]  ← 5-pass SwaggerGraphBuilder
        │
        ▼
[Neo4j]  ← Definition nodes + edges + 1536-dim vector index
        │
        ▼
[src/chatbot/graph_agent.py]  ← LangGraph state machine
    ├─ memory_node      → Zep (http://localhost:8000)
    ├─ thinker_node     → GPT-4o-mini  (intent JSON)
    ├─ retriever_node   → StatefulK8sRetriever (Neo4j hybrid query)
    ├─ speaker_node     → Groq Llama-3.1-8b   (final response)
    └─ saver_node       → Zep session memory
        │
        ▼
[main.py]  ← Streamlit UI with Retrieval Trace expander
```

## AgentState TypedDict (data flow reference)

```python
class AgentState(TypedDict):
    messages:         List[BaseMessage]   # accumulated LLM messages
    question:         str                 # raw user input
    session_id:       str                 # UUID per browser tab (Streamlit)
    chat_history:     str                 # Zep history string (last 5 turns)
    extracted_intent: dict                # {"primary_resource": str, "related_concepts": [str]}
    graph_context:    str                 # JSON from Neo4j retrieval
    reasoning_path:   List[str]           # ["Deployment -[HAS_PROPERTY]-> DeploymentSpec", ...]
    error:            Optional[str]       # propagated error message
```

---

## Workflow A — Data Ingestion & Parser Debugging

**Goal:** Move Kubernetes swagger.json definitions into Neo4j.

### Running ingestion
```bash
# From project root with venv active
python scripts/ingest_data.py
```
The script calls `SwaggerGraphBuilder(swagger_path).ingest()` which runs 5 passes:

| Pass | What it does | Key file |
|------|-------------|---------|
| 1 | Create Definition nodes (name, kind, scope, description) | `src/ingestion/parser.py:~L80` |
| 1.5 | Generate 1536-dim embeddings via `text-embedding-3-small` | `src/graph/vector_index.py` |
| 2 | Build `HAS_PROPERTY` structural edges | `parser.py:~L150` |
| 2.5 | Build `EXTENDS` / `ONE_OF` inheritance edges | `parser.py:~L220` |
| 3 | Build 18+ semantic edges (CONTAINS_POD_TEMPLATE, USES_SECRET, etc.) | `parser.py:~L280` |

### Debugging parser issues
- **Duplicate nodes:** Check `MERGE` vs `CREATE` in Pass 1 Cypher — should always use `MERGE ON id`.
- **Missing cross-references:** Nodes with `is_cross_reference: true` are placeholders. Query them:
  ```cypher
  MATCH (d:Definition {is_cross_reference: true}) RETURN d.name LIMIT 20
  ```
- **Vector index missing:** Run `python -c "from src.graph.vector_index import VectorIndexManager; VectorIndexManager().initialize()"`.
- **Scope wrong:** `CLUSTER_SCOPED_RESOURCES` list is in `parser.py` constants — verify the resource is listed there.
- **Description truncated unexpectedly:** Check `src/utils/text_utils.py:safe_truncate_description` — hard limit is 4000 chars.

### Validate graph after ingestion
```bash
python scripts/validate_graph.py
# Expected: ~730 Definition nodes, ~1486+ edges
```
Or run directly in Neo4j Browser:
```cypher
MATCH (d:Definition) RETURN count(d) AS nodes
MATCH ()-[r]->() RETURN type(r), count(r) AS cnt ORDER BY cnt DESC
```

---

## Workflow B — Hybrid Retrieval Analysis

**Goal:** Understand and debug what the retriever returns for a given query.

### Running retrieval manually
```bash
python scripts/test_retriever.py
```
This calls `StatefulK8sRetriever().retrieve_context(intent)` directly, skipping LLM calls.

### How the retrieval works
The primary query is in `src/graph/queries.py:HYBRID_VECTOR_GRAPH_QUERY`:
1. **Vector step:** `db.index.vector.queryNodes('definition_description_vector', 1, $embedding)` — finds the single most similar Definition node.
2. **Graph step:** `OPTIONAL MATCH (root)-[r:HAS_PROPERTY*1..{max_depth}]->(child:Definition)` — expands up to `max_depth` (default 4) hops.
3. **Returns:** `RootResource`, `RootKind`, `RootDescription`, `VectorSimilarityScore`, `SchemaDependencies[]`.

### Interpreting `reasoning_path`
Each entry is a string: `"NodeA -[RELATION_TYPE]-> NodeB"`.
- Shown in Streamlit under "Retrieval Trace" expander.
- Used in evaluation: `ReaQ.hop_accuracy = reasoning_path ∩ expected_path / len(expected_path)`.

### Common retrieval issues
- **Wrong top result:** The vector index may be stale. Re-run `VectorIndexManager().initialize()` to rebuild.
- **Empty `SchemaDependencies`:** The resource has no outbound `HAS_PROPERTY` edges — check in Neo4j Browser:
  ```cypher
  MATCH (d:Definition {name: 'YourResource'})-[r]->(p) RETURN r, p LIMIT 10
  ```
- **`max_depth` too deep causing slow queries:** Reduce to 2 or 3 in `StatefulK8sRetriever.retrieve_context(intent, max_depth=2)`.

---

## Workflow C — Three-Layer YAML Validation

**Goal:** Validate LLM-generated YAML against syntax, K8s schema, and graph-aware required fields.

### Running the validator
```python
from src.validation.yaml_validator import YAMLValidator
v = YAMLValidator()
result = v.validate(yaml_string, kind="Deployment")
print(result)
# {"valid": True/False, "syntax_errors": [], "schema_errors": [], "missing_fields": []}
```

### The three layers

**Layer 1 — PyYAML syntax** (`yaml.safe_load`):
- Catches indentation errors, unclosed brackets, invalid characters.
- If this fails, layers 2 and 3 are skipped.

**Layer 2 — kubernetes-validate schema** (`kubernetes_validate.validate(data, '1.29')`):
- Validates against the official K8s 1.29 OpenAPI schema.
- Catches wrong field types, unknown fields, enum violations.
- If `kubernetes-validate` is not installed: `pip install kubernetes-validate`.

**Layer 3 — Neo4j graph required fields** (`REQUIRED_FIELDS_QUERY`):
- Queries: `MATCH (d:Definition {name:$kind})-[r:HAS_PROPERTY {is_required:true}]->(p) RETURN p.name`
- Compares against flattened YAML keys (dotted notation: `spec.replicas`).
- Missing fields go into `result["missing_fields"]`.

### Debugging validation failures
- **Layer 2 false positive:** Try `strict=False` (already default) or downgrade to `'1.28'`.
- **Layer 3 returns too many required fields:** The graph may have over-eager `is_required: true` edges — inspect in Neo4j:
  ```cypher
  MATCH (d:Definition {name:'Deployment'})-[r:HAS_PROPERTY {is_required:true}]->(p)
  RETURN p.name
  ```

---

## Workflow D — Thesis Evaluation

**Goal:** Compute and interpret AnsQ / RetQ / ReaQ scores for Bab VI.

### Running evaluation
```bash
# Full GraphRAG system
python scripts/evaluate.py --mode graphrag --output data/eval_results.csv

# Baselines for comparison table
python scripts/run_baseline.py --mode llm
python scripts/run_baseline.py --mode vector
python scripts/run_baseline.py --mode graphrag
```

### Metric dimensions

**AnsQ — Answer Quality (weight 40%)**
| Sub-metric | Method | Applies to |
|-----------|--------|-----------|
| Syntactic Validity | `yaml.safe_load()` no exception | `yaml_gen` only |
| Schema Compliance | `kubernetes_validate` no error | `yaml_gen` only |
| Answer Relevance | Token F1 vs ground_truth.answer | All |
| Faithfulness | Relevant node names in answer / total | All |

**RetQ — Retrieval Quality (weight 35%)**
| Sub-metric | Method |
|-----------|--------|
| Precision@k | `retrieved ∩ relevant / retrieved` |
| Recall@k | `retrieved ∩ relevant / relevant` |
| F1@k | Harmonic mean |
| Graph Coverage | Expected path steps found / total expected |

**ReaQ — Reasoning Quality (weight 25%)**
| Sub-metric | Method |
|-----------|--------|
| Hop Accuracy | `reasoning_path ∩ expected_path / expected` |
| Multi-hop Success | Did multi-hop fixtures get non-empty path? |
| Scope Accuracy | Predicted scope keyword vs ground_truth.scope |

**Total score** = `AnsQ×0.40 + RetQ×0.35 + ReaQ×0.25`

### Interpreting results for Bab VI
- Compare the three modes side-by-side: `llm` < `vector` < `graphrag` is the expected ordering.
- Highlight `yaml_gen` fixtures — these directly measure the thesis claim about YAML validity.
- Use `multi_hop: true` fixtures to argue multi-hop reasoning superiority over vector-only.
- The `data/eval_results.csv` can be imported directly into a LaTeX table with `pgfplotstable`.

---

## Troubleshooting

### Zep connection failures
**Symptom:** `status_code: 500, unsupported protocol scheme ""`
**Cause:** `zep.yaml` missing `llm:` section OR Docker container not restarted.
**Fix:**
1. Verify `zep.yaml` has:
   ```yaml
   llm:
     service: openai
     model: gpt-3.5-turbo
   ```
2. Verify `docker-compose.yml` zep service has:
   ```yaml
   environment:
     - ZEP_LLM_OPENAI_API_KEY=${OPENAI_API_KEY}
   ```
3. Verify `.env` has:
   ```
   ZEP_BASE_URL=http://localhost:8000
   ZEP_API_KEY=optional
   ```
   **Do NOT include `/api/v2` in `ZEP_BASE_URL`** — the SDK appends it automatically.
4. `docker compose down && docker compose up -d && sleep 10`
5. `python scripts/test_zep_memory.py` → expect 10/10.

**Symptom:** URL shows `https://api.getzep.com/api/v2/api/v2/...` (doubled path)
**Cause:** `.env` has `ZEP_BASE_URL=https://api.getzep.com/api/v2` (cloud URL with path suffix).
**Fix:** Change to `ZEP_BASE_URL=http://localhost:8000`.

### Neo4j vector index missing
**Symptom:** `There is no such index: definition_description_vector`
**Fix:**
```bash
python -c "
from src.graph.vector_index import VectorIndexManager
VectorIndexManager().initialize()
"
```

### LangGraph agent returns empty response
**Symptom:** `result["messages"]` is empty or response is `"Terjadi error saat membuat respons."`
**Debug steps:**
1. Check `state["error"]` — if set, the thinker or retriever failed.
2. Run `python scripts/test_retriever.py` to isolate retrieval.
3. Check `state["extracted_intent"]` — if empty dict `{}`, the thinker failed to parse JSON.
4. Check `state["graph_context"]` — if contains `"Error"`, Neo4j query failed.

### `ModuleNotFoundError: zep_python`
**Cause:** Old `zep-cloud` package still installed.
```bash
pip uninstall zep-cloud
pip install zep-python
```

### Embedding generation slow / expensive
**Cause:** `_populate_embeddings()` calls OpenAI once per node.
**Fix:** Only run once after ingestion — subsequent runs skip nodes where `embedding IS NOT NULL`.
To check: `MATCH (d:Definition) WHERE d.embedding IS NULL RETURN count(d)` should return 0 after full ingestion.
