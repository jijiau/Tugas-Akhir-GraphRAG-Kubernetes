# src/memory/zep_store.py
import logging

logger = logging.getLogger(__name__)

ZEP_BASE_URL = "http://localhost:8000"
ZEP_API_KEY = "z_1dWlkIjoiNGE2YTBkOGYtOTI0ZS00YjY3LWE1ZmUtZjIyYTlkNWI1NGM0In0.kWlj92M-g4J9EKJxmdPW5XWugegbT9FeH4rCQgoq1BIB_v3pH8pgBI3wVlectlmzS2PkOgwJIOAW9QuxcUaUSg"


def _init_client():
    """
    Try importing zep_python v2 (Zep) first, then fall back to v1 (ZepClient).
    Returns (client, version) tuple.
    """
    try:
        from zep_python.client import Zep
        client = Zep(base_url=ZEP_BASE_URL, api_key=ZEP_API_KEY)
        logger.info("ZepMemoryStore: using zep-python v2 (Zep client)")
        return client, "v2"
    except (ImportError, Exception):
        pass

    try:
        from zep_python import ZepClient
        client = ZepClient(base_url=ZEP_BASE_URL, api_key=ZEP_API_KEY)
        logger.info("ZepMemoryStore: using zep-python v1 (ZepClient)")
        return client, "v1"
    except (ImportError, Exception):
        pass

    return None, None


class ZepMemoryStore:
    def __init__(self):
        self.client, self.version = _init_client()
        if self.client is None:
            logger.warning("ZepMemoryStore: could not initialize Zep client. Memory will be disabled.")

    # ── Core methods ────────────────────────────────────────────────────────────

    def save_memory(self, session_id: str, role: str, content: str):
        """Save a single message turn to Zep."""
        if self.client is None:
            return
        try:
            zep_role = "user" if role.lower() in ["user", "human"] else "assistant"

            if self.version == "v2":
                from zep_python.types import Message
                msg = Message(role_type=zep_role, content=content, role=zep_role)
                self.client.memory.add(session_id=session_id, messages=[msg])
            else:
                from zep_python.types import Message as V1Message, Memory
                msg = V1Message(role=zep_role, content=content)
                memory = Memory(messages=[msg])
                self.client.memory.add_memory(session_id=session_id, memory=memory)

            logger.info(f"Memori tersimpan untuk sesi: {session_id}")
        except Exception as e:
            logger.error(f"Zep Save Error: {e}")
            print(f"Zep Memory Save Failed: {e}. Continuing without memory.")

    def get_memory(self, session_id: str, limit: int = 5) -> str:
        """Retrieve memory for a session, returning summary or last N messages."""
        if self.client is None:
            return ""
        try:
            if self.version == "v2":
                memory = self.client.memory.get(session_id=session_id)
            else:
                memory = self.client.memory.get_memory(session_id=session_id)

            if memory and hasattr(memory, "summary") and memory.summary and memory.summary.content:
                return memory.summary.content

            if memory and hasattr(memory, "messages") and memory.messages:
                msgs = memory.messages[-limit:]
                history = [
                    f"{m.role_type if hasattr(m, 'role_type') else m.role}: {m.content}"
                    for m in msgs
                ]
                return "\n".join(history)

            return ""
        except Exception as e:
            logger.warning(f"Belum ada memori untuk {session_id}: {e}")
            return ""

    # ── Flexible alias: add_message ─────────────────────────────────────────────
    # Supports all calling conventions:
    #   add_message(session_id, role, content)
    #   add_message(session_id=..., user_msg=..., ai_msg=...)
    #   add_message(session_id=..., role=..., message=...)

    def add_message(self, session_id: str = None, role: str = None,
                    content: str = None, user_msg: str = None,
                    ai_msg: str = None, message: str = None, **kwargs):
        if not session_id:
            return

        # Case: both user_msg and ai_msg provided → save two turns
        if user_msg and ai_msg:
            self.save_memory(session_id=session_id, role="user", content=user_msg)
            self.save_memory(session_id=session_id, role="assistant", content=ai_msg)
            return

        # Case: single message with resolved content and role
        resolved_content = content or message or user_msg or ai_msg or kwargs.get("text", "")
        if not resolved_content:
            return

        resolved_role = role or ("user" if user_msg else ("assistant" if ai_msg else "user"))
        self.save_memory(session_id=session_id, role=resolved_role, content=resolved_content)

    # ── Flexible alias: get_history ─────────────────────────────────────────────
    # Supports:
    #   get_history(session_id)
    #   get_history(session_id=..., limit=10)

    def get_history(self, session_id: str = None, limit: int = 5, **kwargs) -> str:
        if not session_id:
            return ""
        return self.get_memory(session_id=session_id, limit=limit)

    # ── Additional aliases ───────────────────────────────────────────────────────

    def add_turn(self, session_id: str, role: str, content: str):
        self.save_memory(session_id=session_id, role=role, content=content)

    def get_context(self, session_id: str, limit: int = 5) -> str:
        return self.get_memory(session_id=session_id, limit=limit)