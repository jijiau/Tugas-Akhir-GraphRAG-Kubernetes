// Hybrid vector + graph search — fallback saat exact match gagal.
// Root ditemukan via Native Vector Index (cosine similarity), lalu
// diperluas dengan traversal multi-hop yang sama seperti pencarian
// exact match.
// Parameter: $embedding (list[float])
CALL db.index.vector.queryNodes('definition_description_vector', 1, $embedding)
YIELD node AS root, score

OPTIONAL MATCH (root)-[r:HAS_PROPERTY|SCALES_RESOURCE|CONTAINS_POD_TEMPLATE|CONTAINS_JOB_TEMPLATE
                       |BINDS_ROLE|BINDS_SERVICE_ACCOUNT|EXTENDS|HAS_CONTAINER
                       |CLAIMS_VOLUME|MOUNTS_VOLUME|USES_STORAGE_CLASS|LOADS_CONFIGMAP
                       |USES_SECRET|SELECTS_POD|ROUTES_TO_SERVICE|USES_SERVICE_ACCOUNT
                       |ONE_OF|ANY_OF*1..3]->(child:Definition)

WITH root, score, r, child

WITH root, score,
     CASE
         WHEN child IS NOT NULL AND r IS NOT NULL THEN {
             path_depth:        size(r),
             relation_type:     type(last(r)),
             yaml_field:        last(r).name,
             is_array:          coalesce(last(r).is_array, false),
             child_resource:    child.name,
             child_description: substring(child.description, 0, 150)
         }
         ELSE null
     END AS dep

RETURN root.name        AS RootResource,
       root.kind        AS RootKind,
       root.description AS RootDescription,
       score            AS VectorSimilarityScore,
       collect(dep)     AS SchemaDependencies
