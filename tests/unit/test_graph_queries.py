# tests/unit/test_graph_queries.py
# Verify that Cypher constants are importable and well-formed strings.
import pytest

pytestmark = pytest.mark.unit

from src.graph.queries import (
    HYBRID_VECTOR_GRAPH_QUERY,
    SIMPLE_GRAPH_EXPAND_QUERY,
    REQUIRED_FIELDS_QUERY,
    ALL_FIELDS_QUERY,
)


def test_hybrid_query_has_placeholder():
    assert "{max_depth}" in HYBRID_VECTOR_GRAPH_QUERY


def test_hybrid_query_formats_correctly():
    cypher = HYBRID_VECTOR_GRAPH_QUERY.format(max_depth=4)
    assert "1..4" in cypher
    assert "$embedding" in cypher
    assert "RootResource" in cypher
    assert "SchemaDependencies" in cypher


def test_simple_query_has_top_k():
    assert "$top_k" in SIMPLE_GRAPH_EXPAND_QUERY
    assert "$embedding" in SIMPLE_GRAPH_EXPAND_QUERY


def test_required_fields_query_has_param():
    assert "$kind" in REQUIRED_FIELDS_QUERY
    assert "is_required" in REQUIRED_FIELDS_QUERY


def test_all_fields_query_has_param():
    assert "$kind" in ALL_FIELDS_QUERY
