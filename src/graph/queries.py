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
# Traversal memakai SEMUA 18 tipe edge (default; F14) — caller mensubstitusi
# {all_edges} via .format(). Ablation 'has_property_only' menggantinya dengan
# "HAS_PROPERTY" saja untuk membuktikan kontribusi edge semantik (T1).
# Parameter: $root_name (str); {all_edges} + {max_depth} via .format()
# ---------------------------------------------------------------------------
SCHEMA_DEPS_QUERY = """
MATCH (root:Definition {{name: $root_name}})
OPTIONAL MATCH (root)-[r:{all_edges}*1..{max_depth}]->(child:Definition)

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
# All 18 relationship types in the K8s graph (default edge-set).
# Substituted at call time via .format(all_edges=...) into SCHEMA_DEPS_QUERY /
# HYBRID_VECTOR_GRAPH_QUERY (LLM context) and PATH_EDGES_QUERY (reasoning path
# → RetQ + path_coverage metrics). The 'has_property_only' ablation overrides
# this with "HAS_PROPERTY" alone to isolate the semantic-edge contribution
# (thesis T1, F14) on BOTH generation (context) and retrieval (path) metrics.
# Expanding beyond HAS_PROPERTY captures cross-resource relationships:
#   SCALES_RESOURCE      — HPA → Deployment/StatefulSet/ReplicaSet
#   CONTAINS_POD_TEMPLATE— Deployment/StatefulSet/DaemonSet/Job → PodTemplateSpec
#   BINDS_ROLE           — RoleBinding/ClusterRoleBinding → Role/ClusterRole
#   BINDS_SERVICE_ACCOUNT— RoleBinding/ClusterRoleBinding → ServiceAccount
#   EXTENDS              — Deployment/Pod → DeploymentSpec/PodSpec
#   ROUTES_TO_SERVICE    — Ingress → Service
#   SELECTS_POD          — Service → Pod
#   USES_STORAGE_CLASS   — PVC → StorageClass
#   CLAIMS_VOLUME        — StatefulSet → PVC
#   HAS_CONTAINER        — PodSpec → Container
#   MOUNTS_VOLUME        — PodSpec → Volume
#   USES_SECRET          — PodSpec → Secret
#   USES_SERVICE_ACCOUNT — PodSpec → ServiceAccount
#   LOADS_CONFIGMAP      — Container → ConfigMap
#   ONE_OF / ANY_OF      — polymorphic type alternatives
#   CONTAINS_JOB_TEMPLATE— CronJob → JobTemplateSpec
# ---------------------------------------------------------------------------
_ALL_EDGE_TYPES = (
    "HAS_PROPERTY|SCALES_RESOURCE|CONTAINS_POD_TEMPLATE|CONTAINS_JOB_TEMPLATE"
    "|BINDS_ROLE|BINDS_SERVICE_ACCOUNT|EXTENDS|HAS_CONTAINER"
    "|CLAIMS_VOLUME|MOUNTS_VOLUME|USES_STORAGE_CLASS|LOADS_CONFIGMAP"
    "|USES_SECRET|SELECTS_POD|ROUTES_TO_SERVICE|USES_SERVICE_ACCOUNT"
    "|ONE_OF|ANY_OF"
)

# ---------------------------------------------------------------------------
# Path edges — untuk reasoning path (Explainable AI) + metrik RetQ/path_coverage.
# Mengembalikan pasangan parent->child yang sebenarnya di setiap hop,
# bukan root->leaf. Digunakan untuk display trace di Streamlit & evaluasi.
# Edge-set disubstitusi saat call-time (F14): default 18 edge; ablation
# 'has_property_only' → "HAS_PROPERTY" saja.
# Parameter: $root_name (str); {all_edges} + {max_depth} via .format()
# ---------------------------------------------------------------------------
PATH_EDGES_QUERY = """
MATCH p = (root:Definition {{name: $root_name}})
          -[:{all_edges}*1..{max_depth}]->(leaf:Definition)
WITH p
LIMIT 500
WITH [i IN range(0, size(nodes(p))-2) | {{
    parent:   nodes(p)[i].name,
    child:    nodes(p)[i+1].name,
    rel_type: type(relationships(p)[i]),
    depth:    i + 1
}}] AS edges
UNWIND edges AS edge
RETURN DISTINCT edge.parent   AS parent,
                edge.child    AS child,
                edge.rel_type AS rel_type,
                edge.depth    AS depth
ORDER BY edge.depth ASC, edge.parent ASC
LIMIT 50
"""

# ---------------------------------------------------------------------------
# Primary retrieval (vector fallback) — digunakan saat exact match gagal.
# Traversal memakai SEMUA 18 tipe edge (default; F14) via {all_edges} substitusi
# .format(); ablation 'has_property_only' → "HAS_PROPERTY" saja.
# Seed vektor LIMIT 1 (consumer custom_retriever ambil rows[0]); lihat F7'.
# Parameter: $embedding (list[float]); {all_edges} + {max_depth} via .format()
# ---------------------------------------------------------------------------
HYBRID_VECTOR_GRAPH_QUERY = """
CALL db.index.vector.queryNodes('definition_description_vector', 1, $embedding)
YIELD node AS root, score

OPTIONAL MATCH (root)-[r:{all_edges}*1..{max_depth}]->(child:Definition)

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
# Simple vector search with 1-hop expansion (production GraphRetriever)
# Used by: src/retrieval/graph_retriever.py, scripts/run_baseline.py
# NOTE (F1): NOT a fair eval baseline — the OPTIONAL MATCH already augments the
# pure-vector result with 1-hop graph context. The evaluation Vector baseline
# must use SIMPLE_VECTOR_QUERY (below) instead.
# ---------------------------------------------------------------------------
SIMPLE_GRAPH_EXPAND_QUERY = """
CALL db.index.vector.queryNodes('definition_description_vector', $top_k, $embedding)
YIELD node, score
OPTIONAL MATCH (node)-[r:HAS_PROPERTY|EXTENDS|CONTAINS_POD_TEMPLATE]-(related)
RETURN node.fullName, node.description, related.fullName, r, score
ORDER BY score DESC
"""

# ---------------------------------------------------------------------------
# Pure dense vector search (NO graph expansion) — fair Vector RAG baseline (F1).
# Returns only the top-k nodes by cosine similarity; the consumer's
# `related.fullName` lookup resolves to None (no expansion), so the same
# row-parsing code path works unchanged.
# Used by: scripts/evaluate.py (mode="vector")
# Parameter: $embedding (list[float]), $top_k (int)
# ---------------------------------------------------------------------------
SIMPLE_VECTOR_QUERY = """
CALL db.index.vector.queryNodes('definition_description_vector', $top_k, $embedding)
YIELD node, score
RETURN node.fullName, node.description, score
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
