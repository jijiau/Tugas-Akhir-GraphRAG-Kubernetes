"""
Edge Distribution Analysis for Kubernetes GraphRAG Thesis
==========================================================
Analyzes edge distribution across 7 categories + Logical Inference.
Useful for Bab 4 (Hasil & Pembahasan) - Graph Statistics.

Usage:
    python scripts/analyze_edge_distribution.py
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph.neo4j_client import Neo4jClient

# Edge category mapping (sesuai dengan parser.py)
EDGE_CATEGORIES = {
    "Structural": ["HAS_PROPERTY", "EXTENDS", "ONE_OF", "ANY_OF"],
    "Workload": ["CONTAINS_POD_TEMPLATE", "CONTAINS_JOB_TEMPLATE", "HAS_CONTAINER"],
    "Storage": ["CLAIMS_VOLUME", "MOUNTS_VOLUME", "USES_STORAGE_CLASS"],
    "Configuration": ["LOADS_CONFIGMAP", "USES_SECRET"],
    "Networking": ["SELECTS_POD", "ROUTES_TO_SERVICE"],
    "RBAC": ["BINDS_ROLE", "BINDS_SERVICE_ACCOUNT", "USES_SERVICE_ACCOUNT"],
    "Autoscaling": ["SCALES_RESOURCE"],
    "Logical Inference": ["EXTENDS", "ONE_OF", "ANY_OF"],  # From Pass 3 logical rules
}

def get_edge_statistics(db):
    """Get all edge types and their counts."""
    query = """
    MATCH ()-[r]->()
    RETURN type(r) AS edge_type, count(r) AS count
    ORDER BY count DESC
    """
    return db.execute_query(query)

def get_category_distribution(db):
    """Get edge count per category."""
    category_counts = defaultdict(int)
    category_details = defaultdict(lambda: defaultdict(int))
    
    for category, edge_types in EDGE_CATEGORIES.items():
        for edge_type in edge_types:
            query = f"""
            MATCH ()-[r:{edge_type}]->()
            RETURN count(r) AS count
            """
            result = db.execute_query(query)
            count = result[0]['count'] if result else 0
            if count > 0:
                category_counts[category] += count
                category_details[category][edge_type] = count
    
    return category_counts, category_details

def get_node_statistics(db):
    """Get node statistics."""
    query = """
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS count
    ORDER BY count DESC
    """
    return db.execute_query(query)

def get_graph_density(db):
    """Calculate graph density metrics."""
    # Total nodes
    nodes_query = "MATCH (n) RETURN count(n) AS count"
    nodes_result = db.execute_query(nodes_query)
    total_nodes = nodes_result[0]['count'] if nodes_result else 0
    
    # Total edges
    edges_query = "MATCH ()-[r]->() RETURN count(r) AS count"
    edges_result = db.execute_query(edges_query)
    total_edges = edges_result[0]['count'] if edges_result else 0
    
    # Edges per node
    edges_per_node = round(total_edges / total_nodes, 2) if total_nodes > 0 else 0
    
    # Root resources count
    root_query = "MATCH (n:K8sResource) RETURN count(n) AS count"
    root_result = db.execute_query(root_query)
    root_resources = root_result[0]['count'] if root_result else 0
    
    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "edges_per_node": edges_per_node,
        "root_resources": root_resources,
    }

def print_report(edge_stats, category_counts, category_details, node_stats, density):
    """Print formatted analysis report."""
    print("="*80)
    print("📊 KUBERNETES GRAPH EDGE DISTRIBUTION ANALYSIS")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Graph Overview
    print("🔷 GRAPH OVERVIEW")
    print("-"*80)
    print(f"   Total Nodes:        {density['total_nodes']:,}")
    print(f"   Total Edges:        {density['total_edges']:,}")
    print(f"   Edges per Node:     {density['edges_per_node']}")
    print(f"   Root Resources:     {density['root_resources']:,} (K8sResource label)")
    print()
    
    # Node Distribution
    print("🔷 NODE DISTRIBUTION")
    print("-"*80)
    print(f"   {'Label':<40} {'Count':>15}")
    print("-"*80)
    for stat in node_stats:
        label = stat['label'] if stat['label'] else 'N/A'
        count = stat['count']
        print(f"   {label:<40} {count:>15,}")
    print()
    
    # Edge Distribution by Type
    print("🔷 EDGE DISTRIBUTION (All Types)")
    print("-"*80)
    print(f"   {'Edge Type':<40} {'Count':>15} {'Category':<20}")
    print("-"*80)
    
    # Map edge types to categories
    edge_to_category = {}
    for category, edge_types in EDGE_CATEGORIES.items():
        for edge_type in edge_types:
            if edge_type not in edge_to_category:
                edge_to_category[edge_type] = category
    
    for stat in edge_stats:
        edge_type = stat['edge_type']
        count = stat['count']
        category = edge_to_category.get(edge_type, "Other")
        print(f"   {edge_type:<40} {count:>15,} {category:<20}")
    print()
    
    # Edge Distribution by Category
    print("🔷 EDGE DISTRIBUTION BY CATEGORY")
    print("-"*80)
    print(f"   {'Category':<25} {'Total Count':>15} {'Percentage':>12}")
    print("-"*80)
    
    total_edges = sum(category_counts.values())
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories:
        percentage = round((count / total_edges * 100), 2) if total_edges > 0 else 0
        print(f"   {category:<25} {count:>15,} {percentage:>11.2f}%")
    
    print("-"*80)
    print(f"   {'TOTAL':<25} {total_edges:>15,} {'100.00%':>12}")
    print()
    
    # Category Details
    print("🔷 CATEGORY DETAILS")
    print("-"*80)
    for category, details in category_details.items():
        print(f"\n   {category}:")
        for edge_type, count in sorted(details.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {edge_type:<35} {count:,}")
    print()
    
    # Thesis Summary
    print("🔷 THESIS SUMMARY (Bab 4 - Hasil & Pembahasan)")
    print("-"*80)
    print(f"""
   Graph Statistics:
   • Total nodes in knowledge graph: {density['total_nodes']:,}
   • Total relationships: {density['total_edges']:,}
   • Graph density: {density['edges_per_node']} relations/node
   • Root resources (K8sResource): {density['root_resources']:,}
   
   Edge Distribution:
   • Structural edges: {category_counts.get('Structural', 0):,} ({round(category_counts.get('Structural', 0)/total_edges*100, 2)}%)
   • Workload edges: {category_counts.get('Workload', 0):,} ({round(category_counts.get('Workload', 0)/total_edges*100, 2)}%)
   • Storage edges: {category_counts.get('Storage', 0):,} ({round(category_counts.get('Storage', 0)/total_edges*100, 2)}%)
   • Configuration edges: {category_counts.get('Configuration', 0):,} ({round(category_counts.get('Configuration', 0)/total_edges*100, 2)}%)
   • Networking edges: {category_counts.get('Networking', 0):,} ({round(category_counts.get('Networking', 0)/total_edges*100, 2)}%)
   • RBAC edges: {category_counts.get('RBAC', 0):,} ({round(category_counts.get('RBAC', 0)/total_edges*100, 2)}%)
   • Autoscaling edges: {category_counts.get('Autoscaling', 0):,} ({round(category_counts.get('Autoscaling', 0)/total_edges*100, 2)}%)
   
   Graph Health:
   • High connectivity indicates comprehensive schema coverage
   • Edge distribution reflects Kubernetes API complexity
   • Structural edges dominate (expected for schema graph)
    """)
    print("="*80)

def save_report(edge_stats, category_counts, category_details, node_stats, density):
    """Save report to JSON file."""
    os.makedirs("logs", exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "graph_overview": density,
        "node_distribution": {stat['label']: stat['count'] for stat in node_stats},
        "edge_distribution": {stat['edge_type']: stat['count'] for stat in edge_stats},
        "category_distribution": dict(category_counts),
        "category_details": {k: dict(v) for k, v in category_details.items()},
        "thesis_summary": {
            "total_nodes": density['total_nodes'],
            "total_edges": density['total_edges'],
            "edges_per_node": density['edges_per_node'],
            "root_resources": density['root_resources'],
        }
    }
    
    report_path = "logs/edge_distribution_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Report saved to: {report_path}")

def main():
    """Main entry point."""
    print("🔌 Connecting to Neo4j...")
    db = Neo4jClient()
    
    print("📊 Analyzing edge distribution...")
    print()
    
    # Get statistics
    edge_stats = get_edge_statistics(db)
    category_counts, category_details = get_category_distribution(db)
    node_stats = get_node_statistics(db)
    density = get_graph_density(db)
    
    # Print report
    print_report(edge_stats, category_counts, category_details, node_stats, density)
    
    # Save report
    save_report(edge_stats, category_counts, category_details, node_stats, density)

if __name__ == "__main__":
    main()