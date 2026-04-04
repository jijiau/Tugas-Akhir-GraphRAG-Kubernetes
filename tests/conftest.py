# tests/conftest.py
import json
import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_paths():
    return sorted(FIXTURES_DIR.rglob("*.json"))


def pytest_generate_tests(metafunc):
    """Auto-parametrize any test that declares 'fixture_path' as a parameter."""
    if "fixture_path" in metafunc.fixturenames:
        paths = _load_fixture_paths()
        metafunc.parametrize(
            "fixture_path",
            paths,
            ids=[p.stem for p in paths],
        )


@pytest.fixture(scope="session")
def agent():
    from src.chatbot.graph_agent import create_agent_graph
    return create_agent_graph()


@pytest.fixture(scope="session")
def neo4j_client():
    from src.graph.neo4j_client import Neo4jClient
    return Neo4jClient()


@pytest.fixture(scope="session")
def zep_store():
    from src.memory.zep_store import ZepMemoryStore
    return ZepMemoryStore()


@pytest.fixture(scope="session")
def yaml_validator():
    from src.validation.yaml_validator import YAMLValidator
    return YAMLValidator()


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
