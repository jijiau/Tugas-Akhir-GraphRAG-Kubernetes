// Schema dependencies (multi-hop traversal) — konteks untuk LLM.
// Dipanggil setelah root ditemukan (exact match atau vector search).
// Traversal memakai seluruh 18 tipe edge (default); ablation
// 'has_property_only' menggantinya dengan HAS_PROPERTY saja.
// Tipe edge dan kedalaman maksimum (di sini: 3) disubstitusi saat
// call-time via .format() Python karena Cypher tidak mendukung
// parameterisasi $-param untuk nama tipe relationship maupun batas
// variable-length path.
// Parameter: $root_name (str)
MATCH (root:Definition {name: $root_name})
OPTIONAL MATCH (root)-[r:HAS_PROPERTY|SCALES_RESOURCE|CONTAINS_POD_TEMPLATE|CONTAINS_JOB_TEMPLATE
                       |BINDS_ROLE|BINDS_SERVICE_ACCOUNT|EXTENDS|HAS_CONTAINER
                       |CLAIMS_VOLUME|MOUNTS_VOLUME|USES_STORAGE_CLASS|LOADS_CONFIGMAP
                       |USES_SECRET|SELECTS_POD|ROUTES_TO_SERVICE|USES_SERVICE_ACCOUNT
                       |ONE_OF|ANY_OF*1..3]->(child:Definition)

WITH root, r, child

WITH root,
     CASE
         WHEN child IS NOT NULL AND r IS NOT NULL THEN {
             path_depth:       size(r),
             relation_type:    type(last(r)),
             yaml_field:       last(r).name,
             is_array:         coalesce(last(r).is_array, false),
             child_resource:   child.name,
             child_description: substring(child.description, 0, 150)
         }
         ELSE null
     END AS dep

RETURN root.name        AS RootResource,
       root.kind        AS RootKind,
       root.description AS RootDescription,
       1.0              AS VectorSimilarityScore,
       collect(dep)     AS SchemaDependencies
