"""
Quick test for local Neo4j connection
"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def test_connection():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    print(f"🔌 Testing connection to {uri}...")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            value = result.single()["test"]
            if value == 1:
                print("✅ Connection successful!")
                return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_connection()