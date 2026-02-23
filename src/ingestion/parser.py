import json
from typing import Set, Dict, Any, List
from src.graph.neo4j_client import Neo4jClient

# --- Semantic Stopping & Filtering Configuration ---
PRIMITIVE_TYPES = {"string", "integer", "number", "boolean"}
IGNORE_LIST = {
    "io.k8s.apimachinery.pkg.apis.meta.v1.ManagedFieldsEntry",
    "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta",  # Noisy metadata
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusDetails",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Time"         # Extremely repetitive
}

class SwaggerGraphBuilder:
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.db = Neo4jClient()
        self.definitions: Dict[str, Any] = {}
        self.paths: Dict[str, Any] = {}

    def load_swagger(self):
        """Loads the 5MB JSON file into memory."""
        print("Loading Swagger file...")
        with open(self.swagger_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.definitions = data.get('definitions', {})
            self.paths = data.get('paths', {})

    def ingest(self):
        """
        Main entry point using the 3-Pass Architecture to prevent cycle errors 
        and ensure complete graph integrity.
        """
        self.load_swagger()
        print(f"Starting Ingestion: {len(self.definitions)} definitions.")

        # Wipe existing DB for clean ingestion (Optional but recommended for testing)
        self.db.execute_query("MATCH (n) DETACH DELETE n")

        print("--> Pass 1: Creating Root Nodes & Definitions...")
        self._pass_1_create_nodes()

        print("--> Pass 2: Resolving Structural Relationships ($ref)...")
        self._pass_2_create_structural_edges()

        print("--> Pass 3: Extracting Semantic Operational Logic...")
        self._pass_3_build_semantic_edges()

        print("Ingestion Complete! The Kubernetes Graph is ready.")

    def _pass_1_create_nodes(self):
        """
        PASS 1: Iterate all definitions and create standalone nodes.
        Extracts GVK to identify Root Resources and simplifies names for the LLM.
        """
        for full_name, schema in self.definitions.items():
            if full_name in IGNORE_LIST:
                continue

            # 1. Penyederhanaan Nama Node (Ide dari kamu)
            # Memotong string dari titik terakhir (e.g., io.k8s...Pod -> Pod)
            short_name = full_name.split(".")[-1]

            # 2. Deteksi Root Object (GVK)
            # Mengecek apakah objek ini punya GVK (artinya bisa di-deploy mandiri)
            gvk_list = schema.get("x-kubernetes-group-version-kind", [])
            is_root = len(gvk_list) > 0
            
            # Jika dia punya GVK, ambil 'kind' resminya. 
            # Jika tidak, tandai sebagai 'SubResource'
            kind = gvk_list[0].get("kind", short_name) if is_root else "SubResource"

            # 3. Ambil Deskripsi (potong 500 karakter agar database tidak berat)
            desc = schema.get('description', 'No description provided.')[:500]

            # 4. Cypher Query: Buat Node
            # PERHATIKAN: ID unik pakai full_name, tapi kita simpan name, kind, dan is_root!
            self.db.execute_query("""
                MERGE (d:Definition {id: $full_name})
                SET d.name = $short_name,
                    d.fullName = $full_name,
                    d.kind = $kind,
                    d.is_root = $is_root,
                    d.description = $desc,
                    d.source = 'k8s_swagger_v1'
            """, {
                "full_name": full_name,
                "short_name": short_name,
                "kind": kind,
                "is_root": is_root,
                "desc": desc
            })

    def _pass_2_create_structural_edges(self):
        """
        PASS 2: Read properties of each definition and map connections.
        Applies Primitive Truncation safely using Cypher dict injection.
        """
        for name, schema in self.definitions.items():
            if name in IGNORE_LIST:
                continue

            properties = schema.get('properties', {})
            primitive_props = {}

            for field_name, field_schema in properties.items():
                field_type = field_schema.get('type')
                ref = field_schema.get('$ref')

                # Handle Arrays of Refs
                if field_type == 'array' and '$ref' in field_schema.get('items', {}):
                    ref = field_schema['items']['$ref']

                # 1. Semantic Stop: Primitive Truncation
                if field_type in PRIMITIVE_TYPES:
                    primitive_props[field_name] = field_type
                
                # 2. Structural Edge ($ref to another Definition)
                elif ref:
                    target_name = ref.split("/")[-1]
                    if target_name not in IGNORE_LIST:
                        self.db.execute_query("""
                            MATCH (source:Definition {name: $source_name})
                            MATCH (target:Definition {name: $target_name})
                            MERGE (source)-[:HAS_PROPERTY {name: $field_name}]->(target)
                        """, {
                            "source_name": name,
                            "target_name": target_name,
                            "field_name": field_name
                        })

            # Update all primitive properties safely in one batch
            if primitive_props:
                self.db.execute_query("""
                    MATCH (d:Definition {name: $name})
                    SET d += $primitive_props
                """, {
                    "name": name,
                    "primitive_props": primitive_props
                })

    def _pass_3_build_semantic_edges(self):
        """
        PASS 3: The Semantic Rule Engine.
        Infers operational logic (Stateful, RBAC, Scaling) without explicit $refs.
        """
        semantic_rules = [
            # Workload -> Pod Rule
            """
            MATCH (w:Definition)-[:HAS_PROPERTY {name: 'template'}]->(t:Definition)-[:HAS_PROPERTY {name: 'spec'}]->(p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})
            MERGE (w)-[:MANAGES_POD]->(p)
            """,
            # StatefulSet -> PVC Rule (Crucial for the Stateful validation)
            """
            MATCH (s:Definition {kind: 'StatefulSet'})-[:HAS_PROPERTY {name: 'volumeClaimTemplates'}]->(pvc:Definition)
            MERGE (s)-[:CLAIMS_VOLUME]->(pvc)
            """,
            # Storage -> Volume
            """
            MATCH (p:Definition {name: 'io.k8s.api.core.v1.PodSpec'})-[:HAS_PROPERTY {name: 'volumes'}]->(v:Definition)
            MERGE (p)-[:MOUNTS_VOLUME]->(v)
            """
        ]

        for query in semantic_rules:
            self.db.execute_query(query)