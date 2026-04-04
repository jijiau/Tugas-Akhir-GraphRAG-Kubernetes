# tests/integration/test_memory.py
# SQLite memory — tidak butuh Docker atau koneksi eksternal.
import pytest


@pytest.mark.integration
def test_memory_write_read_roundtrip(zep_store):
    sid = "integration-memory-001"
    zep_store.add_message(session_id=sid, user_msg="Apa itu Pod?", ai_msg="Pod adalah unit terkecil di Kubernetes.")
    history = zep_store.get_history(session_id=sid, limit=5)
    assert "Pod" in history
    assert len(history) > 0


@pytest.mark.integration
def test_memory_persists_across_instances():
    """Karena SQLite ada di disk, instance baru harus bisa baca data lama."""
    from src.memory.zep_store import ZepMemoryStore
    sid = "integration-persist-001"
    store1 = ZepMemoryStore()
    store1.add_message(session_id=sid, user_msg="dari instance 1", ai_msg="response 1")

    store2 = ZepMemoryStore()
    history = store2.get_history(session_id=sid, limit=5)
    assert "dari instance 1" in history
