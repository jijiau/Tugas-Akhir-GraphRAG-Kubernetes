"""
Swagger Graph Builder — Pipeline Ingestion 5-Fase

Fase:
    Pass 1   — Buat node Definition (nama, kind, scope, deskripsi)
    Pass 1.5 — Generate embedding vektor 1536-dim (text-embedding-3-small)
    Pass 2   — Buat edge HAS_PROPERTY struktural (resolusi $ref)
    Pass 2.5 — Buat edge EXTENDS / ONE_OF / ANY_OF (pewarisan tipe)
    Pass 3   — Buat 18 jenis edge semantik (CONTAINS_POD_TEMPLATE, USES_SECRET, dll.)
"""

import json
from typing import Dict, Any
from src.graph.neo4j_client import Neo4jClient
from src.utils.text_utils import safe_truncate_description
from src.graph.vector_index import VectorIndexManager

PRIMITIVE_TYPES = {"string", "integer", "number", "boolean", "array", "object"}

# Tipe metadata generik yang dikecualikan karena tidak relevan untuk pembuatan YAML
IGNORE_LIST = {
    "io.k8s.apimachinery.pkg.apis.meta.v1.ManagedFieldsEntry",
    "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusDetails",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Time",
    "io.k8s.apimachinery.pkg.apis.meta.v1.MicroTime",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Duration",
    "io.k8s.apimachinery.pkg.apis.meta.v1.RawExtension",
    "io.k8s.apimachinery.pkg.apis.meta.v1.FieldsV1",
    "io.k8s.apimachinery.pkg.apis.meta.v1.OwnerReference",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Patch",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusCause",
    "io.k8s.apimachinery.pkg.version.Info",
}

CLUSTER_SCOPED_RESOURCES = {
    "Namespace", "Node", "PersistentVolume", "ClusterRole",
    "ClusterRoleBinding", "StorageClass", "CustomResourceDefinition",
    "PriorityClass", "CSIDriver", "CSINode", "VolumeAttachment",
    "RuntimeClass", "APIService", "MutatingWebhookConfiguration",
    "ValidatingWebhookConfiguration", "ValidatingAdmissionPolicy",
    "ValidatingAdmissionPolicyBinding", "CertificateSigningRequest",
    "IngressClass", "FlowSchema", "PriorityLevelConfiguration",
    "SelfSubjectAccessReview", "SubjectAccessReview", "TokenReview"
}


class SwaggerGraphBuilder:
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.db = Neo4jClient()
        self.definitions: Dict[str, Any] = {}

    def load_swagger(self):
        with open(self.swagger_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.definitions = data.get('definitions', {})

    def ingest(self):
        self.load_swagger()
        self.db.execute_query("MATCH (n) DETACH DELETE n")

        print("--> Pass 1: Creating Resource Definition Nodes...")
        self._pass_1_create_nodes()

        print("--> Pass 1.5: Generating Vector Embeddings...")
        vector_mgr = VectorIndexManager()
        vector_mgr.initialize()

        print("--> Pass 2: Resolving Schema Relationships...")
        self._pass_2_create_structural_edges()

        print("--> Pass 2.5: Resolving Inheritance & Union Types...")
        self._pass_2b_create_inheritance_edges()

        print("--> Pass 3: Extracting YAML Configuration Patterns...")
        self._pass_3_build_semantic_edges()

    def _pass_1_create_nodes(self):
        created_count = 0

        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue

            short_name = full_name.split(".")[-1]
            gvk_list = schema.get("x-kubernetes-group-version-kind", [])
            kind = short_name
            scope = "Namespaced"

            if gvk_list and isinstance(gvk_list, list) and len(gvk_list) > 0:
                first_gvk = gvk_list[0]
                if isinstance(first_gvk, dict) and isinstance(first_gvk.get('kind'), str):
                    kind = first_gvk.get('kind').strip()
                    is_root = True
                    scope = "Cluster" if kind in CLUSTER_SCOPED_RESOURCES else "Namespaced"
                else:
                    kind, is_root, scope = "SubResource", False, "N/A"
            else:
                kind, is_root, scope = "SubResource", False, "N/A"

            original_desc = schema.get('description', 'No description provided.')
            desc = safe_truncate_description(original_desc, hard_limit=4000)

            self.db.execute_query("""
                MERGE (d:Definition {id: $full_name})
                SET d.name = $short_name,
                    d.fullName = $full_name,
                    d.kind = $kind,
                    d.is_root = $is_root,
                    d.scope = $scope,
                    d.description = $desc,
                    d.description_length = $original_length,
                    d.was_truncated = $was_truncated,
                    d.source = 'k8s_swagger_v1'
            """, {
                "full_name": full_name, "short_name": short_name,
                "kind": kind, "is_root": is_root, "scope": scope,
                "desc": desc, "original_length": len(original_desc),
                "was_truncated": len(desc) < len(original_desc)
            })
            created_count += 1

        self.db.execute_query("MATCH (d:Definition {is_root: true}) SET d:K8sResource")
        print(f"   Created {created_count} nodes")

    def _pass_2_create_structural_edges(self):
        edge_count = 0

        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue

            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])
            primitive_props = {}

            for field_name, field_schema in properties.items():
                field_type = field_schema.get('type')
                ref = field_schema.get('$ref')
                is_array = is_map = False
                is_required = field_name in required_fields

                if field_type == 'array' and 'items' in field_schema:
                    items = field_schema['items']
                    if isinstance(items, dict):
                        if '$ref' in items:
                            ref, is_array = items['$ref'], True
                        else:
                            primitive_props[field_name] = f"array_of_{items.get('type', 'object')}"
                            continue

                if field_type == 'object' and 'additionalProperties' in field_schema:
                    add_props = field_schema['additionalProperties']
                    if isinstance(add_props, dict):
                        if '$ref' in add_props:
                            ref, is_map = add_props['$ref'], True
                        else:
                            primitive_props[field_name] = f"map_of_{add_props.get('type', 'object')}"
                            continue

                if field_type in PRIMITIVE_TYPES and not ref:
                    if field_name not in ["kind", "id", "name", "is_root", "description",
                                          "source", "was_truncated", "description_length", "fullName"]:
                        primitive_props[field_name] = field_type

                elif ref:
                    target_name = ref.split("/")[-1]
                    if target_name in IGNORE_LIST:
                        primitive_props[field_name] = "string" if "Time" in target_name else "object"
                    else:
                        if target_name in self.definitions:
                            self.db.execute_query("""
                                MATCH (source:Definition {id: $source_id})
                                MATCH (target:Definition {id: $target_id})
                                MERGE (source)-[r:HAS_PROPERTY {name: $field_name}]->(target)
                                SET r.is_array = $is_array,
                                    r.is_map = $is_map,
                                    r.is_required = $is_required
                            """, {
                                "source_id": full_name, "target_id": target_name,
                                "field_name": field_name, "is_array": is_array,
                                "is_map": is_map, "is_required": is_required
                            })
                        else:
                            # Cross-reference: target tidak ada di definitions tetapi
                            # valid sebagai tipe Kubernetes — buat placeholder node.
                            self.db.execute_query("""
                                MERGE (target:Definition {id: $target_id})
                                ON CREATE SET
                                    target.name = $short_name,
                                    target.fullName = $target_id,
                                    target.kind = 'SubResource',
                                    target.is_root = false,
                                    target.source = 'k8s_swagger_cross_ref',
                                    target.description = 'External cross-reference from Swagger $ref',
                                    target.is_cross_reference = true
                                WITH target
                                MATCH (source:Definition {id: $source_id})
                                MERGE (source)-[r:HAS_PROPERTY {name: $field_name}]->(target)
                                SET r.is_array = $is_array,
                                    r.is_map = $is_map,
                                    r.is_required = $is_required
                            """, {
                                "source_id": full_name, "target_id": target_name,
                                "short_name": target_name.split(".")[-1],
                                "field_name": field_name, "is_array": is_array,
                                "is_map": is_map, "is_required": is_required
                            })
                        edge_count += 1

            if primitive_props:
                self.db.execute_query(
                    "MATCH (d:Definition {id: $full_name}) SET d += $primitive_props",
                    {"full_name": full_name, "primitive_props": primitive_props}
                )

        print(f"   Created {edge_count} structural edges (HAS_PROPERTY)")

    def _pass_2b_create_inheritance_edges(self):
        inheritance_count = union_count = 0

        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue

            for item in schema.get('allOf', []):
                if isinstance(item, dict) and '$ref' in item:
                    parent_name = item['$ref'].split('/')[-1]
                    if parent_name not in IGNORE_LIST:
                        self.db.execute_query(
                            "MATCH (child:Definition {id: $child_id}), (parent:Definition {id: $parent_id}) "
                            "MERGE (child)-[:EXTENDS]->(parent)",
                            {"child_id": full_name, "parent_id": parent_name}
                        )
                        inheritance_count += 1

            for item in schema.get('oneOf', []) + schema.get('anyOf', []):
                if isinstance(item, dict) and '$ref' in item:
                    option_name = item['$ref'].split('/')[-1]
                    if option_name not in IGNORE_LIST:
                        self.db.execute_query(
                            "MATCH (union:Definition {id: $union_id}), (option:Definition {id: $option_id}) "
                            "MERGE (union)-[:ONE_OF]->(option)",
                            {"union_id": full_name, "option_id": option_name}
                        )
                        union_count += 1

        print(f"   Created {inheritance_count} inheritance and {union_count} union edges")

    def _pass_3_build_semantic_edges(self):
        semantic_rules = [
            ("Deployment → PodTemplate",
             "MATCH (d:Definition {kind: 'Deployment'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'template'}]->(t) MERGE (d)-[:CONTAINS_POD_TEMPLATE]->(t)"),
            ("ReplicaSet → PodTemplate",
             "MATCH (rs:Definition {kind: 'ReplicaSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'template'}]->(t) MERGE (rs)-[:CONTAINS_POD_TEMPLATE]->(t)"),
            ("DaemonSet → PodTemplate",
             "MATCH (ds:Definition {kind: 'DaemonSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'template'}]->(t) MERGE (ds)-[:CONTAINS_POD_TEMPLATE]->(t)"),
            ("Job → PodTemplate",
             "MATCH (j:Definition {kind: 'Job'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'template'}]->(t) MERGE (j)-[:CONTAINS_POD_TEMPLATE]->(t)"),
            ("StatefulSet → PodTemplate",
             "MATCH (s:Definition {kind: 'StatefulSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'template'}]->(t) MERGE (s)-[:CONTAINS_POD_TEMPLATE]->(t)"),
            ("CronJob → JobTemplate",
             "MATCH (cj:Definition {kind: 'CronJob'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'jobTemplate'}]->(j) MERGE (cj)-[:CONTAINS_JOB_TEMPLATE]->(j)"),
            ("PodSpec → Container",
             "MATCH (p:Definition {id: 'io.k8s.api.core.v1.PodSpec'})"
             "-[:HAS_PROPERTY {name: 'containers'}]->(c) MERGE (p)-[:HAS_CONTAINER]->(c)"),
            ("StatefulSet → VolumeClaimTemplates",
             "MATCH (s:Definition {kind: 'StatefulSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec)"
             "-[:HAS_PROPERTY {name: 'volumeClaimTemplates'}]->(pvc) MERGE (s)-[:CLAIMS_VOLUME]->(pvc)"),
            ("PodSpec → Volume",
             "MATCH (p:Definition {id: 'io.k8s.api.core.v1.PodSpec'})"
             "-[:HAS_PROPERTY {name: 'volumes'}]->(v) MERGE (p)-[:MOUNTS_VOLUME]->(v)"),
            ("PVC → StorageClass",
             "MATCH (pvc:Definition {kind: 'PersistentVolumeClaim'}), (sc:Definition {kind: 'StorageClass'})"
             " MERGE (pvc)-[:USES_STORAGE_CLASS]->(sc)"),
            ("Container → ConfigMap",
             "MATCH (c:Definition {id: 'io.k8s.api.core.v1.Container'}), (cm:Definition {kind: 'ConfigMap'})"
             " MERGE (c)-[:LOADS_CONFIGMAP]->(cm)"),
            ("PodSpec → Secret",
             "MATCH (p:Definition {id: 'io.k8s.api.core.v1.PodSpec'}), (s:Definition {kind: 'Secret'})"
             " MERGE (p)-[:USES_SECRET]->(s)"),
            ("Service → Pod Selector",
             "MATCH (svc:Definition {kind: 'Service'}), (pod:Definition {kind: 'Pod'})"
             " MERGE (svc)-[:SELECTS_POD]->(pod)"),
            ("Ingress → Service",
             "MATCH (i:Definition {kind: 'Ingress'}), (s:Definition {kind: 'Service'})"
             " MERGE (i)-[:ROUTES_TO_SERVICE]->(s)"),
            ("RoleBinding → Role",
             "MATCH (rb:Definition {kind: 'RoleBinding'}), (r:Definition {kind: 'Role'})"
             " MERGE (rb)-[:BINDS_ROLE]->(r)"),
            ("ClusterRoleBinding → ClusterRole",
             "MATCH (rb:Definition {kind: 'ClusterRoleBinding'}), (r:Definition {kind: 'ClusterRole'})"
             " MERGE (rb)-[:BINDS_ROLE]->(r)"),
            ("RoleBinding → ServiceAccount",
             "MATCH (rb:Definition {kind: 'RoleBinding'}), (sa:Definition {kind: 'ServiceAccount'})"
             " MERGE (rb)-[:BINDS_SERVICE_ACCOUNT]->(sa)"),
            ("ClusterRoleBinding → ServiceAccount",
             "MATCH (rb:Definition {kind: 'ClusterRoleBinding'}), (sa:Definition {kind: 'ServiceAccount'})"
             " MERGE (rb)-[:BINDS_SERVICE_ACCOUNT]->(sa)"),
            ("PodSpec → ServiceAccount",
             "MATCH (p:Definition {id: 'io.k8s.api.core.v1.PodSpec'}), (sa:Definition {kind: 'ServiceAccount'})"
             " MERGE (p)-[:USES_SERVICE_ACCOUNT]->(sa)"),
            ("HPA → Deployment",
             "MATCH (h:Definition {kind: 'HorizontalPodAutoscaler'}), (t:Definition {kind: 'Deployment'})"
             " MERGE (h)-[:SCALES_RESOURCE]->(t)"),
            ("HPA → StatefulSet",
             "MATCH (h:Definition {kind: 'HorizontalPodAutoscaler'}), (t:Definition {kind: 'StatefulSet'})"
             " MERGE (h)-[:SCALES_RESOURCE]->(t)"),
            ("HPA → ReplicaSet",
             "MATCH (h:Definition {kind: 'HorizontalPodAutoscaler'}), (t:Definition {kind: 'ReplicaSet'})"
             " MERGE (h)-[:SCALES_RESOURCE]->(t)"),
            ("Pod → PodSpec (Logical EXTENDS)", """
                MATCH (p:Definition {kind: 'Pod'}), (spec:Definition {id: 'io.k8s.api.core.v1.PodSpec'})
                MERGE (p)-[:EXTENDS]->(spec)
            """),
            ("Deployment → DeploymentSpec (Logical EXTENDS)", """
                MATCH (d:Definition {kind: 'Deployment'}), (spec:Definition {id: 'io.k8s.api.apps.v1.DeploymentSpec'})
                MERGE (d)-[:EXTENDS]->(spec)
            """),
            ("Volume → VolumeSources (Logical ONE_OF)", """
                MATCH (v:Definition {id: 'io.k8s.api.core.v1.Volume'})-[:HAS_PROPERTY]->(target)
                WHERE target.name IN ['ConfigMapVolumeSource', 'EmptyDirVolumeSource',
                                      'SecretVolumeSource', 'HostPathVolumeSource',
                                      'PersistentVolumeClaimVolumeSource']
                MERGE (v)-[:ONE_OF]->(target)
            """),
            ("EnvFrom → EnvSources (Logical ANY_OF)", """
                MATCH (env:Definition {id: 'io.k8s.api.core.v1.EnvFromSource'})-[:HAS_PROPERTY]->(target)
                WHERE target.name IN ['ConfigMapEnvSource', 'SecretEnvSource']
                MERGE (env)-[:ANY_OF]->(target)
            """)
        ]

        executed = 0
        for rule_name, query in semantic_rules:
            try:
                self.db.execute_query(query)
                executed += 1
            except Exception as e:
                print(f"   SKIPPED {rule_name}: {str(e)[:80]}")

        print(f"   Executed {executed} semantic rules")
