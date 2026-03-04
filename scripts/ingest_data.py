"""
Kubernetes Swagger → YAML Configuration Graph Ingestion
=========================================================
Parses the Kubernetes OpenAPI spec to build a Knowledge Graph for 
YAML Infrastructure-as-Code generation.

SCOPE:
    ✅ Ingest: definitions (K8s resource schemas for YAML)
       ├─ Properties & $ref (Pass 2)
       ├─ allOf/oneOf/anyOf inheritance (Pass 2.5)
       └─ Semantic YAML patterns (Pass 3)
    
    ❌ Skip: paths (HTTP API specs - handled by kubectl)

Use Case:
    - User asks: "How to create a Deployment?"
    - System generates: Valid Kubernetes YAML configuration
    - User applies: kubectl apply -f generated.yaml

Why Inheritance (Pass 2.5) is INCLUDED:
    - allOf defines YAML field structure (metadata, spec, status)
    - oneOf defines valid alternatives (volume types, probe types)
    - Critical for generating VALID YAML (not just API calls)

Usage:
    python scripts/ingest_data.py

Post-Ingestion:
    python scripts/validate_graph.py  # Run validation separately
"""

import os
import sys
import time
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.parser import SwaggerGraphBuilder
from src.graph.neo4j_client import Neo4jClient

def download_swagger_if_missing():
    """Downloads the Kubernetes Swagger file if it doesn't exist."""
    import urllib.request
    
    swagger_url = "https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json"
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    swagger_path = os.path.join(data_dir, 'kubernetes_swagger.json')
    
    os.makedirs(data_dir, exist_ok=True)
    
    if not os.path.exists(swagger_path):
        print(f"📥 Downloading Kubernetes Swagger from GitHub...")
        print(f"   URL: {swagger_url}")
        urllib.request.urlretrieve(swagger_url, swagger_path)
        print(f"   ✅ Downloaded to: {swagger_path}")
    else:
        file_size = os.path.getsize(swagger_path) / (1024 * 1024)
        print(f"✅ Swagger file found: {swagger_path} ({file_size:.2f} MB)")
    
    return swagger_path

def main():
    """Main ingestion pipeline with progress tracking."""
    print("="*70)
    print("🚀 Kubernetes Swagger → Neo4j Graph Ingestion")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    
    try:
        # Step 1: Ensure Swagger file exists
        swagger_path = download_swagger_if_missing()
        print()
        
        # Step 2: Initialize Parser
        print("📦 Initializing SwaggerGraphBuilder...")
        parser = SwaggerGraphBuilder(swagger_path)
        print()
        
        # Step 3: Run Ingestion (3-Pass Architecture + 2.5)
        print("🔨 Starting 3-Pass Ingestion Process...")
        print("-"*70)
        parser.ingest()
        print("-"*70)
        print()
        
        # Step 4: Summary
        elapsed_time = time.time() - start_time
        print("="*70)
        print("✅ INGESTION COMPLETE!")
        print("="*70)
        print(f"⏱️  Total Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print(f"📈 Graph Status: Ready for validation")
        print()
        print("Next Steps:")
        print("   1. Run: python scripts/validate_graph.py (graph validation)")
        print("   2. Check: logs/graph_statistics_report.json (thesis appendix)")
        print("   3. Run: streamlit run main.py (launch chatbot)")
        print()
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: File not found - {e}")
        print("   Make sure data/kubernetes_swagger.json exists")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Ingestion failed - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up database connections
        Neo4jClient()._instance.close()
        print("🔌 Database connections closed.")

if __name__ == "__main__":
    main()