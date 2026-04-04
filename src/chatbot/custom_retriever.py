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
        logger.info(f"Searching graph for intent: {search_query}")

        try:
            # 1. Generate vector embedding dari search query
            embedding = self.vector_mgr.generate_embedding(search_query)

            # 2. Fixed Cypher Query — pisahkan OPTIONAL MATCH dari agregasi
            #    Root cause error sebelumnya: variabel `child` dan `r` tidak
            #    tersedia di scope WITH karena variable-length path pattern.
            #    Fix: pakai dua WITH clause terpisah untuk resolve scope.
            cypher = """
            CALL db.index.vector.queryNodes('definition_description_vector', 1, $embedding)
            YIELD node AS root, score

            OPTIONAL MATCH (root)-[r:HAS_PROPERTY*1..2]->(child:Definition)

            WITH root, score, r, child

            WITH root, score,
                 CASE
                     WHEN child IS NOT NULL AND r IS NOT NULL THEN {
                         path_depth: size(r),
                         relation_type: type(last(r)),
                         yaml_field: last(r).name,
                         is_array: coalesce(last(r).is_array, false),
                         child_resource: child.name,
                         child_description: substring(child.description, 0, 150)
                     }
                     ELSE null
                 END AS dep

            RETURN root.name        AS RootResource,
                   root.kind        AS RootKind,
                   root.description AS RootDescription,
                   score            AS VectorSimilarityScore,
                   collect(dep)     AS SchemaDependencies
            """

            results = self.db.execute_query(cypher, {"embedding": embedding})

            if not results:
                return "Tidak ada skema Kubernetes yang relevan di dalam Knowledge Graph."

            # 3. Konversi record Neo4j ke Python dict lalu JSON
            record_dict = dict(results[0])

            # Filter null dari SchemaDependencies (collect(null) kadang masih lolos)
            if "SchemaDependencies" in record_dict and record_dict["SchemaDependencies"]:
                record_dict["SchemaDependencies"] = [
                    d for d in record_dict["SchemaDependencies"] if d is not None
                ]

            formatted_context = json.dumps(record_dict, indent=2, ensure_ascii=False)
            return formatted_context

        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            return f"Error retrieving context from Neo4j: {str(e)}"