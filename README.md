# Skill: Thesis GraphRAG-Kubernetes Implementation
 
## Project Overview
 
This is an undergraduate thesis project building a **GraphRAG chatbot for Kubernetes** using only the `definitions` section of `data/kubernetes_swagger.json`. The system ingests Kubernetes API definitions into a Neo4j knowledge graph, performs hybrid retrieval (vector similarity + multi-hop graph traversal), and generates answers through a dual-LLM pipeline (GPT-4o-mini "thinker" for intent extraction, Groq LLaMA "speaker" for response generation). The UI is Streamlit.
 
### Architecture
 
```
User Question
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Agent Pipeline  (src/chatbot/graph_agent.py)     │
│                                                             │
│  memory → thinker → retriever → speaker → saver → END      │
│    │         │          │          │         │               │
│  Zep       GPT-4o    Neo4j      Groq      Zep              │
│  Store     -mini     Vector+    LLaMA     Store             │
│            (intent)  Graph      (answer)                    │
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
├── docker-compose.yml               # Postgres (pgvector) + Zep v1
├── zep.yaml                         # Zep server config (LLM + extractors)
├── requirements.txt                 # Python dependencies
├── data/
│   ├── kubernetes_swagger.json      # Full Kubernetes OpenAPI spec
│   └── definitions.json             # Extracted definitions section
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
│   │   ├── parser.py                # Swagger → Neo4j graph ingestion
│   │   └── runner.py                # Ingestion orchestrator
│   ├── memory/
│   │   └── zep_store.py             # Zep memory + in-process fallback
│   ├── retrieval/
│   │   └── graph_retriever.py       # Simpler vector-only retriever
│   ├── validation/
│   │   ├── yaml_validator.py        # PyYAML + kubernetes-validate + Neo4j
│   │   ├── auditor.py               # Graph health audit (node/edge counts)
│   │   └── rules.py                 # Validation rule constants
│   └── models/
│       └── swagger_models.py        # Pydantic models for swagger parsing
├── scripts/
│   ├── smoke_test.py                # Quick system health check
│   ├── test_retriever.py            # Retriever integration test
│   ├── ingest_data.py               # Run graph ingestion
│   ├── evaluate.py                  # 3-dimension evaluation (AnsQ/RetQ/ReaQ)
│   └── run_baseline.py              # Baseline comparison (llm/vector/graphrag)
└── tests/                           # pytest suite (microsoft/graphrag style)
    ├── conftest.py                  # Shared fixtures, parametrization
    ├── fixtures/                    # Expert-validated eval question JSONs
    │   ├── conceptual/
    │   ├── yaml_gen/
    │   ├── relationship/
    │   └── followup/
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
    graph_context: str
    reasoning_path: Optional[List[str]]   # graph traversal trace
    error: Optional[str]
```
 
### Neo4j Graph Schema
 
Nodes: `Definition` (with properties: `name`, `kind`, `description`, `fullName`)
Edges: `HAS_PROPERTY` (with: `name`, `is_required`, `is_array`), `EXTENDS`, `ONE_OF`, `ANY_OF`, plus semantic edges like `CONTAINS_POD_TEMPLATE`, `CLAIMS_VOLUME`, `SELECTS_POD`, `BINDS_ROLE`, etc.
 
Vector index: `definition_description_vector` on `Definition.description` embeddings.
 
### Settings (src/config/settings.py)
 
All config loaded from `.env` via Pydantic:
- `neo4j_uri`, `neo4j_username`, `neo4j_password`
- `zep_base_url` (default `http://localhost:8000`), `zep_api_key`
- `openai_api_key`, `groq_api_key`
- `thinker_model` (default `gpt-4o-mini`), `speaker_model` (default `llama-3.1-8b-instant`)
 
### Cypher Queries (src/graph/queries.py)
 
All Cypher strings live here as named constants. Retrievers import from here:
- `HYBRID_VECTOR_GRAPH_QUERY` — vector search + multi-hop `HAS_PROPERTY*1..{max_depth}` expansion
- `SIMPLE_GRAPH_EXPAND_QUERY` — 1-hop semantic relationship expansion
- `REQUIRED_FIELDS_QUERY` — required field lookup for YAML validation
 
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
  }
}
```
 
### Evaluation Metrics (scripts/evaluate.py)
 
Three custom dimensions, no ragas:
 
| Dimension | Weight | Metrics |
|-----------|--------|---------|
| **AnsQ** (Answer Quality) | 40% | Syntactic Validity, Schema Compliance, Graph-Field Compliance, Faithfulness (LLM judge), Answer Relevance (F1 token overlap) |
| **RetQ** (Retrieval Quality) | 35% | Precision@k, Recall@k, F1@k, Graph Coverage, Edge Coverage |
| **ReaQ** (Reasoning Quality) | 25% | Hop Accuracy, Multi-Hop Success Rate, Scope Accuracy, Hallucination Rate (LLM judge) |
 
Weighted total: `AnsQ*0.4 + RetQ*0.35 + ReaQ*0.25`
 
### Baseline Comparison (scripts/run_baseline.py)
 
Three modes via `--mode` flag:
- `llm` — GPT-4o-mini only, no retrieval
- `vector` — `GraphRetriever.search_knowledge()` (cosine similarity only)
- `graphrag` — full `create_agent_graph()` pipeline with multi-hop
 
## Infrastructure
 
- **Neo4j**: External (connection via `NEO4J_URI` in `.env`)
- **Zep v1**: `zepai/zep:1.0.2` via `docker-compose.yml`, with Postgres (`ankane/pgvector:v0.5.1`)
  - Config: `zep.yaml` mounted at `/app/zep.yaml`
  - Env: `ZEP_LLM_OPENAI_API_KEY` passed from `.env`'s `OPENAI_API_KEY`
- **LLMs**: OpenAI (thinker) + Groq (speaker), keys in `.env`
 
## Constraints
 
- Budget: ~1M IDR for 6 months — minimize LLM token usage
- Zep summarization uses `gpt-3.5-turbo` (cheapest), `message_window: 24` to reduce call frequency
- `intent` and `questions` extractors disabled in `zep.yaml` to save tokens
- All evaluations use custom metrics (no ragas dependency)
- YAML validation uses `kubernetes-validate` library (no live cluster required)
- Language: Indonesian (Bahasa Indonesia) for user-facing text, English for code/docs
