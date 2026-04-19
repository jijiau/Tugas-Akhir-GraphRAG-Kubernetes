# tests/conftest.py
"""
Shared pytest configuration for the GraphRAG-Kubernetes test suite.

Filter CLI options (can be combined freely):
  --fixture-type  conceptual|yaml_gen|relationship|followup
  --multi-hop     true|false
  --scope         Namespaced|Cluster

Examples:
  # Run only YAML-generation fixtures
  pytest tests/evaluation/ -m evaluation --fixture-type yaml_gen

  # Run only multi-hop relationship smoke tests
  pytest tests/smoke/ --fixture-type relationship --multi-hop true

  # Run all Cluster-scoped integration tests
  pytest tests/integration/ --scope Cluster
"""
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


# ── CLI filter registration ───────────────────────────────────────────────────

def pytest_addoption(parser):
    """Register custom CLI options for fixture filtering."""
    parser.addoption(
        "--fixture-type",
        action="store",
        default=None,
        metavar="TYPE",
        help="Filter fixtures by type: conceptual|yaml_gen|relationship|followup",
    )
    parser.addoption(
        "--multi-hop",
        action="store",
        default=None,
        metavar="BOOL",
        help="Filter fixtures by multi_hop flag: true|false",
    )
    parser.addoption(
        "--scope",
        action="store",
        default=None,
        metavar="SCOPE",
        help="Filter fixtures by Kubernetes scope: Namespaced|Cluster",
    )


# ── Fixture loading with filter support ───────────────────────────────────────

def _parse_multi_hop(value: str) -> bool:
    """Convert CLI string 'true'/'false' to bool."""
    return value.strip().lower() in ("true", "1", "yes")


# Minimum selection_score a realworld fixture must carry to be included.
# Must stay in sync with SCORE_ACCEPT in scripts/select_realworld_fixtures.py.
REALWORLD_MIN_SCORE = 2.0


def _is_realworld_accepted(data: dict) -> bool:
    """
    Return True only if a realworld fixture was produced by the scoring
    algorithm and met the acceptance threshold.  Manually-dropped files
    that lack selection metadata are excluded so the count is always
    driven by the algorithm, never hardcoded.
    """
    return (
        "selection_scores_breakdown" in data
        and data.get("selection_score", 0.0) >= REALWORLD_MIN_SCORE
    )


def _load_fixture_paths(config=None) -> list:
    """
    Return all fixture JSON paths, optionally filtered by CLI options.

    Filtering is applied in-place so that every parametrized test that uses
    `fixture_path` automatically respects the filter flags — no test needs to
    be changed individually.

    Realworld fixtures are additionally filtered by scoring-algorithm
    acceptance (selection_score >= REALWORLD_MIN_SCORE) regardless of any
    CLI flags, so the number of test cases is never hardcoded.
    """
    all_paths = sorted(FIXTURES_DIR.rglob("*.json"))

    fixture_type = config.getoption("--fixture-type", default=None) if config else None
    multi_hop_raw = config.getoption("--multi-hop", default=None) if config else None
    scope = config.getoption("--scope", default=None) if config else None

    has_cli_filter = any([fixture_type, multi_hop_raw, scope])

    filtered = []
    for p in all_paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue  # Skip malformed; dedicated integrity test catches these

        # Realworld fixtures: always gate on scoring algorithm acceptance
        if data.get("type") == "realworld" and not _is_realworld_accepted(data):
            continue

        # CLI filters (only applied when at least one flag is set)
        if has_cli_filter:
            if fixture_type and data.get("type") != fixture_type:
                continue
            if multi_hop_raw is not None:
                expected = _parse_multi_hop(multi_hop_raw)
                if data.get("multi_hop") != expected:
                    continue
            if scope and data.get("scope", "").lower() != scope.lower():
                continue

        filtered.append(p)

    return filtered


# ── Auto-marker injection ─────────────────────────────────────────────────────

def _marker_for_fixture(data: dict) -> list:
    """
    Return a list of pytest marker names derived from fixture metadata.
    These are applied automatically so tests can be selected via -m.
    """
    markers = []
    ftype = data.get("type", "")
    if ftype in ("conceptual", "yaml_gen", "relationship", "followup"):
        markers.append(ftype)

    if data.get("multi_hop"):
        markers.append("multi_hop")
    else:
        markers.append("single_hop")

    scope = data.get("scope", "").lower()
    if scope == "namespaced":
        markers.append("namespaced")
    elif scope == "cluster":
        markers.append("cluster")

    return markers


# ── pytest_generate_tests — parametrize fixture_path ─────────────────────────

def pytest_generate_tests(metafunc):
    """
    Auto-parametrize any test that declares 'fixture_path' as a parameter.

    Applies CLI filters so only matching fixtures are parametrized.
    Also injects fixture-derived markers (type, multi_hop, scope) onto each
    parametrized item so `-m yaml_gen` or `-m multi_hop` works.
    """
    if "fixture_path" not in metafunc.fixturenames:
        return

    paths = _load_fixture_paths(config=metafunc.config)

    # Build parametrize arguments with per-item markers.
    # In pytest ≥ 8 the id MUST be set inside pytest.param() — a separate
    # ids= kwarg is silently ignored when pytest.param objects are in the list,
    # causing every item to display as [NOTSET].
    params = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            item_marks = [getattr(pytest.mark, m) for m in _marker_for_fixture(data)]
        except Exception:
            item_marks = []
        params.append(pytest.param(p, marks=item_marks, id=p.stem))

    if not params:
        # No fixtures match the active filters — mark the slot as skipped so
        # pytest reports "1 skipped" instead of generating a bogus [NOTSET] id.
        metafunc.parametrize(
            "fixture_path",
            [pytest.param(None, marks=[pytest.mark.skip(reason="No fixtures match the active filter flags")], id="no-match")],
        )
        return

    metafunc.parametrize("fixture_path", params)


# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def agent():
    """LangGraph agent — requires OpenAI + Groq API keys and Neo4j running."""
    from src.chatbot.graph_agent import create_agent_graph
    return create_agent_graph()


@pytest.fixture(scope="session")
def neo4j_client():
    """Neo4j driver — requires NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env."""
    from src.graph.neo4j_client import Neo4jClient
    return Neo4jClient()


@pytest.fixture(scope="session")
def zep_store():
    """SQLite-backed memory store — no external dependencies."""
    from src.memory.zep_store import ZepMemoryStore
    return ZepMemoryStore()


@pytest.fixture(scope="session")
def yaml_validator():
    """YAML validator — requires Neo4j for graph-aware field checks."""
    from src.validation.yaml_validator import YAMLValidator
    return YAMLValidator()


# ── Utility ───────────────────────────────────────────────────────────────────

def load_fixture(path: Path) -> dict:
    """Load and parse a fixture JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))
