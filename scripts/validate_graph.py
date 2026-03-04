"""
Graph Validation & Statistics Script
=====================================
Validates graph integrity and generates thesis-ready statistics.

Usage:
    python scripts/validate_graph.py

Output:
    - Console summary table
    - logs/graph_statistics_report.json (for thesis appendix)
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.validation.auditor import GraphAuditor


def main():
    print("🔍 Graph Validation & Statistics")
    print("="*70)
    
    auditor = GraphAuditor()
    results = auditor.run_full_audit()
    
    # === NODE COUNTS ===
    print(f"\n📊 NODE STATISTICS:")
    print(f"   {'Label':<35} {'Count':>12}")
    print(f"   {'-'*35} {'-'*12}")
    
    node_counts = results.get('total_nodes', {})
    for label, count in sorted(node_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {label:<35} {count:>12,}")
    
    total_nodes = sum(node_counts.values())
    print(f"   {'-'*35} {'-'*12}")
    print(f"   {'TOTAL':<35} {total_nodes:>12,}")
    
    # === RELATIONSHIP COUNTS ===
    print(f"\n🔗 RELATIONSHIP STATISTICS:")
    print(f"   {'Type':<35} {'Count':>12}")
    print(f"   {'-'*35} {'-'*12}")
    
    rel_counts = results.get('total_relationships', {})
    for rel_type, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {rel_type:<35} {count:>12,}")
    
    total_rels = sum(rel_counts.values())
    print(f"   {'-'*35} {'-'*12}")
    print(f"   {'TOTAL':<35} {total_rels:>12,}")
    
    # === GRAPH DENSITY ===
    density = auditor.get_graph_density()
    print(f"\n📐 GRAPH DENSITY:")
    print(f"   • Edges per Node: {density['edges_per_node']}")
    print(f"   • Node Connectivity: {density['node_connectivity_percent']}%")
    print(f"   • Total Nodes: {density['total_nodes']:,}")
    print(f"   • Total Relationships: {density['total_relationships']:,}")
    
    # === INTEGRITY CHECKS ===
    print(f"\n✅ INTEGRITY CHECKS:")
    orphans = results.get('orphan_resources', 0)
    missing_fields = results.get('missing_field_types', 0)
    broken = results.get('broken_references', 0)
    
    print(f"   • Orphan Resources: {orphans} {'✅' if orphans == 0 else '⚠️'}")
    print(f"   • Missing Field Types: {missing_fields} {'✅' if missing_fields == 0 else '⚠️'}")
    print(f"   • Broken References: {broken} {'✅' if broken == 0 else '⚠️'}")
    
    # === SEMANTIC RELATIONSHIPS ===
    print(f"\n🎯 SEMANTIC RELATIONSHIPS (YAML Patterns):")
    semantic = results.get('semantic_relationships', {})
    for rel_type, count in sorted(semantic.items(), key=lambda x: x[1], reverse=True):
        status = "✅" if count > 0 else "❌"
        print(f"   • {rel_type}: {count} {status}")
    
    # === K8S RESOURCE SUMMARY ===
    k8s_summary = auditor.get_k8s_resource_summary()
    print(f"\n🛡️  KUBERNETES RESOURCE SUMMARY:")
    print(f"   • Total Root Resources: {k8s_summary['total_root_resources']}")
    print(f"   • By Kind:")
    for kind, count in list(k8s_summary['by_kind'].items())[:10]:
        print(f"      - {kind}: {count}")
    
    # === HEALTH SCORE ===
    health_score = results.get('graph_health_score', 0)
    print(f"\n🏥 GRAPH HEALTH SCORE:")
    if health_score >= 90:
        rating = "🏆 EXCELLENT"
    elif health_score >= 70:
        rating = "✅ GOOD"
    elif health_score >= 50:
        rating = "⚠️  ACCEPTABLE"
    else:
        rating = "❌ NEEDS IMPROVEMENT"
    
    print(f"   • Score: {health_score}/100 - {rating}")
    
    # === SAVE REPORT ===
    os.makedirs("logs", exist_ok=True)
    report_path = "logs/graph_statistics_report.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_nodes": total_nodes,
        "total_relationships": total_rels,
        "node_counts": node_counts,
        "relationship_counts": rel_counts,
        "graph_density": density,
        "integrity_checks": {
            "orphan_resources": orphans,
            "missing_field_types": missing_fields,
            "broken_references": broken,
        },
        "semantic_relationships": semantic,
        "k8s_resource_summary": k8s_summary,
        "graph_health_score": health_score,
        "thesis_summary": {
            "nodes": total_nodes,
            "relationships": total_rels,
            "density": density['edges_per_node'],
            "health": health_score,
        }
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Report saved to: {report_path}")
    
    # === THESIS NARRATIVE ===
    print(f"\n📝 Thesis Summary (Bab 4 - Hasil & Pembahasan):")
    print(f"   • Total nodes in knowledge graph: {total_nodes:,}")
    print(f"   • Total relationships: {total_rels:,}")
    print(f"   • Graph density: {density['edges_per_node']:.2f} relations/node")
    print(f"   • Graph health score: {health_score}/100 ({rating})")
    print(f"   • Integrity issues: {orphans + missing_fields + broken} total")
    print()
    print(f"   Kesimpulan: Graph {'sehat dan siap untuk RAG queries' if health_score >= 80 else 'memerlukan perbaikan sebelum demo'}")
    print("="*70)


if __name__ == "__main__":
    main()