# src/memory/zep_store.py
import logging
from zep_python.client import Zep
from zep_python.types import Message

# Configure Logger
logger = logging.getLogger(__name__)

class ZepMemoryStore:
    def __init__(self):
        # Hardcode API Secret secara eksplisit untuk menghabisi error 401
        self.client = Zep(
            base_url="http://localhost:8000", 
            api_key="z_1dWlkIjoiNGE2YTBkOGYtOTI0ZS00YjY3LWE1ZmUtZjIyYTlkNWI1NGM0In0.kWlj92M-g4J9EKJxmdPW5XWugegbT9FeH4rCQgoq1BIB_v3pH8pgBI3wVlectlmzS2PkOgwJIOAW9QuxcUaUSg"
        )

    def add_message(self, session_id: str, user_msg: str, ai_msg: str):
        """Menyimpan percakapan baru secara aman."""
        try:
            # Sintaks v2 langsung menerima list of dicts
            messages = [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": ai_msg}
            ]
            self.client.memory.add(session_id=session_id, messages=messages)
            logger.info(f"✅ Memory saved for session: {session_id}")
            
        except Exception as e:
            # Graceful Degradation: Chatbot tetap berjalan meski memori gagal menyimpan
            logger.error(f"🚨 Zep Memory Save Failed: {e}. Continuing without memory.")

    def get_history(self, session_id: str, limit: int = 5) -> str:
        """Mengambil riwayat percakapan untuk konteks LLM."""
        try:
            # Sintaks v2 menggunakan memory.get()
            memory = self.client.memory.get(session_id=session_id)
            if not memory or not memory.messages:
                return ""
            
            # Ambil pesan terakhir sesuai limit untuk menghemat token LLM
            recent_messages = memory.messages[-limit:]
            # Ekstrak konten dari object Message
            history = "\n".join([f"{m.role}: {m.content}" for m in recent_messages])
            return history
            
        except Exception as e:
            # Tangkap exception secara spesifik jika sesi belum ada
            logger.info(f"Starting fresh session for {session_id}")
            return ""

    def save_memory(self, session_id: str, role: str, content: str):
        # 1. Konversi identitas LangGraph ke format baku Zep
        zep_role = "user" if role.lower() in ["user", "human"] else "assistant"
        
        # 2. Gunakan parameter 'role_type'
        msg = Message(role_type=zep_role, content=content)
        
        try:
            self.client.memory.add_memory(session_id=session_id, messages=[msg])
        except Exception as e:
            print(f"Zep Save Error: {e}")