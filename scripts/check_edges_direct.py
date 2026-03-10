"""
Direct check: What edges actually exist in Neo4j?
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.graph.neo4j_client import Neo4jClient

db = Neo4jClient()

print("🔍 Checking ACTUAL edges in Neo4j database...")
print("="*70)

# Check all relationship types
result = db.execute_query("""
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
""")

print("\n📊 All relationship types in database:")
for record in result:
    print(f"   {record['type']:35} : {record['count']}")

# Check specific semantic edges
semantic_edges = [
    'CONTAINS_POD_TEMPLATE',
    'CONTAINS_JOB_TEMPLATE',
    'CLAIMS_VOLUME',
    'EXTENDS',
    'ONE_OF',
]

print("\n🔎 Checking specific semantic edges:")
for edge_type in semantic_edges:
    result = db.execute_query(f"""
        MATCH ()-[r:{edge_type}]->()
        RETURN count(r) as count
    """)
    count = result[0]['count'] if result else 0
    status = "✅" if count > 0 else "❌"
    print(f"   {status} {edge_type:30} : {count}")

# Check kind values
print("\n📊 Top kind values:")
result = db.execute_query("""
    MATCH (d:Definition) WHERE d.is_root = true
    RETURN d.kind as kind, count(*) as count
    ORDER BY count DESC
    LIMIT 10
""")
for record in result:
    print(f"   {record['kind']:30} : {record['count']}")