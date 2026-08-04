# tests/unit/test_graph_queries.py
# Verify that Cypher constants are importable and well-formed strings.
import pytest

pytestmark = pytest.mark.unit

from src.graph.queries import (
    SCHEMA_DEPS_QUERY,
    HYBRID_VECTOR_GRAPH_QUERY,
    PATH_EDGES_QUERY,
    SIMPLE_GRAPH_EXPAND_QUERY,
    SIMPLE_VECTOR_QUERY,
    REQUIRED_FIELDS_QUERY,
    ALL_FIELDS_QUERY,
    _ALL_EDGE_TYPES,
)


def test_hybrid_query_has_placeholders():
    # F14: context queries now carry BOTH placeholders, substituted at call time.
    assert "{max_depth}" in HYBRID_VECTOR_GRAPH_QUERY
    assert "{all_edges}" in HYBRID_VECTOR_GRAPH_QUERY


def test_hybrid_query_formats_correctly():
    cypher = HYBRID_VECTOR_GRAPH_QUERY.format(max_depth=4, all_edges="HAS_PROPERTY")
    assert "1..4" in cypher
    assert "$embedding" in cypher
    assert "RootResource" in cypher
    assert "SchemaDependencies" in cypher


@pytest.mark.parametrize("query", [SCHEMA_DEPS_QUERY, HYBRID_VECTOR_GRAPH_QUERY, PATH_EDGES_QUERY])
def test_context_queries_support_edge_set_substitution(query):
    # F14: default = all 18 edges; the has_property_only ablation restricts to one.
    assert "{all_edges}" in query
    all_edge_cypher = query.format(max_depth=3, all_edges=_ALL_EDGE_TYPES)
    assert "SELECTS_POD" in all_edge_cypher          # a semantic edge is present
    assert "ROUTES_TO_SERVICE" in all_edge_cypher
    restricted_cypher = query.format(max_depth=3, all_edges="HAS_PROPERTY")
    assert "SELECTS_POD" not in restricted_cypher     # ablation drops semantic edges
    assert "HAS_PROPERTY" in restricted_cypher


def test_all_edge_types_has_18_relations():
    assert len(_ALL_EDGE_TYPES.split("|")) == 18
    assert "HAS_PROPERTY" in _ALL_EDGE_TYPES


def test_simple_vector_query_is_pure_dense():
    # F1: the eval Vector baseline must NOT do graph expansion.
    assert "$top_k" in SIMPLE_VECTOR_QUERY
    assert "$embedding" in SIMPLE_VECTOR_QUERY
    assert "OPTIONAL MATCH" not in SIMPLE_VECTOR_QUERY   # no 1-hop expansion
    # The old baseline (production GraphRetriever) DOES expand — kept for that path.
    assert "OPTIONAL MATCH" in SIMPLE_GRAPH_EXPAND_QUERY


def test_simple_query_has_top_k():
    assert "$top_k" in SIMPLE_GRAPH_EXPAND_QUERY
    assert "$embedding" in SIMPLE_GRAPH_EXPAND_QUERY


def test_required_fields_query_has_param():
    assert "$kind" in REQUIRED_FIELDS_QUERY
    assert "is_required" in REQUIRED_FIELDS_QUERY


def test_all_fields_query_has_param():
    assert "$kind" in ALL_FIELDS_QUERY
