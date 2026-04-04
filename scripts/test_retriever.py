# scripts/test_retriever.py
import json
from src.chatbot.custom_retriever import StatefulK8sRetriever
from dotenv import load_dotenv

# Muat environment agar koneksi Neo4j terbuka
load_dotenv()

def debug_graph_retrieval():
    retriever = StatefulK8sRetriever()
    
    # Simulasi output dari LLM Thinker (Intent Extraction)
    # Kita buat manual supaya HEMAT TOKEN (tidak memanggil OpenAI)
    mock_intent = {
        "primary_resource": "Deployment",
        "related_concepts": ["nginx", "container", "replicas"]
    }
    
    print(f"🔍 Testing retrieval for: {mock_intent['primary_resource']}")
    print("-" * 50)
    
    # Panggil fungsi retriever yang baru kita perbaiki
    context = retriever.retrieve_context(mock_intent)
    
    # Cek hasil
    if "Error" in context or "Tidak ada" in context:
        print(f"❌ RETRIEVAL FAILED!")
        print(f"Detail: {context}")
    else:
        print(f"✅ RETRIEVAL SUCCESS!")
        # Parse kembali ke JSON agar enak dibaca di terminal
        parsed_data = json.loads(context)
        print(json.dumps(parsed_data, indent=4))

if __name__ == "__main__":
    debug_graph_retrieval()