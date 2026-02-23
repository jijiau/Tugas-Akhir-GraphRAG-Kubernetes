k8s-graphrag-thesis/
├── .env                  # Local secrets (NEO4J_URI, ZEP_KEY, etc.) - DO NOT COMMIT
├── .env.example          # Template for secrets - SAFE TO COMMIT
├── .gitignore            # Ignore .env, __pycache__, venv, data/*.json
├── requirements.txt      # Dependencies (Neo4j, Zep, LangChain, Streamlit)
├── README.md             # Setup instructions & Thesis overview
├── main.py               # Entry point for Streamlit UI
├── data/
│   └── kubernetes_swagger.json  # The 5MB source file (gitignored)
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py   # Pydantic settings loader (Security)
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── neo4j_client.py # Singleton DB connection
│   │   └── queries.py    # Centralized Cypher queries (DRY)
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py     # Semantic Stopping Logic (Your thesis core)
│   │   └── runner.py     # CLI script to trigger ingestion
│   ├── memory/
│   │   ├── __init__.py
│   │   └── zep_store.py  # Zep Cloud integration (Chat History)
│   ├── chatbot/
│   │   ├── __init__.py
│   │   ├── graph_agent.py   # LangGraph State Machine (Logic Only)
│   │   ├── prompts.py       # Centralized Prompt Templates (NEW)
│   │   └── retriever.py     # Neo4j Cypher Logic
│   ├── validation/          # NEW MODULE
│   │   ├── __init__.py
│   │   ├── auditor.py       # Cypher-based integrity checks
│   │   └── rules.py         # Validation rules (e.g., "No Orphans")
│   ├── models/
│   │   ├── __init__.py
│   │   └── swagger_models.py # Pydantic v2 validation schemas
│   └── ui/
│       ├── __init__.py
│       └── dashboard.py  # Streamlit components
├── scripts/
│   ├── ingest_data.py       # Runs ingestion
│   └── validate_graph.py    # Runs full DB audit (Thesis Requirement)Convenience script to run ingestion
├── tests/
│   ├── __init__.py
│   ├── test_parser.py    # Unit tests for Semantic Stopping
│   └── test_graph.py     # Integration tests for Neo4j
└── docs/
    └── architecture.md   # Thesis diagrams & logic explanations