# src/graph/queries.py
# Centralized Cypher query constants — single source of truth for all graph queries.

# ---------------------------------------------------------------------------
# Exact name match — cari root node berdasarkan nama persis.
# Digunakan sebelum vector search untuk memastikan precision.
# Parameter: $primary_resource (str)
# ---------------------------------------------------------------------------
EXACT_MATCH_QUERY = """
MATCH (d:Definition)
WHERE d.name = $primary_resource
   OR d.name ENDS WITH ('.' + $primary_resource)
RETURN d.name AS name, d.kind AS kind, d.description AS description
ORDER BY
  CASE WHEN d.name = $primary_resource THEN 0 ELSE 1 END
LIMIT 1
"""

# ---------------------------------------------------------------------------
# Schema dependencies (flat list) — untuk LLM context.
# Dipanggil setelah root ditemukan (exact match atau vector).
# Parameter: $root_name (str), $max_depth (int)
# ---------------------------------------------------------------------------
SCHEMA_DEPS_QUERY = """
MATCH (root:Definition {{name: $root_name}})
OPTIONAL MATCH (root)-[r:HAS_PROPERTY*1..{max_depth}]->(child:Definition)

WITH root, r, child

WITH root,
     CASE
         WHEN child IS NOT NULL AND r IS NOT NULL THEN {{
             path_depth:       size(r),
             relation_type:    type(last(r)),
             yaml_field:       last(r).name,
             is_array:         coalesce(last(r).is_array, false),
             child_resource:   child.name,
             child_description: substring(child.description, 0, 150)
         }}
         ELSE null
     END AS dep

RETURN root.name        AS RootResource,
       root.kind        AS RootKind,
       root.description AS RootDescription,
       1.0              AS VectorSimilarityScore,
       collect(dep)     AS SchemaDependencies
"""

# ---------------------------------------------------------------------------
# Path edges — untuk reasoning path (Explainable AI).
# Mengembalikan pasangan parent->child yang sebenarnya di setiap hop,
# bukan root->leaf. Digunakan untuk display trace di Streamlit.
# Parameter: $root_name (str), max_depth via .format()
# ---------------------------------------------------------------------------
PATH_EDGES_QUERY = """
MATCH p = (root:Definition {{name: $root_name}})-[:HAS_PROPERTY*1..{max_depth}]->(leaf:Definition)
WITH p
LIMIT 500
WITH [i IN range(0, size(nodes(p))-2) | {{
    parent: nodes(p)[i].name,
    child:  nodes(p)[i+1].name,
    depth:  i + 1
}}] AS edges
UNWIND edges AS edge
RETURN DISTINCT edge.parent AS parent,
                edge.child  AS child,
                edge.depth  AS depth
ORDER BY edge.depth ASC, edge.parent ASC
LIMIT 50
"""

# ---------------------------------------------------------------------------
# Primary retrieval (vector fallback) — digunakan saat exact match gagal.
# Parameter: $embedding (list[float]), max_depth via .format()
# ---------------------------------------------------------------------------
HYBRID_VECTOR_GRAPH_QUERY = """
CALL db.index.vector.queryNodes('definition_description_vector', 1, $embedding)
YIELD node AS root, score

OPTIONAL MATCH (root)-[r:HAS_PROPERTY*1..{max_depth}]->(child:Definition)

WITH root, score, r, child

WITH root, score,
     CASE
         WHEN child IS NOT NULL AND r IS NOT NULL THEN {{
             path_depth:        size(r),
             relation_type:     type(last(r)),
             yaml_field:        last(r).name,
             is_array:          coalesce(last(r).is_array, false),
             child_resource:    child.name,
             child_description: substring(child.description, 0, 150)
         }}
         ELSE null
     END AS dep

RETURN root.name        AS RootResource,
       root.kind        AS RootKind,
       root.description AS RootDescription,
       score            AS VectorSimilarityScore,
       collect(dep)     AS SchemaDependencies
"""

# ---------------------------------------------------------------------------
# Simple vector search with 1-hop expansion (baseline / GraphRetriever)
# Used by: src/retrieval/graph_retriever.py, scripts/run_baseline.py
# ---------------------------------------------------------------------------
SIMPLE_GRAPH_EXPAND_QUERY = """
CALL db.index.vector.queryNodes('definition_description_vector', $top_k, $embedding)
YIELD node, score
OPTIONAL MATCH (node)-[r:HAS_PROPERTY|EXTENDS|CONTAINS_POD_TEMPLATE]-(related)
RETURN node.fullName, node.description, related.fullName, r, score
ORDER BY score DESC
"""

# ---------------------------------------------------------------------------
# Fetch required fields for a given resource kind from the graph
# Used by: src/validation/yaml_validator.py
# ---------------------------------------------------------------------------
REQUIRED_FIELDS_QUERY = """
MATCH (d:Definition {name: $kind})-[r:HAS_PROPERTY {is_required: true}]->(p)
RETURN p.name AS field_name
"""

# ---------------------------------------------------------------------------
# Fetch all properties for a resource (required + optional)
# Used by: src/validation/yaml_validator.py
# ---------------------------------------------------------------------------
ALL_FIELDS_QUERY = """
MATCH (d:Definition {name: $kind})-[r:HAS_PROPERTY]->(p)
RETURN p.name AS field_name, r.is_required AS is_required
"""
