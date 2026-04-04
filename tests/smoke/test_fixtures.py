# tests/smoke/test_fixtures.py
# Parametrized smoke: every fixture must produce a non-empty response with a reasoning path.
import json
from tests.conftest import load_fixture


def test_fixture_runs(fixture_path, agent):
    data = load_fixture(fixture_path)
    result = agent.invoke({
        "question": data["question"],
        "session_id": "smoke_test",
        "messages": [],
        "chat_history": "",
        "extracted_intent": {},
        "graph_context": "",
        "reasoning_path": [],
        "error": None,
    })
    assert result.get("messages"), f"No messages returned for fixture: {fixture_path.stem}"
    assert result["messages"][-1].content.strip(), f"Empty response for fixture: {fixture_path.stem}"
    assert result.get("reasoning_path") is not None, f"reasoning_path missing for: {fixture_path.stem}"
