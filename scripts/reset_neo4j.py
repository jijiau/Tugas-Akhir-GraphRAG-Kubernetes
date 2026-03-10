"""
Nuclear reset: Drop and recreate entire database
"""
import os
import sys

# Add parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph.neo4j_client import Neo4jClient

db = Neo4jClient()

print("☢️  NUCLEAR RESET - This will delete ALL data!")
confirm = input("Type 'YES' to confirm: ")
if confirm != 'YES':
    print("Aborted.")
    sys.exit()

print("\n🗑️  Deleting all nodes and relationships...")
db.execute_query("MATCH (n) DETACH DELETE n")

print("🗑️  Dropping all constraints...")
try:
    # Neo4j 4.x+ syntax
    db.execute_query("DROP CONSTRAINT definition_name_unique")
    db.execute_query("DROP CONSTRAINT constraint_definition_name")
    db.execute_query("DROP CONSTRAINT definition_id_unique")
    print("   ✓ Constraints dropped")
except Exception as e:
    print(f"   ⚠️  Could not drop: {e}")

print("\n🔍 Verifying cleanup...")
nodes = db.execute_query("MATCH (n) RETURN count(n) as c")
constraints = db.execute_query("SHOW CONSTRAINTS")

print(f"   Remaining nodes: {nodes[0]['c'] if nodes else 'ERROR'}")
print(f"   Remaining constraints: {len(constraints)}")

if nodes and nodes[0]['c'] == 0:
    print("\n✅ Database is clean - ready for fresh ingestion")
else:
    print("\n❌ Database still has data - check Neo4j Desktop")