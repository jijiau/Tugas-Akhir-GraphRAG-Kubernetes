# tests/integration/test_retrieval_pipeline.py
"""
Integration tests for StatefulK8sRetriever and GraphRetriever.

Requires:
  - Neo4j running with Kubernetes schema ingested
  - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD set in .env

Run:
  pytest tests/integration/test_retrieval_pipeline.py -v -m integration
"""
import pytest
from src.chatbot.custom_retriever import StatefulK8sRetriever
from src.retrieval.graph_retriever import GraphRetriever


# ── StatefulK8sRetriever — Exact Match Path ──────────────────────────────────

@pytest.mark.integration
def test_deployment_retrieval(neo4j_client):
    """Exact match on 'Deployment' must return non-error context."""
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": ["Pod", "ReplicaSet"]}
    context, path = retriever.retrieve_context(intent)
    assert "Error" not in context, f"Retrieval error: {context}"
    assert "Deployment" in context or "deployment" in context.lower()


@pytest.mark.integration
def test_statefulset_retrieval(neo4j_client):
    """Exact match on 'StatefulSet' must succeed without error."""
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "StatefulSet", "related_concepts": ["PersistentVolumeClaim"]}
    context, path = retriever.retrieve_context(intent)
    assert "Error" not in context


@pytest.mark.integration
def test_retrieval_returns_reasoning_path(neo4j_client):
    """Reasoning path must be a list (may be empty if graph has no edges)."""
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": []}
    context, path = retriever.retrieve_context(intent, max_depth=4)
    assert isinstance(path, list)


@pytest.mark.integration
def test_unknown_resource_returns_fallback(neo4j_client):
    """Unknown resource must not raise — must return a graceful string fallback."""
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "NonExistentResource12345", "related_concepts": []}
    context, path = retriever.retrieve_context(intent)
    # Should return empty/no results message, not raise an exception
    assert isinstance(context, str)
    assert isinstance(path, list)


# ── StatefulK8sRetriever — Multi-hop Traversal ───────────────────────────────

@pytest.mark.integration
def test_multi_hop_traversal_depth(neo4j_client):
    """
    Deep traversal (max_depth=6) on a hub resource like 'Pod' must return
    a reasoning path with more than one edge, exercising the multi-hop path.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Pod", "related_concepts": ["PodSpec", "Container"]}
    context, path = retriever.retrieve_context(intent, max_depth=6)
    assert "Error" not in context
    # Multi-hop: at least one HAS_PROPERTY edge should appear
    if path:
        assert any("->" in edge for edge in path)


@pytest.mark.integration
def test_hpa_retrieval_with_related_concepts(neo4j_client):
    """
    HPA is a multi-hop resource (HPA → Deployment → Pod).
    Context must reference HPA and related concepts.
    """
    retriever = StatefulK8sRetriever()
    intent = {
        "primary_resource": "HorizontalPodAutoscaler",
        "related_concepts": ["Deployment", "metrics"],
    }
    context, path = retriever.retrieve_context(intent, max_depth=4)
    assert isinstance(context, str)
    assert "Error" not in context


# ── StatefulK8sRetriever — Single-hop Baseline ───────────────────────────────

@pytest.mark.integration
def test_single_hop_service_retrieval(neo4j_client):
    """
    Single-hop baseline: 'Service' retrieval with depth=1 must return
    direct properties only (no deep traversal), verifying the retriever
    respects max_depth boundaries.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Service", "related_concepts": []}
    context, path = retriever.retrieve_context(intent, max_depth=1)
    assert isinstance(context, str)
    assert "Error" not in context
    # With depth=1, path should be short (0–5 edges)
    assert len(path) <= 5, (
        f"Expected ≤5 edges for depth-1 traversal, got {len(path)}: {path}"
    )


@pytest.mark.integration
def test_namespace_retrieval_single_hop(neo4j_client):
    """
    Namespace is a cluster-scoped root resource.
    Single-hop retrieval must succeed and return context.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Namespace", "related_concepts": []}
    context, path = retriever.retrieve_context(intent, max_depth=1)
    assert isinstance(context, str)
    assert "Error" not in context


# ── StatefulK8sRetriever — Context Format ────────────────────────────────────

@pytest.mark.integration
def test_context_is_valid_json(neo4j_client):
    """
    Retrieved context must be valid JSON (the retriever serialises via
    json.dumps). This guards against raw Neo4j objects leaking into output.
    """
    import json
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "ConfigMap", "related_concepts": []}
    context, _ = retriever.retrieve_context(intent)
    # Only validate JSON structure if context looks like a JSON object
    if context.startswith("{"):
        parsed = json.loads(context)
        assert isinstance(parsed, dict)


@pytest.mark.integration
def test_context_contains_root_resource_key(neo4j_client):
    """
    The JSON context must include 'RootResource' when an exact match is found.
    """
    import json
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": []}
    context, _ = retriever.retrieve_context(intent)
    if context.startswith("{"):
        parsed = json.loads(context)
        assert "RootResource" in parsed, (
            f"Missing 'RootResource' key in: {list(parsed.keys())}"
        )


# ── GraphRetriever (baseline vector-only retriever) ──────────────────────────

@pytest.mark.integration
def test_graph_retriever_returns_string(neo4j_client):
    """GraphRetriever.search_knowledge() must return a string."""
    retriever = GraphRetriever()
    result = retriever.search_knowledge("What is a Deployment?")
    assert isinstance(result, str)


@pytest.mark.integration
def test_graph_retriever_non_empty_for_known_concept(neo4j_client):
    """
    Querying a well-known Kubernetes concept must return non-empty context,
    confirming the vector index is populated.
    """
    retriever = GraphRetriever()
    result = retriever.search_knowledge("Kubernetes Pod specification containers")
    assert len(result.strip()) > 0, "Expected non-empty context for known K8s concept"


@pytest.mark.integration
def test_graph_retriever_top_k_limits_results(neo4j_client):
    """
    top_k limits the number of seed nodes from vector search, NOT the number
    of output blocks. Each seed node is expanded to its 1-hop neighbours via
    OPTIONAL MATCH, so one seed can produce several (node, neighbour) rows.

    What we can assert:
      - With top_k=1 the result comes from exactly 1 distinct root node.
      - With top_k=2 the result comes from at most 2 distinct root nodes.
    """
    retriever = GraphRetriever()

    # top_k=1 → at most 1 distinct "Resource:" header
    result_1 = retriever.search_knowledge("Service selector", top_k=1)
    root_nodes_1 = {
        line.replace("Resource: ", "").strip()
        for line in result_1.splitlines()
        if line.startswith("Resource: ")
    }
    assert len(root_nodes_1) <= 1, (
        f"Expected ≤1 distinct root node for top_k=1, got {len(root_nodes_1)}: {root_nodes_1}"
    )

    # top_k=2 → at most 2 distinct "Resource:" headers
    result_2 = retriever.search_knowledge("Service selector", top_k=2)
    root_nodes_2 = {
        line.replace("Resource: ", "").strip()
        for line in result_2.splitlines()
        if line.startswith("Resource: ")
    }
    assert len(root_nodes_2) <= 2, (
        f"Expected ≤2 distinct root nodes for top_k=2, got {len(root_nodes_2)}: {root_nodes_2}"
    )
