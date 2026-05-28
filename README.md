---
title: K8s GraphRAG Chatbot
sdk: docker
app_port: 7860
pinned: false
---

# Thesis GraphRAG-Kubernetes Implementation

## Project Overview

This is an undergraduate thesis project building a **GraphRAG chatbot for Kubernetes** using only the `definitions` section of `data/kubernetes_swagger.json`. The system ingests Kubernetes API definitions into a Neo4j knowledge graph, performs hybrid retrieval (exact match + vector similarity + multi-hop graph traversal), and generates answers through a dual-LLM pipeline (GPT-4o-mini "thinker" for intent extraction, Groq LLaMA "speaker" for response generation). The UI is Streamlit.

### Architecture

```
User Question
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Agent Pipeline  (src/chatbot/graph_agent.py)     │
│                                                             │
│  memory → thinker → retriever → speaker → saver → END      │
│    │         │          │          │         │              │
│  SQLite    GPT-4o    Neo4j      Groq      SQLite            │
│  Memory    -mini     Exact+     LLaMA     Memory            │
│            (intent   Vector+    (answer)                    │
│            +type)    Graph                                  │
│                      Traversal                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Streamlit UI  (main.py)
```

### Key Directory Structure

```
repo/
├── main.py                          # Streamlit entry point
├── docker-compose.yml               # Postgres (pgvector) — legacy, tidak aktif dipakai
├── requirements.txt                 # Python dependencies
├── data/
│   ├── kubernetes_swagger.json      # Full Kubernetes OpenAPI spec
│   ├── definitions.json             # Extracted definitions section
│   ├── conversation_memory.db       # SQLite conversation memory (auto-generated)
│   └── traceability_matrix.csv      # Dataset coverage traceability
├── src/
│   ├── config/settings.py           # Pydantic settings (env vars)
│   ├── chatbot/
│   │   ├── graph_agent.py           # LangGraph state machine (AgentState)
│   │   ├── custom_retriever.py      # Hybrid vector+graph retriever
│   │   ├── llm_factory.py           # LLM provider initialization
│   │   └── prompts.py               # INTENT_PROMPT, RESPONSE_PROMPT
│   ├── graph/
│   │   ├── neo4j_client.py          # Neo4j driver wrapper
│   │   ├── vector_index.py          # Embedding generation + index mgmt
│   │   └── queries.py               # Named Cypher query constants
│   ├── ingestion/
│   │   └── parser.py                # Swagger → Neo4j graph ingestion
│   ├── memory/
│   │   └── zep_store.py             # SQLite conversation memory (ZepMemoryStore API)
│   ├── retrieval/
│   │   └── graph_retriever.py       # Simpler vector-only retriever
│   ├── validation/
│   │   ├── yaml_validator.py        # PyYAML + kubernetes-validate + Neo4j
│   │   └── auditor.py               # Graph health audit (node/edge counts)
│   ├── analysis/
│   │   ├── eda_base.py              # EDA base class
│   │   ├── entity_analysis.py       # Entity distribution analysis
│   │   ├── text_analysis.py         # Description text analysis
│   │   └── schema_analysis.py       # Schema structure analysis
│   ├── utils/
│   │   └── text_utils.py            # Text utility helpers (e.g. safe_truncate_description)
│   └── models/
│       └── swagger_models.py        # Pydantic models for swagger parsing
├── scripts/
│   ├── smoke_test.py                # Quick system health check
│   ├── test_retriever.py            # Retriever integration test
│   ├── ingest_data.py               # Run graph ingestion
│   ├── evaluate.py                  # 3-dimension evaluation (AnsQ/RetQ/ReaQ)
│   ├── run_baseline.py              # Baseline comparison (llm/vector/graphrag)
│   └── validate_dataset.py          # Dataset validity (YAML GT, paths, traceability)
└── tests/                           # pytest suite
    ├── conftest.py                  # Shared fixtures, parametrization
    ├── fixtures/                    # Expert-validated eval question JSONs
    │   ├── conceptual/              # Definitional/explanation questions
    │   ├── yaml_gen/                # YAML generation tasks
    │   ├── relationship/            # Multi-hop relationship questions
    │   ├── followup/                # Context-dependent follow-up questions
    │   └── realworld/               # Questions from Stack Overflow answers
    ├── unit/                        # Isolated component tests
    ├── integration/                 # Live service tests
    ├── smoke/                       # Fixture-based smoke tests
    └── evaluation/                  # Metric function tests
```

## Critical Code Patterns

### AgentState (src/chatbot/graph_agent.py)

All data flows through `AgentState` TypedDict:
```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    session_id: str
    chat_history: str
    extracted_intent: dict
    intent_type: Optional[str]            # explain|generate_yaml|trace_relationship|followup|planning
    graph_context: str
    reasoning_path: Optional[List[str]]   # graph traversal trace
    error: Optional[str]
```

### Intent-Aware Retrieval Depth

The thinker extracts `intent_type` which controls graph traversal depth:
```python
_DEPTH_BY_INTENT = {
    "explain":             2,
    "followup":            2,
    "generate_yaml":       3,
    "trace_relationship":  3,
    "planning":            3,
}
_DEFAULT_DEPTH = 3
```

### Neo4j Graph Schema

Nodes: `Definition` (with properties: `name`, `kind`, `description`, `fullName`)

Edges (18 types):
- `HAS_PROPERTY` (with: `name`, `is_required`, `is_array`) — structural properties
- `EXTENDS`, `ONE_OF`, `ANY_OF` — type system / inheritance
- `CONTAINS_POD_TEMPLATE`, `CONTAINS_JOB_TEMPLATE` — template embedding
- `HAS_CONTAINER` — PodSpec → Container
- `CLAIMS_VOLUME`, `MOUNTS_VOLUME`, `USES_STORAGE_CLASS` — storage relationships
- `USES_SECRET`, `LOADS_CONFIGMAP`, `USES_SERVICE_ACCOUNT` — config injection
- `SELECTS_POD`, `ROUTES_TO_SERVICE` — networking
- `BINDS_ROLE`, `BINDS_SERVICE_ACCOUNT` — RBAC
- `SCALES_RESOURCE` — HPA scaling targets

Vector index: `definition_description_vector` on `Definition.embedding` property (1536-dim, cosine).

### Settings (src/config/settings.py)

All config loaded from `.env` via Pydantic:
- `neo4j_uri`, `neo4j_username`, `neo4j_password`
- `openai_api_key`, `groq_api_key`
- `thinker_model` (default `gpt-4o-mini`), `speaker_model` (default `llama-3.1-8b-instant`)
- `environment` (default `development`)

### Cypher Queries (src/graph/queries.py)

All Cypher strings live here as named constants. Key queries:
- `EXACT_MATCH_QUERY` — exact/suffix name match, used as Phase 1 retrieval
- `SCHEMA_DEPS_QUERY` — multi-hop `HAS_PROPERTY` expansion from root node
- `HYBRID_VECTOR_GRAPH_QUERY` — vector search + `HAS_PROPERTY` expansion fallback
- `PATH_EDGES_QUERY` — traverses all 18 edge types for reasoning path construction (uses `_ALL_EDGE_TYPES` constant)
- `SIMPLE_GRAPH_EXPAND_QUERY` — 1-hop expansion for baseline/simple retriever
- `REQUIRED_FIELDS_QUERY` — required field lookup for YAML validation
- `ALL_FIELDS_QUERY` — all properties for a resource

`PATH_EDGES_QUERY` uses Python `.format(max_depth=N)` substitution — the `{max_depth}` placeholder is single-brace (not `{{max_depth}}`).

### YAML Validation (src/validation/yaml_validator.py)

Three-layer validation:
1. `yaml.safe_load()` — syntax
2. `kubernetes_validate.validate(data, '1.29')` — K8s schema compliance (no cluster needed)
3. Neo4j `REQUIRED_FIELDS_QUERY` — graph-aware required field check

### Test Fixtures (tests/fixtures/)

Each fixture is an expert-validated JSON:
```json
{
  "id": "deployment_basic",
  "type": "conceptual|yaml_gen|relationship|followup",
  "question": "...",
  "resource": "io.k8s.api.apps.v1.Deployment",
  "scope": "Namespaced|Cluster",
  "multi_hop": false,
  "ground_truth": {
    "answer": "...",
    "context": ["node: description", ...],
    "relevant_nodes": ["io.k8s..."],
    "expected_path": ["A -[REL]-> B", ...],
    "required_fields": [],
    "expected_yaml_keys": []
  },
  "source_reference": "https://kubernetes.io/docs/...",
  "api_reference": "https://kubernetes.io/docs/reference/..."
}
```

Realworld fixtures additionally include `so_url` and `so_answer_score` for Stack Overflow provenance.

### Evaluation Metrics (scripts/evaluate.py)

Three custom dimensions, no ragas:

| Dimension | Weight | Metrics |
|-----------|--------|---------|
| **AnsQ** (Answer Quality) | 40% | Syntactic Validity, Schema Compliance, Graph-Field Compliance, Faithfulness (node name overlap), Answer Relevance (cosine similarity via `text-embedding-3-small`) |
| **RetQ** (Retrieval Quality) | 35% | Precision@k, Recall@k, F1@k, Graph Coverage, NDCG@k, Edge Coverage |
| **ReaQ** (Reasoning Quality) | 25% | Hop Accuracy, Multi-Hop Success Rate, Scope Accuracy (conditional — skipped for non-scope questions), Hallucination Rate (vocabulary-based: Neo4j canonical terms) |

Weighted total: `AnsQ*0.4 + RetQ*0.35 + ReaQ*0.25`

**v3 Evaluation Results (GraphRAG mode, 79 fixtures):**
| Metric | Score |
|--------|-------|
| AnsQ   | 0.6235 |
| RetQ   | 0.5541 |
| ReaQ   | 0.7468 |
| **Total** | **0.6300** |

### Dataset Validity (scripts/validate_dataset.py)

Five validity efforts producing reports in `data/`:
1. **source_reference** — every fixture links to official kubernetes.io docs
2. **SO metadata** — realworld fixtures link to Stack Overflow answers with score > 5
3. **YAML GT validation** — syntactic + schema validation of YAML ground truths
4. **Traceability matrix** — maps fixture types × question types × K8s domains
5. **Neo4j path validation** — verifies each `expected_path` edge exists in the graph

```bash
python scripts/validate_dataset.py          # requires Neo4j running
python scripts/validate_dataset.py --skip-neo4j  # offline mode
```

### Baseline Comparison (scripts/run_baseline.py)

Three modes via `--mode` flag:
- `llm` — GPT-4o-mini only, no retrieval
- `vector` — `GraphRetriever.search_knowledge()` (cosine similarity only)
- `graphrag` — full `create_agent_graph()` pipeline with multi-hop

## Infrastructure

- **Neo4j**: External (connection via `NEO4J_URI` in `.env`)
- **Conversation Memory**: SQLite lokal (`data/conversation_memory.db`) — tidak butuh Docker, zero token cost. Diimplementasikan di `src/memory/zep_store.py` dengan class `ZepMemoryStore` sebagai drop-in replacement dari Zep v1 yang sebelumnya dipakai.
- **LLMs**: OpenAI (thinker) + Groq (speaker), keys in `.env`
- **docker-compose.yml**: Hanya berisi Postgres service (legacy dari implementasi Zep sebelumnya) — tidak aktif dipakai.

## Constraints

- Budget: ~1M IDR for 6 months — minimize LLM token usage
- Conversation memory menggunakan SQLite lokal (zero token, zero Docker dependency) sebagai pengganti Zep v1
- Groq free tier: 6.000 tokens/minute — graph_context di-truncate ke 12.000 chars sebelum dikirim ke speaker
- All evaluations use custom metrics (no ragas dependency)
- YAML validation uses `kubernetes-validate` library (no live cluster required)
- Language: Indonesian (Bahasa Indonesia) for user-facing text, English for code/docs
