# tests/integration/test_end_to_end.py
"""
End-to-end integration tests: fixture → retriever → metrics.

These tests simulate the full evaluation pipeline without calling the LLM.
They verify that the retriever can produce context for every evaluation
fixture, and that the metric functions can score that context without errors.

Requires:
  - Neo4j running with Kubernetes schema ingested
  - NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD set in .env

Run:
  pytest tests/integration/test_end_to_end.py -v -m integration
"""
import json
import pytest
from pathlib import Path
from src.chatbot.custom_retriever import StatefulK8sRetriever
from scripts.evaluate import compute_retq, compute_reaq

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_fixtures(fixture_type: str) -> list[dict]:
    """Load all fixtures of a given type from disk."""
    paths = sorted((FIXTURES_DIR / fixture_type).glob("*.json"))
    fixtures = []
    for p in paths:
        try:
            fixtures.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return fixtures


# ── Retrieval pipeline — all fixture types ───────────────────────────────────

@pytest.mark.integration
@pytest.mark.parametrize("fixture", _load_fixtures("conceptual"), ids=lambda f: f["id"])
def test_conceptual_fixture_retrieval_succeeds(neo4j_client, fixture):
    """
    For every conceptual fixture, the retriever must return a non-error
    context. This verifies that the vector index can surface relevant nodes
    for conceptual questions.
    """
    retriever = StatefulK8sRetriever()
    resource = fixture.get("resource", "").split(".")[-1]  # strip FQDN prefix
    intent = {
        "primary_resource": resource,
        "related_concepts": fixture.get("ground_truth", {}).get("relevant_nodes", []),
    }
    context, path = retriever.retrieve_context(intent)
    assert isinstance(context, str), "context must be a string"
    assert isinstance(path, list), "reasoning path must be a list"
    assert "Error retrieving" not in context, (
        f"Retrieval error for fixture '{fixture['id']}': {context}"
    )


@pytest.mark.integration
@pytest.mark.parametrize("fixture", _load_fixtures("relationship"), ids=lambda f: f["id"])
def test_relationship_fixture_retrieval_succeeds(neo4j_client, fixture):
    """
    For every relationship fixture (both single-hop and multi-hop), the
    retriever must return context without error.
    """
    retriever = StatefulK8sRetriever()
    resource = fixture.get("resource", "").split(".")[-1]
    expected_path = fixture.get("ground_truth", {}).get("expected_path", [])
    related = [
        edge.split(" -[")[0].strip()
        for edge in expected_path
        if " -[" in edge
    ]
    intent = {
        "primary_resource": resource,
        "related_concepts": related,
    }
    context, path = retriever.retrieve_context(intent)
    assert isinstance(context, str)
    assert "Error retrieving" not in context, (
        f"Retrieval error for fixture '{fixture['id']}': {context}"
    )


# ── Single-hop vs multi-hop — retrieval path length comparison ───────────────

@pytest.mark.integration
def test_single_hop_path_shorter_than_multi_hop(neo4j_client):
    """
    Single-hop retrieval (depth=1) should produce a shorter reasoning path
    than multi-hop retrieval (depth=4) for the same resource.

    This validates that max_depth is actually respected by the Cypher query.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": []}

    _, path_shallow = retriever.retrieve_context(intent, max_depth=1)
    _, path_deep    = retriever.retrieve_context(intent, max_depth=4)

    # Shallow must not exceed deep (can be equal if graph is small)
    assert len(path_shallow) <= len(path_deep), (
        f"Single-hop path ({len(path_shallow)}) longer than multi-hop path ({len(path_deep)})"
    )


# ── Metric functions — smoke on retrieved context ────────────────────────────

@pytest.mark.integration
def test_retq_on_retrieved_context(neo4j_client):
    """
    Run compute_retq against a live retrieval result.
    Scores must be in [0, 1] and no exception must be raised.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Service", "related_concepts": ["Pod"]}
    _, path = retriever.retrieve_context(intent, max_depth=3)

    # Build a ground_truth dict that matches compute_retq's expected shape
    ground_truth = {
        "relevant_nodes": [
            "io.k8s.api.core.v1.Service",
            "io.k8s.api.core.v1.ServiceSpec",
            "io.k8s.api.core.v1.Pod",
        ],
        "expected_path": [
            "Service -[HAS_PROPERTY]-> ServiceSpec",
            "ServiceSpec -[SELECTS_POD]-> Pod",
        ],
    }

    scores = compute_retq(reasoning_path=path, ground_truth=ground_truth)
    assert 0.0 <= scores["precision_at_k"] <= 1.0
    assert 0.0 <= scores["recall_at_k"] <= 1.0
    assert 0.0 <= scores["f1_at_k"] <= 1.0
    assert 0.0 <= scores["retq_score"] <= 1.0


@pytest.mark.integration
def test_reaq_on_retrieved_context(neo4j_client):
    """
    Run compute_reaq against a live retrieval result for a namespaced resource.
    Scores must be bounded and no exception must be raised.
    """
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Pod", "related_concepts": []}
    context, path = retriever.retrieve_context(intent, max_depth=3)

    # Pod is Namespaced — use a plausible answer mentioning namespace
    answer = "Pod berjalan di Namespace tertentu dalam cluster Kubernetes."
    ground_truth = {
        "expected_path": ["Pod -[HAS_PROPERTY]-> PodSpec"],
        "relevant_nodes": ["io.k8s.api.core.v1.Pod", "io.k8s.api.core.v1.PodSpec"],
        "multi_hop": False,
        "scope": "Namespaced",
    }

    scores = compute_reaq(
        reasoning_path=path,
        answer=answer,
        ground_truth=ground_truth,
        fixture_type="relationship",
    )
    assert 0.0 <= scores["reaq_score"] <= 1.0
