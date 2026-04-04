# tests/unit/test_zep_store.py
# Memory store sekarang berbasis SQLite — tidak ada mock yang diperlukan.
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def store(tmp_path):
    """Buat store dengan DB sementara agar tidak mengotori data/ saat testing."""
    db_file = tmp_path / "test_memory.db"
    import src.memory.zep_store as mem_module
    # Patch path DB ke tempdir
    with patch.object(mem_module, "_DB_PATH", db_file):
        mem_module._conn = None  # reset singleton
        from src.memory.zep_store import ZepMemoryStore
        yield ZepMemoryStore()
        mem_module._conn = None  # teardown


def test_add_and_get_history(store):
    store.add_message(session_id="s1", user_msg="Apa itu Pod?", ai_msg="Pod adalah unit terkecil.")
    history = store.get_history(session_id="s1", limit=5)
    assert "Apa itu Pod?" in history
    assert "Pod adalah unit terkecil." in history


def test_history_respects_limit(store):
    for i in range(10):
        store.save_memory("s2", "user", f"pesan {i}")
    history = store.get_history(session_id="s2", limit=3)
    lines = [l for l in history.strip().splitlines() if l]
    assert len(lines) == 3


def test_history_order_is_oldest_first(store):
    store.save_memory("s3", "user", "pertama")
    store.save_memory("s3", "assistant", "kedua")
    store.save_memory("s3", "user", "ketiga")
    history = store.get_history(session_id="s3", limit=3)
    lines = history.strip().splitlines()
    assert "pertama" in lines[0]
    assert "ketiga" in lines[-1]


def test_empty_session_returns_empty_string(store):
    result = store.get_history(session_id="nonexistent")
    assert result == ""


def test_no_session_id_is_noop(store):
    store.add_message(session_id=None, user_msg="ignored")  # tidak boleh raise
    assert store.get_history(session_id=None) == ""


def test_add_turn_alias(store):
    store.add_turn("s4", "user", "hello")
    store.add_turn("s4", "assistant", "world")
    history = store.get_context("s4", limit=5)
    assert "hello" in history
    assert "world" in history


def test_multiple_sessions_isolated(store):
    store.add_message(session_id="sessionA", user_msg="A question", ai_msg="A answer")
    store.add_message(session_id="sessionB", user_msg="B question", ai_msg="B answer")
    histA = store.get_history("sessionA")
    histB = store.get_history("sessionB")
    assert "A question" in histA
    assert "B question" not in histA
    assert "B question" in histB
