import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def test_env():
    """1. Check .env loading"""
    load_dotenv()
    required = ["NEO4J_URI", "OPENAI_API_KEY", "GROQ_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"❌ FAIL: Missing env variables: {missing}")
        return False
    print("✅ PASS: Environment variables loaded.")
    return True


def test_neo4j():
    """2. Check Neo4j Connection (Read Only)"""
    from src.graph.neo4j_client import Neo4jClient
    try:
        db = Neo4jClient()
        result = db.execute_query("RETURN 1 as test")
        if result and result[0]["test"] == 1:
            print("✅ PASS: Neo4j connection established.")
            return True
        print("❌ FAIL: Neo4j query returned unexpected result.")
        return False
    except Exception as e:
        print(f"❌ FAIL: Neo4j connection error: {e}")
        return False


def test_memory():
    """3. Check SQLite conversation memory (write + read round-trip)"""
    from src.memory.zep_store import ZepMemoryStore
    try:
        store = ZepMemoryStore()
        store.add_message(session_id="smoke_test", user_msg="ping", ai_msg="pong")
        history = store.get_history(session_id="smoke_test", limit=2)
        if "ping" in history and "pong" in history:
            print("✅ PASS: SQLite memory write+read working.")
            return True
        print("❌ FAIL: Memory round-trip returned unexpected content.")
        return False
    except Exception as e:
        print(f"❌ FAIL: Memory error: {e}")
        return False


def test_llms():
    """4. Check Multi-Agent LLM Keys (Minimal Token Usage)"""
    from src.chatbot.llm_factory import get_thinker_llm, get_speaker_llm
    try:
        thinker = get_thinker_llm()
        thinker.invoke("Say 'OK'")
        print("✅ PASS: OpenAI (Thinker) API working.")

        speaker = get_speaker_llm()
        speaker.invoke("Say 'OK'")
        print("✅ PASS: Groq (Speaker) API working.")
        return True
    except Exception as e:
        print(f"❌ FAIL: LLM API error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting System Smoke Test...\n")
    results = [
        test_env(),
        test_neo4j(),
        test_memory(),
        test_llms(),
    ]
    print("\n" + "=" * 30)
    if all(results):
        print("🎉 ALL SYSTEMS READY. Proceed to Ingestion.")
    else:
        print("⚠️  CRITICAL ERRORS FOUND. Fix .env or Connections first.")
        sys.exit(1)
