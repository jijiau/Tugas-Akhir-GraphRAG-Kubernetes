# src/chatbot/custom_retriever.py
import json
import logging
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_index import VectorIndexManager

logger = logging.getLogger(__name__)

class StatefulK8sRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    def retrieve_context(self, intent_data: dict) -> str:
        primary = intent_data.get("primary_resource", "")
        related = intent_data.get("related_concepts", [])
        
        search_query = f"{primary} {' '.join(related)} Kubernetes"
        logger.info(f"🔍 Searching graph for intent: {search_query}")
        
        try:
            # 1. Konversi text intent menjadi Vector Embedding
            embedding = self.vector_mgr.generate_embedding(search_query)
            
            # 2. Hybrid Cypher Query
            cypher = """
            CALL db.index.vector.queryNodes('definition_description_vector', 1, $embedding)
            YIELD node AS root, score
            
            OPTIONAL MATCH path = (root)-[r:HAS_PROPERTY*1..2]->(child:Definition)
            
            // Evaluasi dan siapkan data dependensi (jika null, jadikan null secara eksplisit)
            WITH root, score,
                 CASE WHEN child IS NOT NULL THEN {
                     path_depth: size(r),
                     relation_type: type(r[-1]),
                     yaml_field: r[-1].name,
                     is_array: coalesce(r[-1].is_array, false),
                     child_resource: child.name,
                     child_description: substring(child.description, 0, 150)
                 } ELSE null END AS dep
                 
            // Lakukan agregasi. collect(null) akan otomatis mengembalikan array kosong []
            RETURN root.name AS RootResource,
                   root.kind AS RootKind,
                   root.description AS RootDescription,
                   score AS VectorSimilarityScore,
                   collect(dep) AS SchemaDependencies
            """
            
            results = self.db.execute_query(cypher, {"embedding": embedding})
            
            if not results:
                return "Tidak ada skema Kubernetes yang relevan di dalam Knowledge Graph."
            
            # 3. Konversi Record Neo4j menjadi standard Python Dictionary sebelum di-dump ke JSON
            record_dict = dict(results[0])
            formatted_context = json.dumps(record_dict, indent=2)
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            return f"Error retrieving context from Neo4j: {str(e)}"