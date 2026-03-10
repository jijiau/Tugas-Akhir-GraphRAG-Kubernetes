"""
Swagger Graph Builder with Semantic Stopping Logic
===================================================
Implements 4-Pass Architecture for safe, cycle-free graph construction.

SCOPE:
    ✅ INGEST: definitions (K8s resource schemas for YAML)
    ❌ SKIP: paths (HTTP API specs - handled by kubectl)

Edge Ontology (7 Categories):
    1. Structural: HAS_PROPERTY, EXTENDS, ONE_OF, ANY_OF
    2. Workload: CONTAINS_POD_TEMPLATE, CONTAINS_JOB_TEMPLATE, HAS_CONTAINER
    3. Storage: CLAIMS_VOLUME, MOUNTS_VOLUME, USES_STORAGE_CLASS
    4. Configuration: LOADS_CONFIGMAP, USES_SECRET
    5. Networking: SELECTS_POD, ROUTES_TRAFFIC_TO
    6. RBAC: BINDS_ROLE, BINDS_SERVICE_ACCOUNT, USES_SERVICE_ACCOUNT
    7. Autoscaling: SCALES_RESOURCE
"""

import json
import os
from typing import Dict, Any
from src.graph.neo4j_client import Neo4jClient
from datetime import datetime
from src.utils.text_utils import safe_truncate_description

PRIMITIVE_TYPES = {"string", "integer", "number", "boolean", "array", "object"}
IGNORE_LIST = {
    "io.k8s.apimachinery.pkg.apis.meta.v1.ManagedFieldsEntry",
    "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusDetails",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Time",
    "io.k8s.apimachinery.pkg.apis.meta.v1.MicroTime",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Duration",
    "io.k8s.apimachinery.pkg.apis.meta.v1.RawExtension",
}

class SwaggerGraphBuilder:
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.db = Neo4jClient()
        self.definitions: Dict[str, Any] = {}

    def load_swagger(self):
        print(f"📂 Loading Swagger file: {self.swagger_path}")
        with open(self.swagger_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.definitions = data.get('definitions', {})
        print(f"   ✓ Loaded {len(self.definitions)} resource definitions")

    def ingest(self):
        self.load_swagger()
        print()
        print(f"📊 Starting Ingestion: {len(self.definitions)} definitions")
        print()
        print("⚠️  Cleaning existing graph data...")
        self.db.execute_query("MATCH (n) DETACH DELETE n")
        print("   ✓ Database cleared")
        print()
        print("--> Pass 1: Creating Resource Definition Nodes...")
        self._pass_1_create_nodes()
        print()
        print("--> Pass 2: Resolving Schema Relationships...")
        self._pass_2_create_structural_edges()
        print()
        print("--> Pass 2.5: Resolving Inheritance & Union Types...")
        self._pass_2b_create_inheritance_edges()
        print()
        print("--> Pass 3: Extracting YAML Configuration Patterns...")
        self._pass_3_build_semantic_edges()
        print()
        print("✅ Ingestion Complete!")

    def _pass_1_create_nodes(self):
        """PASS 1: Create nodes with BULLETPROOF GVK extraction."""
        created_count = 0
        skipped_count = 0
        
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                skipped_count += 1
                continue

            # 1. Basic naming
            short_name = full_name.split(".")[-1]

            # 2. GVK extraction - ULTRA SIMPLE (NO type() calls!)
            gvk_list = schema.get("x-kubernetes-group-version-kind", [])
            is_root = False
            kind = short_name  # Default

            if gvk_list and isinstance(gvk_list, list) and len(gvk_list) > 0:
                first_gvk = gvk_list[0]
                if isinstance(first_gvk, dict):
                    kind_value = first_gvk.get('kind')
                    if kind_value and isinstance(kind_value, str):
                        kind = kind_value  # ← DIRECT ASSIGNMENT, NO type()!
                        is_root = True
                    else:
                        kind = short_name
                        is_root = True
                else:
                    kind = short_name
                    is_root = True
            else:
                kind = "SubResource"
                is_root = False

            # Debug: print first 10 root resources
            if is_root and created_count < 10:
                print(f"      [DEBUG] {short_name:30} kind='{kind}'")

            # 3. Description
            original_desc = schema.get('description', 'No description provided.')
            desc = safe_truncate_description(original_desc, hard_limit=4000)
            original_length = len(original_desc)
            was_truncated = len(desc) < original_length

            # 4. Create node
            self.db.execute_query("""
                MERGE (d:Definition {id: $full_name})
                SET d.name = $short_name,
                    d.fullName = $full_name,
                    d.kind = $kind,
                    d.is_root = $is_root,
                    d.description = $desc,
                    d.description_length = $original_length,
                    d.was_truncated = $was_truncated,
                    d.source = 'k8s_swagger_v1'
            """, {
                "full_name": full_name,
                "short_name": short_name,
                "kind": kind,
                "is_root": is_root,
                "desc": desc,
                "original_length": original_length,
                "was_truncated": was_truncated
            })
            
            created_count += 1
            if created_count % 500 == 0:
                print(f"      Processed {created_count} definitions...")

        # Add K8sResource label
        self.db.execute_query("MATCH (d:Definition {is_root: true}) SET d:K8sResource")
        print(f"   ✓ Created {created_count} nodes (skipped {skipped_count} ignored)")

    def _pass_2_create_structural_edges(self):
        """PASS 2: Create HAS_PROPERTY edges."""
        edge_count = 0
        primitive_count = 0
        
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue
            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])
            primitive_props = {}

            for field_name, field_schema in properties.items():
                field_type = field_schema.get('type')
                ref = field_schema.get('$ref')
                is_array = False

                if field_type == 'array' and 'items' in field_schema:
                    items = field_schema['items']
                    if isinstance(items, dict):
                        if '$ref' in items:
                            ref = items['$ref']
                            is_array = True
                        elif items.get('type') in PRIMITIVE_TYPES:
                            primitive_props[field_name] = f"array_of_{items.get('type')}"
                            primitive_count += 1
                            continue

                if field_type == 'object' and 'additionalProperties' in field_schema:
                    add_props = field_schema['additionalProperties']
                    if isinstance(add_props, dict) and '$ref' in add_props:
                        ref = add_props['$ref']

                if field_type in PRIMITIVE_TYPES and not ref:
                    primitive_props[field_name] = field_type
                    primitive_count += 1
                elif ref:
                    target_name = ref.split("/")[-1]
                    if target_name not in IGNORE_LIST:
                        is_required = field_name in required_fields
                        self.db.execute_query("""
                            MATCH (source:Definition {id: $source_id})
                            MATCH (target:Definition {id: $target_id})
                            MERGE (source)-[r:HAS_PROPERTY {name: $field_name}]->(target)
                            SET r.is_array = $is_array, r.is_required = $is_required
                        """, {
                            "source_id": full_name, "target_id": target_name,
                            "field_name": field_name, "is_array": is_array,
                            "is_required": is_required
                        })
                        edge_count += 1

            if primitive_props:
                self.db.execute_query("MATCH (d:Definition {id: $full_name}) SET d += $primitive_props",
                    {"full_name": full_name, "primitive_props": primitive_props})

        print(f"   ✓ Created {edge_count} structural edges")
        print(f"   ✓ Stored {primitive_count} primitive properties")

    def _pass_2b_create_inheritance_edges(self):
        """PASS 2.5: Create inheritance edges."""
        inheritance_count = 0
        union_count = 0
        
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue
            for gvk_key, edge_type in [('allOf', 'EXTENDS'), ('oneOf', 'ONE_OF'), ('anyOf', 'ANY_OF')]:
                items = schema.get(gvk_key, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and '$ref' in item:
                            target = item['$ref'].split('/')[-1]
                            if target not in IGNORE_LIST:
                                self.db.execute_query(f"""
                                    MATCH (a:Definition {{id: $a}})
                                    MATCH (b:Definition {{id: $b}})
                                    MERGE (a)-[:{edge_type}]->(b)
                                """, {"a": full_name, "b": target})
                                if edge_type == 'EXTENDS':
                                    inheritance_count += 1
                                else:
                                    union_count += 1
        
        print(f"   ✓ Created {inheritance_count} inheritance edges (EXTENDS)")
        print(f"   ✓ Created {union_count} union edges (oneOf/anyOf)")

    def _pass_3_build_semantic_edges(self):
        """PASS 3: Create semantic edges."""
        rules = [
            ("Deployment → PodTemplate", "Deployment", "spec", "template", "CONTAINS_POD_TEMPLATE"),
            ("ReplicaSet → PodTemplate", "ReplicaSet", "spec", "template", "CONTAINS_POD_TEMPLATE"),
            ("CronJob → JobTemplate", "CronJob", "spec", "jobTemplate", "CONTAINS_JOB_TEMPLATE"),
            ("PodSpec → Container", None, "io.k8s.api.core.v1.PodSpec", "containers", "HAS_CONTAINER"),
            ("StatefulSet → PVC", "StatefulSet", "spec", "volumeClaimTemplates", "CLAIMS_VOLUME"),
            ("PodSpec → Volume", None, "io.k8s.api.core.v1.PodSpec", "volumes", "MOUNTS_VOLUME"),
            ("PVC → StorageClass", "PersistentVolumeClaim", "spec", "storageClassName", "USES_STORAGE_CLASS"),
            ("Container → ConfigMap", None, "io.k8s.api.core.v1.Container", "envFrom", "LOADS_CONFIGMAP"),
            ("PodSpec → Secret", None, "io.k8s.api.core.v1.PodSpec", "imagePullSecrets", "USES_SECRET"),
            ("Service → Pod", "Service", "spec", "selector", "SELECTS_POD"),
            ("Ingress → Service", "Ingress", "spec", "rules", "ROUTES_TRAFFIC_TO"),
            ("RoleBinding → Role", "RoleBinding", None, "roleRef", "BINDS_ROLE"),
            ("PodSpec → ServiceAccount", None, "io.k8s.api.core.v1.PodSpec", "serviceAccountName", "USES_SERVICE_ACCOUNT"),
            ("HPA → Scale", "HorizontalPodAutoscaler", "spec", "scaleTargetRef", "SCALES_RESOURCE"),
        ]
        
        executed = 0
        for name, kind_filter, id_filter, field_name, edge_type in rules:
            try:
                if kind_filter:
                    query = f"""
                        MATCH (a:Definition {{kind: $kind}})-[:HAS_PROPERTY {{name: $f1}}]->(b)
                        MATCH (b)-[:HAS_PROPERTY {{name: $f2}}]->(c)
                        MERGE (a)-[:{edge_type}]->(c)
                    """
                    self.db.execute_query(query, {"kind": kind_filter, "f1": field_name if edge_type not in ['BINDS_ROLE'] else 'spec', "f2": "template" if edge_type == 'CONTAINS_POD_TEMPLATE' else field_name})
                elif id_filter:
                    query = f"""
                        MATCH (a:Definition {{id: $id}})-[:HAS_PROPERTY {{name: $f}}]->(c)
                        MERGE (a)-[:{edge_type}]->(c)
                    """
                    self.db.execute_query(query, {"id": id_filter, "f": field_name})
                else:
                    query = f"""
                        MATCH (a:Definition {{kind: $kind}})-[:HAS_PROPERTY {{name: $f1}}]->(b)
                        MATCH (b)-[:HAS_PROPERTY {{name: $f2}}]->(c)
                        MERGE (a)-[:{edge_type}]->(c)
                    """
                    self.db.execute_query(query, {"kind": kind_filter or "HorizontalPodAutoscaler", "f1": "spec", "f2": field_name})
                executed += 1
                print(f"      ✓ {name}")
            except Exception as e:
                print(f"      ⚠ {name} - {str(e)[:80]}")
        
        print(f"\n   ✓ Executed: {executed} rules")