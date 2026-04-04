"""
Hybrid Retriever: Combines Vector Search + Graph Traversal (1-hop baseline)
Used by: scripts/run_baseline.py --mode vector
"""
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_index import VectorIndexManager
from src.graph.queries import SIMPLE_GRAPH_EXPAND_QUERY


class GraphRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
        """
        1. Finds relevant nodes via Vector Search.
        2. Expands 1-hop relationships to get context.
        3. Returns structured context string for the LLM.
        """
        embedding = self.vector_mgr.generate_embedding(query)

        results = self.db.execute_query(
            SIMPLE_GRAPH_EXPAND_QUERY,
            {"embedding": embedding, "top_k": top_k}
        )

        context_parts = []
        for record in results:
            node_name = record.get("node.fullName")
            desc      = record.get("node.description")
            related   = record.get("related.fullName")

            snippet = f"Resource: {node_name}\nDescription: {desc}\n"
            if related:
                snippet += f"Related To: {related}\n"
            context_parts.append(snippet)

        return "\n---\n".join(context_parts)
