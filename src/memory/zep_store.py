# src/memory/zep_store.py
#
# SQLite-based conversation memory — drop-in replacement for Zep.
# Alasan penggantian: Zep v1 memanggil LLM internal (entity extraction)
# yang memboroskan token dan menambah beban infrastruktur tanpa nilai tambah
# untuk penelitian ini. SQLite memberikan persistensi yang cukup, zero token,
# dan zero Docker dependency tambahan.
#
# Public API identik dengan versi Zep sebelumnya sehingga graph_agent.py
# tidak perlu diubah sama sekali.

import sqlite3
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Lokasi file SQLite — disimpan di folder data/ agar tidak masuk ke git
_DB_PATH = Path(__file__).parent.parent.parent / "data" / "conversation_memory.db"


def _get_connection() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
    conn.commit()
    return conn


# Singleton connection — satu koneksi per proses
_conn: sqlite3.Connection | None = None


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _get_connection()
        logger.info(f"SQLiteMemory: database di {_DB_PATH}")
    return _conn


# ---------------------------------------------------------------------------
# Public store class — API identik dengan ZepMemoryStore sebelumnya
# ---------------------------------------------------------------------------
class ZepMemoryStore:
    """
    Conversation memory berbasis SQLite.
    Nama kelas dipertahankan 'ZepMemoryStore' agar tidak ada perubahan
    di graph_agent.py atau file lain yang mengimpornya.
    """

    def __init__(self):
        # Inisialisasi DB saat pertama kali diinstansiasi
        _db()
        logger.info("ZepMemoryStore: menggunakan SQLite lokal (tanpa Zep server).")

    # ── internal save ───────────────────────────────────────────────────────

    def save_memory(self, session_id: str, role: str, content: str):
        role = "user" if role.lower() in ("user", "human") else "assistant"
        try:
            _db().execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            _db().commit()
        except Exception as e:
            logger.warning(f"SQLiteMemory: gagal menyimpan pesan: {e}")

    # ── internal get ────────────────────────────────────────────────────────

    def get_memory(self, session_id: str, limit: int = 5) -> str:
        try:
            rows = _db().execute(
                """
                SELECT role, content FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit)
            ).fetchall()
            # Rows dikembalikan dari terbaru ke terlama — balik urutannya
            rows = list(reversed(rows))
            return "\n".join(f"{role}: {content}" for role, content in rows)
        except Exception as e:
            logger.warning(f"SQLiteMemory: gagal mengambil riwayat: {e}")
            return ""

    # ── public aliases (semua calling convention didukung) ──────────────────

    def add_message(self, session_id: str = None, role: str = None,
                    content: str = None, user_msg: str = None,
                    ai_msg: str = None, message: str = None, **kwargs):
        if not session_id:
            return

        if user_msg and ai_msg:
            self.save_memory(session_id=session_id, role="user",      content=user_msg)
            self.save_memory(session_id=session_id, role="assistant", content=ai_msg)
            return

        resolved_content = content or message or user_msg or ai_msg or kwargs.get("text", "")
        if not resolved_content:
            return

        resolved_role = role or ("user" if user_msg else ("assistant" if ai_msg else "user"))
        self.save_memory(session_id=session_id, role=resolved_role, content=resolved_content)

    def get_history(self, session_id: str = None, limit: int = 5, **kwargs) -> str:
        if not session_id:
            return ""
        return self.get_memory(session_id=session_id, limit=limit)

    def add_turn(self, session_id: str, role: str, content: str):
        self.save_memory(session_id=session_id, role=role, content=content)

    def get_context(self, session_id: str, limit: int = 5) -> str:
        return self.get_memory(session_id=session_id, limit=limit)
