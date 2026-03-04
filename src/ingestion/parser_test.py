"""
Swagger Graph Builder for Kubernetes YAML Configuration Generation
===================================================================
Implements 3-Pass Architecture (+ 2.5) for safe, cycle-free graph construction.

SCOPE:
    ✅ Ingest: definitions (K8s resource schemas for YAML)
    ❌ Skip: paths (HTTP API specs - handled by kubectl)

Key Features:
    - Smart Truncation (preserves WARNING/DEPRECATED info)
    - Primitive Truncation (stores primitives as properties, not nodes)
    - GVK Detection (identifies root K8s resources)
    - Edge Metadata (is_array, is_map, is_required for YAML validation)
    - Inheritance Tracking (allOf/oneOf/anyOf)
    - YAML-Focused Semantic Rules (16 patterns for IaC generation)
"""

import json
import os
from typing import Set, Dict, Any, List
from datetime import datetime
from src.graph.neo4j_client import Neo4jClient

# ============================================
# CONSTANTS
# ============================================
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


# ============================================
# HELPER FUNCTIONS
# ============================================
def smart_truncate_description(desc: str, original_length: int = None, max_length: int = 2000) -> str:
    """
    Intelligently truncate description while preserving critical information.
    
    Priority Order:
    1. Keep WARNING, DEPRECATED, SECURITY notices (even if at end)
    2. Truncate at sentence boundary (not mid-sentence)
    3. Preserve first 2000 chars as baseline
    
    Args:
        desc: Original description text
        original_length: Length of original description (for ellipsis check)
        max_length: Maximum characters to keep (default: 2000)
    
    Returns:
        Truncated description with critical info preserved
    """
    if not desc:
        return 'No description provided.'
    
    # Store original length if not provided
    if original_length is None:
        original_length = len(desc)
    
    # If already within limit, return as-is
    if len(desc) <= max_length:
        return desc
    
    # === Priority 1: Find Critical Keywords ===
    critical_keywords = [
        "WARNING", "DEPRECATED", "NOTE", "IMPORTANT", 
        "SECURITY", "CAUTION", "OBSOLETE", "REMOVED"
    ]
    
    # Check if critical info exists AFTER truncation point
    for keyword in critical_keywords:
        pos = desc.find(keyword, max_length - 500)  # Search near the end
        if pos != -1 and pos > max_length - 500:
            # Found critical info, extend to include it
            extended_max = min(pos + 300, len(desc))
            desc = desc[:extended_max]
            break
    
    # === Priority 2: Truncate at Sentence Boundary ===
    if len(desc) > max_length:
        truncated = desc[:max_length]
        # Find last sentence-ending punctuation
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        # Use whichever is closer to the end (but not too far back)
        boundary = max(last_period, last_newline)
        if boundary > max_length - 200:  # Within last 200 chars
            desc = truncated[:boundary + 1]
        else:
            desc = truncated
    
    # === Priority 3: Add Ellipsis if Truncated ===
    if len(desc) < original_length:
        desc = desc.rstrip() + "..."
    
    return desc


# ============================================
# MAIN CLASS
# ============================================
class SwaggerGraphBuilder:
    """
    Builds a Neo4j Knowledge Graph from Kubernetes Swagger/OpenAPI spec.
    
    Architecture:
        Pass 1: Create all Definition nodes (with smart truncation)
        Pass 2: Create HAS_PROPERTY edges based on $ref (with metadata)
        Pass 2.5: Create inheritance edges (allOf/oneOf/anyOf)
        Pass 3: Create semantic edges (YAML configuration patterns)
    
    SCOPE: YAML Configuration Generation (Infrastructure as Code)
    """
    
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.db = Neo4jClient()
        self.definitions: Dict[str, Any] = {}
        self.paths: Dict[str, Any] = {}
        self.visited_refs: Set[str] = set()

    def load_swagger(self):
        """
        Loads the 5MB JSON file into memory.
        SCOPE: Only definitions (YAML schemas), NOT paths (HTTP API).
        """
        print(f"📂 Loading Swagger file: {self.swagger_path}")
        with open(self.swagger_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ✅ ONLY definitions (K8s resource schemas)
            self.definitions = data.get('definitions', {})
            # ❌ SKIP paths (HTTP API specs - handled by kubectl)
        
        print(f"   ✓ Loaded {len(self.definitions)} resource definitions")
        print(f"   ⚠️  Skipped HTTP paths (kubectl handles API execution)")

    def ingest(self):
        """
        Main entry point using the Enhanced 3-Pass Architecture (YAML-focused).
        """
        self.load_swagger()
        print()
        print(f"📊 Starting Ingestion: {len(self.definitions)} definitions")
        print(f"🎯 Scope: Kubernetes YAML Configuration (Infrastructure as Code)")
        print()

        # Clean database
        print("⚠️  Cleaning existing graph data...")
        self.db.execute_query("MATCH (n) DETACH DELETE n")
        print("   ✓ Database cleared")
        print()

        # Pass 1: Create Nodes
        print("--> Pass 1: Creating Resource Definition Nodes...")
        self._pass_1_create_nodes()
        print()

        # Pass 2: Create Structural Edges (properties + $ref)
        print("--> Pass 2: Resolving Schema Relationships...")
        self._pass_2_create_structural_edges()
        print()

        # Pass 2.5: Create Inheritance Edges (allOf/oneOf/anyOf)
        print("--> Pass 2.5: Resolving Inheritance & Union Types...")
        self._pass_2b_create_inheritance_edges()
        print()

        # Pass 3: Create Semantic Edges (YAML-focused)
        print("--> Pass 3: Extracting YAML Configuration Patterns...")
        self._pass_3_build_semantic_edges()
        print()

        # ❌ REMOVED: Pass 4 (API Endpoints - not needed for YAML generation)

        print("✅ Ingestion Complete! The Kubernetes YAML Graph is ready.")

    def _pass_1_create_nodes(self):
        """
        PASS 1: Iterate all definitions and create standalone nodes.
        Uses Smart Truncation to preserve critical information.
        """
        created_count = 0
        skipped_count = 0
        
        for full_name, schema in self.definitions.items():
            # Semantic Stop: Skip ignored definitions
            if full_name in IGNORE_LIST:
                skipped_count += 1
                continue

            # 1. Simplify Name (e.g., io.k8s...Pod -> Pod)
            short_name = full_name.split(".")[-1]

            # 2. Detect Root Object via GVK (Group-Version-Kind)
            gvk_list = schema.get("x-kubernetes-group-version-kind", [])
            is_root = len(gvk_list) > 0
            kind = gvk_list[0].get("kind", short_name) if is_root else "SubResource"

            # 3. Smart Truncate Description
            original_desc = schema.get('description', 'No description provided.')
            original_length = len(original_desc)
            desc = smart_truncate_description(
                desc=original_desc,
                original_length=original_length,
                max_length=2000
            )
            
            # Track truncation metadata for thesis
            was_truncated = original_length > 2000

            # 4. Create Node
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
            
            # Progress indicator every 500 nodes
            if created_count % 500 == 0:
                print(f"      Processed {created_count} definitions...")

        # Add K8sResource label to root resources for faster querying
        self.db.execute_query("""
            MATCH (d:Definition {is_root: true})
            SET d:K8sResource
        """)
        
        print(f"   ✓ Created {created_count} nodes (skipped {skipped_count} ignored)")

    def _pass_2_create_structural_edges(self):
        """
        PASS 2: Read properties of each definition and map connections.
        Enhanced for YAML Generation: tracks arrays, maps, and required fields.
        """
        edge_count = 0
        primitive_count = 0
        
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue

            properties = schema.get('properties', {})
            # Track required fields for valid YAML generation
            required_fields = schema.get('required', [])
            primitive_props = {}

            for field_name, field_schema in properties.items():
                field_type = field_schema.get('type')
                ref = field_schema.get('$ref')
                is_array = False
                is_map = False
                is_required = field_name in required_fields

                # === 1. Handle Arrays of Refs ===
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

                # === 2. Handle Maps/Dictionaries (additionalProperties) ===
                if field_type == 'object' and 'additionalProperties' in field_schema:
                    add_props = field_schema['additionalProperties']
                    if isinstance(add_props, dict):
                        if '$ref' in add_props:
                            ref = add_props['$ref']
                            is_map = True
                        elif add_props.get('type') in PRIMITIVE_TYPES:
                            primitive_props[field_name] = f"map_of_{add_props.get('type')}"
                            primitive_count += 1
                            continue

                # === 3. Semantic Stop: Primitive Truncation ===
                if field_type in PRIMITIVE_TYPES and not ref:
                    primitive_props[field_name] = field_type
                    primitive_count += 1
                
                # === 4. Structural Edge: $ref to another Definition ===
                elif ref:
                    target_name = ref.split("/")[-1]
                    if target_name not in IGNORE_LIST:
                        # Track is_array, is_map, is_required on edge
                        self.db.execute_query("""
                            MATCH (source:Definition {id: $source_id})
                            MATCH (target:Definition {id: $target_id})
                            MERGE (source)-[r:HAS_PROPERTY {name: $field_name}]->(target)
                            SET r.is_array = $is_array,
                                r.is_map = $is_map,
                                r.is_required = $is_required
                        """, {
                            "source_id": full_name,
                            "target_id": target_name,
                            "field_name": field_name,
                            "is_array": is_array,
                            "is_map": is_map,
                            "is_required": is_required
                        })
                        edge_count += 1

            # Batch update primitive properties
            if primitive_props:
                self.db.execute_query("""
                    MATCH (d:Definition {id: $full_name})
                    SET d += $primitive_props
                """, {
                    "full_name": full_name,
                    "primitive_props": primitive_props
                })

        print(f"   ✓ Created {edge_count} structural edges (HAS_PROPERTY)")
        print(f"   ✓ Stored {primitive_count} primitive properties")
        print(f"   ℹ️  Edge properties: is_array, is_map, is_required")

    def _pass_2b_create_inheritance_edges(self):
        """
        PASS 2.5: Create inheritance relationships from allOf/oneOf/anyOf.
        CRITICAL for Kubernetes schema understanding (e.g., Deployment extends ObjectReference).
        """
        inheritance_count = 0
        union_count = 0
        
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue
            
            # === 1. Handle allOf (Inheritance/Composition) ===
            all_of = schema.get('allOf', [])
            for parent_ref in all_of:
                if '$ref' in parent_ref:
                    parent_name = parent_ref['$ref'].split('/')[-1]
                    if parent_name not in IGNORE_LIST:
                        self.db.execute_query("""
                            MATCH (child:Definition {id: $child_id})
                            MATCH (parent:Definition {id: $parent_id})
                            MERGE (child)-[:EXTENDS]->(parent)
                        """, {
                            "child_id": full_name,
                            "parent_id": parent_name
                        })
                        inheritance_count += 1
            
            # === 2. Handle oneOf (Union Types - Important for Volumes, etc.) ===
            one_of = schema.get('oneOf', [])
            if one_of:
                for option_ref in one_of:
                    if '$ref' in option_ref:
                        option_name = option_ref['$ref'].split('/')[-1]
                        if option_name not in IGNORE_LIST:
                            self.db.execute_query("""
                                MATCH (union:Definition {id: $union_id})
                                MATCH (option:Definition {id: $option_id})
                                MERGE (union)-[:ONE_OF]->(option)
                            """, {
                                "union_id": full_name,
                                "option_id": option_name
                            })
                            union_count += 1
            
            # === 3. Handle anyOf (Similar to oneOf but allows multiple) ===
            any_of = schema.get('anyOf', [])
            for option_ref in any_of:
                if '$ref' in option_ref:
                    option_name = option_ref['$ref'].split('/')[-1]
                    if option_name not in IGNORE_LIST:
                        self.db.execute_query("""
                            MATCH (base:Definition {id: $base_id})
                            MATCH (option:Definition {id: $option_id})
                            MERGE (base)-[:ANY_OF]->(option)
                        """, {
                            "base_id": full_name,
                            "option_id": option_name
                        })
                        union_count += 1
        
        print(f"   ✓ Created {inheritance_count} inheritance edges (EXTENDS)")
        print(f"   ✓ Created {union_count} union edges (oneOf/anyOf)")

    def _pass_3_build_semantic_edges(self):
        """
        PASS 3: YAML Configuration Pattern Engine.
        Focus: Relationships needed for generating valid Kubernetes YAML manifests.
        
        Removed: API operations, runtime behavior, garbage collection (kubectl handles these)
        Kept: YAML structure, required fields, spec hierarchy, configuration references
        """
        semantic_rules = [
            # ==================== WORKLOAD HIERARCHY (YAML Structure) ====================
            ("Deployment → PodTemplate", """
                MATCH (d:Definition {kind: 'Deployment'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'template'}]->(t:Definition)
                MERGE (d)-[:CONTAINS_POD_TEMPLATE]->(t)
            """),
            ("ReplicaSet → PodTemplate", """
                MATCH (rs:Definition {kind: 'ReplicaSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'template'}]->(t:Definition)
                MERGE (rs)-[:CONTAINS_POD_TEMPLATE]->(t)
            """),
            ("DaemonSet → PodTemplate", """
                MATCH (ds:Definition {kind: 'DaemonSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'template'}]->(t:Definition)
                MERGE (ds)-[:CONTAINS_POD_TEMPLATE]->(t)
            """),
            ("Job → PodTemplate", """
                MATCH (j:Definition {kind: 'Job'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'template'}]->(t:Definition)
                MERGE (j)-[:CONTAINS_POD_TEMPLATE]->(t)
            """),
            ("CronJob → JobTemplate", """
                MATCH (cj:Definition {kind: 'CronJob'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'jobTemplate'}]->(j:Definition)
                MERGE (cj)-[:CONTAINS_JOB_TEMPLATE]->(j)
            """),

            # ==================== STATEFUL STORAGE (YAML Volume Claims) ====================
            ("StatefulSet → VolumeClaimTemplates", """
                MATCH (s:Definition {kind: 'StatefulSet'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'volumeClaimTemplates'}]->(pvc:Definition)
                MERGE (s)-[:CLAIMS_VOLUME]->(pvc)
            """),
            ("PVC → StorageClass", """
                MATCH (pvc:Definition {kind: 'PersistentVolumeClaim'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'storageClassName'}]->(sc:Definition)
                MERGE (pvc)-[:USES_STORAGE_CLASS]->(sc)
            """),
            ("PodSpec → Volumes", """
                MATCH (p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})-[:HAS_PROPERTY {name: 'volumes'}]->(v:Definition)
                MERGE (p)-[:MOUNTS_VOLUME]->(v)
            """),
            ("PodSpec → Containers", """
                MATCH (p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})-[:HAS_PROPERTY {name: 'containers'}]->(c:Definition)
                MERGE (p)-[:HAS_CONTAINER]->(c)
            """),

            # ==================== CONFIGURATION (YAML ConfigMaps & Secrets) ====================
            ("Container → ConfigMap Reference", """
                MATCH (c:Definition {name: 'io.k8s.api.core.v1.Container'})-[:HAS_PROPERTY {name: 'envFrom'}]->(e:Definition)
                MERGE (c)-[:LOADS_CONFIGMAP]->(e)
            """),
            ("PodSpec → Secret Reference", """
                MATCH (p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})-[:HAS_PROPERTY {name: 'imagePullSecrets'}]->(s:Definition)
                MERGE (p)-[:USES_SECRET]->(s)
            """),

            # ==================== NETWORKING (YAML Service & Ingress) ====================
            ("Service → Pod Selector", """
                MATCH (svc:Definition {kind: 'Service'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'selector'}]->(sel:Definition)
                MERGE (svc)-[:SELECTS_POD]->(sel)
            """),
            ("Ingress → Service Route", """
                MATCH (i:Definition {kind: 'Ingress'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'rules'}]->(r:Definition)
                MERGE (i)-[:ROUTES_TO_SERVICE]->(r)
            """),

            # ==================== RBAC (YAML Role Bindings) ====================
            ("RoleBinding → Role", """
                MATCH (rb:Definition {kind: 'RoleBinding'})-[:HAS_PROPERTY {name: 'roleRef'}]->(r:Definition)
                MERGE (rb)-[:BINDS_ROLE]->(r)
            """),
            ("RoleBinding → ServiceAccount", """
                MATCH (rb:Definition {kind: 'RoleBinding'})-[:HAS_PROPERTY {name: 'subjects'}]->(sa:Definition)
                MERGE (rb)-[:BINDS_SERVICE_ACCOUNT]->(sa)
            """),
            ("PodSpec → ServiceAccount", """
                MATCH (p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})-[:HAS_PROPERTY {name: 'serviceAccountName'}]->(sa:Definition)
                MERGE (p)-[:USES_SERVICE_ACCOUNT]->(sa)
            """),

            # ==================== AUTOSCALING (YAML HPA Config) ====================
            ("HPA → Scale Target", """
                MATCH (h:Definition {kind: 'HorizontalPodAutoscaler'})-[:HAS_PROPERTY {name: 'spec'}]->(spec:Definition)
                MATCH (spec)-[:HAS_PROPERTY {name: 'scaleTargetRef'}]->(t:Definition)
                WHERE t.kind IN ['Deployment', 'StatefulSet', 'DaemonSet', 'ReplicaSet']
                MERGE (h)-[:SCALES_RESOURCE]->(t)
            """),
        ]

        executed_count = 0
        skipped_count = 0
        skipped_rules = []
        executed_rules = []
        
        print(f"   Executing {len(semantic_rules)} YAML pattern rules...")
        
        for rule_name, query in semantic_rules:
            try:
                self.db.execute_query(query)
                executed_count += 1
                executed_rules.append(rule_name)
                print(f"      ✓ {rule_name}")
            except Exception as e:
                skipped_count += 1
                skipped_rules.append({
                    "rule": rule_name,
                    "error": str(e)[:150]
                })
                print(f"      ⚠ {rule_name} - SKIPPED: {str(e)[:100]}")

        print()
        print(f"   ✓ Executed: {executed_count} rules")
        print(f"   ⚠ Skipped: {skipped_count} rules")
        
        if skipped_rules:
            print()
            print("   📋 Skipped Rules Detail:")
            for skip in skipped_rules:
                print(f"      • {skip['rule']}")
                print(f"        Reason: {skip['error']}")
        
        # Save to single log file (overwrite every run)
        report_path = "logs/semantic_rules_execution.log"
        os.makedirs("logs", exist_ok=True)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "scope": "YAML_IaC_ONLY",
            "total_rules": len(semantic_rules),
            "executed": executed_count,
            "skipped": skipped_count,
            "executed_rules": executed_rules,
            "skipped_rules": skipped_rules,
            "removed_rules": [
                "PVC → PV (runtime binding)",
                "NetworkPolicy → Pod (advanced)",
                "Resource → Namespace (separate manifest)",
                "Parent → Child (garbage collection)",
                "Deployment → ReplicaSet (implementation detail)"
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"   💾 Execution log saved to: {report_path} (overwritten)")