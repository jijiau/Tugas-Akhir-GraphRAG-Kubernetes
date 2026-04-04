# tests/integration/test_retrieval_pipeline.py
# Requires live Neo4j connection. Run with: pytest tests/integration/ -v
import pytest
from src.chatbot.custom_retriever import StatefulK8sRetriever


@pytest.mark.integration
def test_deployment_retrieval(neo4j_client):
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": ["Pod", "ReplicaSet"]}
    context, path = retriever.retrieve_context(intent)
    assert "Error" not in context, f"Retrieval error: {context}"
    assert "Deployment" in context or "deployment" in context.lower()


@pytest.mark.integration
def test_statefulset_retrieval(neo4j_client):
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "StatefulSet", "related_concepts": ["PersistentVolumeClaim"]}
    context, path = retriever.retrieve_context(intent)
    assert "Error" not in context


@pytest.mark.integration
def test_retrieval_returns_reasoning_path(neo4j_client):
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "Deployment", "related_concepts": []}
    context, path = retriever.retrieve_context(intent, max_depth=4)
    assert isinstance(path, list)


@pytest.mark.integration
def test_unknown_resource_returns_fallback(neo4j_client):
    retriever = StatefulK8sRetriever()
    intent = {"primary_resource": "NonExistentResource12345", "related_concepts": []}
    context, path = retriever.retrieve_context(intent)
    # Should return empty/no results message, not raise an exception
    assert isinstance(context, str)
    assert isinstance(path, list)
