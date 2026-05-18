"""
Graph Auditor for Kubernetes GraphRAG Thesis
=============================================
Performs comprehensive graph validation and generates thesis-ready statistics.
"""

from src.graph.neo4j_client import Neo4jClient
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphAuditor:
    """
    Comprehensive graph validation for thesis quality assurance.
    """
    
    def __init__(self):
        self.db = Neo4jClient()

    def run_full_audit(self) -> Dict[str, Any]:
        """Executes all validation rules and returns comprehensive report."""
        logger.info("Starting full graph audit...")
        
        results = {
            "total_nodes": self.get_node_counts(),
            "total_relationships": self.get_relationship_counts(),
            "orphan_resources": self.check_orphan_resources(),
            "missing_field_types": self.check_missing_field_types(),
            "broken_references": self.check_broken_references(),
            "semantic_relationships": self.check_semantic_relationships(),
            "workload_completeness_missing": self.check_workload_completeness(),
            "scales_coherence_violations": self.check_scales_resource_coherence(),
            "timestamp": datetime.now().isoformat(),
            "graph_health_score": self.calculate_health_score()
        }
        
        logger.info(f"Audit complete. Graph health score: {results['graph_health_score']}/100")
        return results

    def get_node_counts(self) -> Dict[str, int]:
        """Returns counts per node label."""
        query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """
        results = self.db.execute_query(query)
        # ✅ FIX: Handle list return type
        return {r["label"]: r["count"] for r in results if r and r["label"]}

    def get_relationship_counts(self) -> Dict[str, int]:
        """Returns counts per relationship type."""
        query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """
        results = self.db.execute_query(query)
        # ✅ FIX: Handle list return type
        return {r["type"]: r["count"] for r in results if r and r["type"]}

    def check_orphan_resources(self) -> int:
        """Check for K8sResource nodes without relationships."""
        query = """
            MATCH (r:K8sResource)
            WHERE NOT (r)--()
            RETURN count(r) as orphans
        """
        results = self.db.execute_query(query)
        # ✅ FIX: Handle list return type (access first element)
        return results[0]["orphans"] if results and results[0] else 0

    def check_missing_field_types(self) -> int:
        """Check HAS_PROPERTY relationships without 'name' property."""
        query = """
            MATCH ()-[r:HAS_PROPERTY]->()
            WHERE r.name IS NULL
            RETURN count(r) as missing
        """
        results = self.db.execute_query(query)
        # ✅ FIX: Handle list return type
        return results[0]["missing"] if results and results[0] else 0

    def check_broken_references(self) -> int:
        """Check for isolated nodes (no connections)."""
        query = """
            MATCH (n)
            WHERE NOT (n)--()
            AND labels(n) <> ['APIEndpoint']
            RETURN count(n) as isolated
        """
        results = self.db.execute_query(query)
        # ✅ FIX: Handle list return type
        return results[0]["isolated"] if results and results[0] else 0

    def check_semantic_relationships(self) -> Dict[str, int]:
        """Verify semantic edges were created during Pass 3."""
        semantic_rules = {
            # Workload Hierarchy
            "CONTAINS_POD_TEMPLATE": "MATCH ()-[r:CONTAINS_POD_TEMPLATE]->() RETURN count(r) as count",
            "CONTAINS_JOB_TEMPLATE": "MATCH ()-[r:CONTAINS_JOB_TEMPLATE]->() RETURN count(r) as count",
            # Stateful Storage
            "CLAIMS_VOLUME": "MATCH ()-[r:CLAIMS_VOLUME]->() RETURN count(r) as count",
            "USES_STORAGE_CLASS": "MATCH ()-[r:USES_STORAGE_CLASS]->() RETURN count(r) as count",
            "MOUNTS_VOLUME": "MATCH ()-[r:MOUNTS_VOLUME]->() RETURN count(r) as count",
            "HAS_CONTAINER": "MATCH ()-[r:HAS_CONTAINER]->() RETURN count(r) as count",
            # Configuration
            "LOADS_CONFIGMAP": "MATCH ()-[r:LOADS_CONFIGMAP]->() RETURN count(r) as count",
            "USES_SECRET": "MATCH ()-[r:USES_SECRET]->() RETURN count(r) as count",
            # Networking
            "SELECTS_POD": "MATCH ()-[r:SELECTS_POD]->() RETURN count(r) as count",
            "ROUTES_TO_SERVICE": "MATCH ()-[r:ROUTES_TO_SERVICE]->() RETURN count(r) as count",
            # RBAC
            "BINDS_ROLE": "MATCH ()-[r:BINDS_ROLE]->() RETURN count(r) as count",
            "BINDS_SERVICE_ACCOUNT": "MATCH ()-[r:BINDS_SERVICE_ACCOUNT]->() RETURN count(r) as count",
            "USES_SERVICE_ACCOUNT": "MATCH ()-[r:USES_SERVICE_ACCOUNT]->() RETURN count(r) as count",
            # Autoscaling
            "SCALES_RESOURCE": "MATCH ()-[r:SCALES_RESOURCE]->() RETURN count(r) as count",
            # Inheritance (Pass 2.5)
            "EXTENDS": "MATCH ()-[r:EXTENDS]->() RETURN count(r) as count",
            "ONE_OF": "MATCH ()-[r:ONE_OF]->() RETURN count(r) as count",
            "ANY_OF": "MATCH ()-[r:ANY_OF]->() RETURN count(r) as count",
        }
        
        results = {}
        for rel_type, query in semantic_rules.items():
            query_result = self.db.execute_query(query)
            # ✅ FIX: Handle list return type
            count = query_result[0]["count"] if query_result and query_result[0] else 0
            results[rel_type] = count
            
            if count == 0 and rel_type in ["CONTAINS_POD_TEMPLATE", "CLAIMS_VOLUME", "BINDS_ROLE"]:
                logger.warning(f"Critical semantic relationship missing: {rel_type}")
        
        return results

    def check_workload_completeness(self) -> list:
        """Verify all Workload resources have CONTAINS_POD_TEMPLATE edge."""
        query = """
            MATCH (r:Definition)
            WHERE r.kind IN ['Deployment','ReplicaSet','DaemonSet','StatefulSet','Job']
            AND NOT (r)-[:CONTAINS_POD_TEMPLATE]->()
            RETURN r.kind as kind
        """
        results = self.db.execute_query(query)
        missing = [r["kind"] for r in results if r]
        if missing:
            logger.warning(f"Workload resources missing CONTAINS_POD_TEMPLATE: {missing}")
        return missing

    def check_scales_resource_coherence(self) -> list:
        """Verify SCALES_RESOURCE only targets scalable workload resources."""
        query = """
            MATCH (h)-[:SCALES_RESOURCE]->(t)
            WHERE NOT t.kind IN ['Deployment','StatefulSet','ReplicaSet']
            RETURN t.kind as invalid_target
        """
        results = self.db.execute_query(query)
        violations = [r["invalid_target"] for r in results if r]
        if violations:
            logger.warning(f"SCALES_RESOURCE coherence violations (invalid targets): {violations}")
        return violations

    def calculate_health_score(self) -> int:
        """Calculates overall graph health score (0-100)."""
        score = 100
        
        orphans = self.check_orphan_resources()
        score -= min(orphans * 5, 30)
        
        missing_fields = self.check_missing_field_types()
        score -= min(missing_fields * 2, 20)
        
        broken = self.check_broken_references()
        score -= min(broken * 5, 30)
        
        semantic = self.check_semantic_relationships()
        missing_semantic = sum(1 for count in semantic.values() if count == 0)
        score -= min(missing_semantic * 3, 20)

        # Semantic coherence penalties (new checks)
        workload_missing = self.check_workload_completeness()
        score -= min(len(workload_missing) * 5, 20)

        coherence_violations = self.check_scales_resource_coherence()
        score -= min(len(coherence_violations) * 5, 10)

        return max(0, score)

    def get_graph_density(self) -> Dict[str, float]:
        """Calculates graph density metrics."""
        node_counts = self.get_node_counts()
        rel_counts = self.get_relationship_counts()
        
        total_nodes = sum(node_counts.values())
        total_rels = sum(rel_counts.values())
        
        edges_per_node = total_rels / total_nodes if total_nodes > 0 else 0
        
        connected_query = """
            MATCH (n)
            WHERE (n)--()
            RETURN count(n) as connected
        """
        result = self.db.execute_query(connected_query)
        connected = result[0]["connected"] if result and result[0] else 0
        connectivity = (connected / total_nodes * 100) if total_nodes > 0 else 0
        
        return {
            "edges_per_node": round(edges_per_node, 2),
            "node_connectivity_percent": round(connectivity, 2),
            "total_nodes": total_nodes,
            "total_relationships": total_rels,
        }

    def get_k8s_resource_summary(self) -> Dict[str, Any]:
        """Returns summary of Kubernetes resources."""
        query = """
            MATCH (r:K8sResource)
            WHERE r.is_root = true
            RETURN r.kind as kind, count(r) as count
            ORDER BY count DESC
        """
        results = self.db.execute_query(query)
        
        return {
            "total_root_resources": sum(r["count"] for r in results if r),
            "by_kind": {r["kind"]: r["count"] for r in results if r and r["kind"]}
        }