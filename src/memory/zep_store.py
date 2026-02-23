from zep_cloud import Zep
from src.config.settings import settings
from typing import List

class ZepMemoryStore:
    def __init__(self):
        self.client = Zep(
            base_url=settings.zep_base_url,
            api_key=settings.zep_api_key
        )

    def get_history(self, session_id: str, limit: int = 5) -> str:
        """Retrieves summarized chat history."""
        try:
            # Zep automatically summarizes long conversations
            session = self.client.memory.get_session(session_id)
            messages = session.messages[-limit:] if session.messages else []
            return "\n".join([f"{m.role}: {m.content}" for m in messages])
        except Exception:
            return "No history found."

    def add_message(self, session_id: str, user_msg: str, ai_msg: str):
        """Adds a new exchange to Zep."""
        try:
            self.client.memory.add_messages(
                session_id=session_id,
                messages=[
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": ai_msg}
                ]
            )
        except Exception as e:
            # Fail silently to avoid breaking chat flow
            print(f"Zep Save Error: {e}")