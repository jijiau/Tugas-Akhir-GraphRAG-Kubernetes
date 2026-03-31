"""
Hybrid Retriever: Combines Vector Search + Graph Traversal
"""
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_index import VectorIndexManager

class GraphRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
        """
        1. Finds relevant nodes via Vector Search.
        2. Expands 1-hop relationships to get context.
        3. Returns structured context for the LLM.
        """
        # 1. Get Query Embedding
        embedding = self.vector_mgr.generate_embedding(query)
        
        # 2. Vector Search + Graph Expansion Cypher
        cypher = """
        CALL db.index.vector.queryNodes('definition_description_vector', $top_k, $embedding)
        YIELD node, score
        // Expand 1 hop to get related resources (e.g., Deployment -> PodTemplate)
        OPTIONAL MATCH (node)-[r:HAS_PROPERTY|EXTENDS|CONTAINS_POD_TEMPLATE]-(related)
        RETURN node.fullName, node.description, related.fullName, r, score
        ORDER BY score DESC
        """
        
        results = self.db.execute_query(cypher, {
            "embedding": embedding, 
            "top_k": top_k
        })
        
        # 3. Format Context for LLM
        context_parts = []
        for record in results:
            node_name = record.get("node.fullName")
            desc = record.get("node.description")
            related = record.get("related.fullName")
            
            snippet = f"Resource: {node_name}\nDescription: {desc}\n"
            if related:
                snippet += f"Related To: {related}\n"
            context_parts.append(snippet)
            
        return "\n---\n".join(context_parts)