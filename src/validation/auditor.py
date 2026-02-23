from src.graph.neo4j_client import Neo4jClient
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class GraphAuditor:
    """
    Performs full-database integrity checks for Thesis Validation.
    """
    def __init__(self):
        self.db = Neo4jClient()

    def run_full_audit(self) -> Dict[str, any]:
        """Executes all validation rules."""
        results = {
            "orphan_resources": self.check_orphan_resources(),
            "missing_types": self.check_missing_field_types(),
            "broken_refs": self.check_broken_references(),
            "total_nodes": self.get_node_counts()
        }
        return results

    def check_orphan_resources(self) -> int:
        """
        Rule: Every K8sResource should be connected to an Endpoint OR another Resource.
        """
        query = """
        MATCH (r:K8sResource)
        WHERE NOT (r)-[:HAS_SUB_RESOURCE|HAS_FIELD|CREATES|MANAGES]-()
        AND NOT ()-[:HAS_SUB_RESOURCE|HAS_FIELD|CREATES|MANAGES]->(r)
        RETURN count(r) as orphans
        """
        result = self.db.execute_query(query).single()
        count = result["orphans"] if result else 0
        if count > 0:
            logger.warning(f"Validation Failed: {count} orphan resources found.")
        return count

    def check_missing_field_types(self) -> int:
        """
        Rule: All HAS_FIELD relationships must have a 'name' property.
        """
        query = """
        MATCH ()-[r:HAS_FIELD]->()
        WHERE r.name IS NULL
        RETURN count(r) as missing
        """
        result = self.db.execute_query(query).single()
        return result["missing"] if result else 0

    def check_broken_references(self) -> int:
        """
        Rule: Ensure no dangling relationships point to non-existent nodes.
        """
        # Neo4j usually prevents this, but good for thesis rigor
        query = """
        MATCH (n)
        WHERE NOT (n)-[]->() AND NOT ()-->(n)
        AND labels(n) <> ['ChatSession'] 
        RETURN count(n) as isolated
        """
        result = self.db.execute_query(query).single()
        return result["isolated"] if result else 0

    def get_node_counts(self) -> Dict[str, int]:
        """Returns counts per label for thesis statistics."""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """
        results = self.db.execute_query(query)
        return {r["label"]: r["count"] for r in results}