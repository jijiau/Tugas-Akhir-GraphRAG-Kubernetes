# test_zep_memory.py
# Tests Zep memory (save & retrieve) without consuming any LLM tokens.
# Run: python test_zep_memory.py

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ZEP_BASE_URL = "http://localhost:8000"
ZEP_API_KEY  = "z_1dWlkIjoiNGE2YTBkOGYtOTI0ZS00YjY3LWE1ZmUtZjIyYTlkNWI1NGM0In0.kWlj92M-g4J9EKJxmdPW5XWugegbT9FeH4rCQgoq1BIB_v3pH8pgBI3wVlectlmzS2PkOgwJIOAW9QuxcUaUSg"
TEST_SESSION = "test-session-zep-001"

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []

def check(label: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} {label}"
    if detail:
        msg += f"  →  {detail}"
    print(msg)
    results.append((label, condition))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Connectivity check (no auth needed)
# ─────────────────────────────────────────────────────────────────────────────
def test_connectivity():
    print("\n── 1. Zep Server Connectivity ──────────────────────────────────")
    try:
        import urllib.request
        req = urllib.request.urlopen(f"{ZEP_BASE_URL}/healthz", timeout=5)
        check("HTTP /healthz reachable", req.status == 200, f"status={req.status}")
    except Exception as e:
        check("HTTP /healthz reachable", False, str(e))
        print(f"\n{FAIL} Cannot reach Zep at {ZEP_BASE_URL}. Is the container running?")
        print("  Run: docker compose up -d && docker logs zep-memory")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Client initialisation
# ─────────────────────────────────────────────────────────────────────────────
def init_client():
    print("\n── 2. Client Initialisation ────────────────────────────────────")
    client, version = None, None

    try:
        from zep_python.client import Zep
        client  = Zep(base_url=ZEP_BASE_URL, api_key=ZEP_API_KEY)
        version = "v2"
        check("zep-python v2 import", True, "using Zep()")
    except Exception as e:
        check("zep-python v2 import", False, str(e))

    if client is None:
        try:
            from zep_python import ZepClient
            client  = ZepClient(base_url=ZEP_BASE_URL, api_key=ZEP_API_KEY)
            version = "v1"
            check("zep-python v1 import", True, "using ZepClient()")
        except Exception as e:
            check("zep-python v1 import", False, str(e))

    if client is None:
        print(f"\n{FAIL} Could not initialise any Zep client.")
        print("  Install with: pip install zep-python")
        sys.exit(1)

    print(f"{INFO} Using zep-python {version}")
    return client, version


# ─────────────────────────────────────────────────────────────────────────────
# 3. Save messages
# ─────────────────────────────────────────────────────────────────────────────
def test_save(client, version: str):
    print("\n── 3. Save Messages ────────────────────────────────────────────")

    conversations = [
        ("user",      "Apa itu Deployment di Kubernetes?"),
        ("assistant", "Deployment adalah resource Kubernetes untuk mengelola stateless application."),
        ("user",      "Bagaimana cara menambahkan PVC ke dalamnya?"),
        ("assistant", "Tambahkan volumes dan volumeMounts ke spec container, lalu buat PersistentVolumeClaim."),
    ]

    for role, content in conversations:
        try:
            if version == "v2":
                from zep_python.types import Message
                msg = Message(role_type=role, content=content, role=role)
                client.memory.add(session_id=TEST_SESSION, messages=[msg])
            else:
                from zep_python.types import Message as V1Msg, Memory
                msg    = V1Msg(role=role, content=content)
                memory = Memory(messages=[msg])
                client.memory.add_memory(session_id=TEST_SESSION, memory=memory)

            check(f"Save [{role}] message", True, f'"{content[:50]}..."')
        except Exception as e:
            check(f"Save [{role}] message", False, str(e))

    # Give Zep a moment to persist
    time.sleep(1)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Retrieve messages
# ─────────────────────────────────────────────────────────────────────────────
def test_retrieve(client, version: str):
    print("\n── 4. Retrieve Memory ──────────────────────────────────────────")
    try:
        if version == "v2":
            memory = client.memory.get(session_id=TEST_SESSION)
        else:
            memory = client.memory.get_memory(session_id=TEST_SESSION)

        check("Memory object returned", memory is not None)

        has_messages = (
            hasattr(memory, "messages")
            and memory.messages
            and len(memory.messages) > 0
        )
        check(
            "Messages present in memory",
            has_messages,
            f"{len(memory.messages)} message(s)" if has_messages else "no messages"
        )

        has_summary = (
            hasattr(memory, "summary")
            and memory.summary
            and getattr(memory.summary, "content", None)
        )
        check(
            "Summary generated by Zep",
            has_summary,
            "summary available" if has_summary else "not yet generated (normal for small history)"
        )

        if has_messages:
            print(f"\n{INFO} Last 4 messages retrieved:")
            for m in memory.messages[-4:]:
                role    = getattr(m, "role_type", getattr(m, "role", "?"))
                content = getattr(m, "content", "")
                print(f"    [{role}] {content[:80]}")

        if has_summary:
            print(f"\n{INFO} Zep summary:\n    {memory.summary.content[:200]}")

    except Exception as e:
        check("Retrieve memory", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Simulate graph_agent flow (no LLM calls)
# ─────────────────────────────────────────────────────────────────────────────
def test_agent_flow():
    print("\n── 5. Simulate Agent Memory Flow (no LLM) ──────────────────────")
    try:
        # Import your actual store
        sys.path.insert(0, ".")
        from src.memory.zep_store import ZepMemoryStore

        store = ZepMemoryStore()
        sid   = "agent-flow-test-001"

        # Simulate turn 1
        store.add_message(
            session_id=sid,
            user_msg ="Apa itu StatefulSet?",
            ai_msg   ="StatefulSet digunakan untuk aplikasi stateful seperti database."
        )
        check("add_message() turn 1", True)

        # Simulate turn 2
        store.add_message(
            session_id=sid,
            user_msg ="Tambahkan PVC ke dalamnya.",
            ai_msg   ="Baik, berikut konfigurasi StatefulSet dengan PVC..."
        )
        check("add_message() turn 2", True)

        # Retrieve history — this is what graph_agent passes to the LLM
        history = store.get_history(session_id=sid, limit=5)
        check(
            "get_history() returns non-empty string",
            bool(history and history.strip()),
            f"{len(history)} chars"
        )

        print(f"\n{INFO} History that would be injected into LLM prompt:")
        for line in history.splitlines():
            print(f"    {line}")

    except ImportError as e:
        check("Import ZepMemoryStore", False, f"{e} — skipping agent flow test")
    except Exception as e:
        check("Agent flow simulation", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
def print_summary():
    print("\n── Summary ─────────────────────────────────────────────────────")
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    color  = "\033[92m" if passed == total else "\033[93m"
    print(f"{color}{passed}/{total} checks passed\033[0m")
    if passed < total:
        print("\nFailed checks:")
        for label, ok in results:
            if not ok:
                print(f"  {FAIL} {label}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Zep Memory Test  (zero LLM tokens)")
    print("=" * 60)

    test_connectivity()
    client, version = init_client()
    test_save(client, version)
    test_retrieve(client, version)
    test_agent_flow()
    print_summary()