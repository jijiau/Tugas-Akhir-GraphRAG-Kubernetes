# src/graph/queries.py
# Centralized Cypher query constants — single source of truth for all graph queries.

# ---------------------------------------------------------------------------
# Exact name match — cari root node berdasarkan nama persis.
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
# Schema dependencies — membangun daftar flat dependensi untuk konteks LLM.
# Parameter: $root_name (str), max_depth via .format()
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
# Daftar semua 18 jenis edge dalam KG Kubernetes (digunakan di PATH_EDGES_QUERY).
#   HAS_PROPERTY          — referensi tipe skema (struktural, dari $ref)
#   SCALES_RESOURCE       — HPA → Deployment/StatefulSet/ReplicaSet
#   CONTAINS_POD_TEMPLATE — Deployment/StatefulSet/DaemonSet/Job → PodTemplateSpec
#   CONTAINS_JOB_TEMPLATE — CronJob → JobTemplateSpec
#   BINDS_ROLE            — RoleBinding/ClusterRoleBinding → Role/ClusterRole
#   BINDS_SERVICE_ACCOUNT — RoleBinding/ClusterRoleBinding → ServiceAccount
#   EXTENDS               — Deployment/Pod → DeploymentSpec/PodSpec (logis)
#   HAS_CONTAINER         — PodSpec → Container
#   CLAIMS_VOLUME         — StatefulSet → PVC
#   MOUNTS_VOLUME         — PodSpec → Volume
#   USES_STORAGE_CLASS    — PVC → StorageClass
#   LOADS_CONFIGMAP       — Container → ConfigMap
#   USES_SECRET           — PodSpec → Secret
#   SELECTS_POD           — Service → Pod
#   ROUTES_TO_SERVICE     — Ingress → Service
#   USES_SERVICE_ACCOUNT  — PodSpec → ServiceAccount
#   ONE_OF / ANY_OF       — polimorfisme tipe (allOf/oneOf/anyOf OpenAPI)
# ---------------------------------------------------------------------------
_ALL_EDGE_TYPES = (
    "HAS_PROPERTY|SCALES_RESOURCE|CONTAINS_POD_TEMPLATE|CONTAINS_JOB_TEMPLATE"
    "|BINDS_ROLE|BINDS_SERVICE_ACCOUNT|EXTENDS|HAS_CONTAINER"
    "|CLAIMS_VOLUME|MOUNTS_VOLUME|USES_STORAGE_CLASS|LOADS_CONFIGMAP"
    "|USES_SECRET|SELECTS_POD|ROUTES_TO_SERVICE|USES_SERVICE_ACCOUNT"
    "|ONE_OF|ANY_OF"
)

# ---------------------------------------------------------------------------
# Path edges — untuk reasoning path (explainability).
# Mengembalikan pasangan parent→child nyata di setiap hop.
# Parameter: $root_name (str), max_depth via .format()
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
""".replace("{all_edges}", _ALL_EDGE_TYPES)

# ---------------------------------------------------------------------------
# Hybrid vector + graph retrieval — digunakan saat exact match gagal.
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
# Required fields — untuk validasi YAML Layer 3 (YAMLValidator).
# ---------------------------------------------------------------------------
REQUIRED_FIELDS_QUERY = """
MATCH (d:Definition {name: $kind})-[r:HAS_PROPERTY {is_required: true}]->(p)
RETURN p.name AS field_name
"""

ALL_FIELDS_QUERY = """
MATCH (d:Definition {name: $kind})-[r:HAS_PROPERTY]->(p)
RETURN p.name AS field_name, r.is_required AS is_required
"""
