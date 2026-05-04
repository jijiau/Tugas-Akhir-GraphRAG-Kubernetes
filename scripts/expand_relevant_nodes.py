#!/usr/bin/env python3
"""
scripts/expand_relevant_nodes.py

Expands `relevant_nodes` and `expected_path` in all fixture JSONs by querying
Neo4j for all nodes and edges actually traversed at evaluation depth.

Why this is needed:
  - The retriever returns 8–15 intermediate structural nodes per query
    (DeploymentSpec, PodTemplateSpec, PodSpec, Container, etc.)
  - Old ground truth only listed 2–4 "key" nodes per fixture
  - This mismatch drove precision_at_k = 0.14, suppressing RetQ to 0.53
  - After expansion, ground truth reflects what the retriever actually traverses

Usage:
    python scripts/expand_relevant_nodes.py --dry-run   # preview changes
    python scripts/expand_relevant_nodes.py             # write to fixtures
"""
import sys
import json
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.graph.neo4j_client import Neo4jClient
from src.graph.queries import _ALL_EDGE_TYPES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"

# Depth by fixture type — mirrors _DEPTH_BY_INTENT in custom_retriever.py
DEPTH_BY_TYPE = {
    "conceptual":      2,   # conceptual questions → explain intent → depth 2
    "followup":        2,
    "yaml_gen":        3,
    "relationship":    3,
    "planning":        3,
    "troubleshooting": 3,
    "command":         3,
    "realworld":       3,
}
DEFAULT_DEPTH = 3

_EXPAND_NODES_QUERY_TPL = (
    "MATCH p = (root:Definition {{name: $root_name}})"
    " -[:" + _ALL_EDGE_TYPES + "*1..{depth}]->(leaf:Definition)"
    " UNWIND nodes(p) AS n"
    " RETURN DISTINCT n.name AS name, n.fullName AS fullName"
)

_EXPAND_EDGES_QUERY_TPL = (
    "MATCH p = (root:Definition {{name: $root_name}})"
    " -[:" + _ALL_EDGE_TYPES + "*1..{depth}]->(leaf:Definition)"
    " WITH p LIMIT 500"
    " WITH [i IN range(0, size(nodes(p))-2) | {{"
    "   parent:   nodes(p)[i].name,"
    "   child:    nodes(p)[i+1].name,"
    "   rel_type: type(relationships(p)[i])"
    " }}] AS edges"
    " UNWIND edges AS edge"
    " RETURN DISTINCT edge.parent AS parent,"
    "                 edge.child  AS child,"
    "                 edge.rel_type AS rel_type"
)


def _get_root_short_name(db: Neo4jClient, resource_full: str) -> str | None:
    """Return the Neo4j `name` (short) for a given fullName."""
    rows = db.execute_query(
        "MATCH (d:Definition {fullName: $fn}) RETURN d.name AS name LIMIT 1",
        {"fn": resource_full},
    )
    if rows:
        return rows[0]["name"]
    # Fallback: last segment of dotted name
    return resource_full.split(".")[-1] if resource_full else None


def expand_fixture(db: Neo4jClient, fixture: dict) -> tuple[list, list, int, int]:
    """
    Returns (new_relevant_nodes, new_expected_path, nodes_added, edges_added).
    Merges Neo4j traversal results into the existing ground truth lists.
    """
    resource_full = fixture.get("resource", "")
    fixture_type  = fixture.get("type", "")
    depth = DEPTH_BY_TYPE.get(fixture_type, DEFAULT_DEPTH)

    gt = fixture.get("ground_truth", {})
    existing_nodes = set(gt.get("relevant_nodes", []))
    existing_edges = set(gt.get("expected_path", []))

    if not resource_full:
        return sorted(existing_nodes), sorted(existing_edges), 0, 0

    root_short = _get_root_short_name(db, resource_full)
    if not root_short:
        logger.warning(f"  Could not resolve root for '{resource_full}' — skipping expansion")
        return sorted(existing_nodes), sorted(existing_edges), 0, 0

    # Expand nodes
    node_query = _EXPAND_NODES_QUERY_TPL.format(depth=depth)
    node_rows  = db.execute_query(node_query, {"root_name": root_short})

    # Always include root itself
    root_row = db.execute_query(
        "MATCH (d:Definition {name: $n}) RETURN d.name AS name, d.fullName AS fullName LIMIT 1",
        {"n": root_short},
    )

    new_full_names = set(existing_nodes)
    for row in node_rows + root_row:
        fn = row.get("fullName")
        if fn:
            new_full_names.add(fn)

    # Expand edges
    edge_query = _EXPAND_EDGES_QUERY_TPL.format(depth=depth)
    edge_rows  = db.execute_query(edge_query, {"root_name": root_short})

    new_edges = set(existing_edges)
    for row in edge_rows:
        edge_str = f"{row['parent']} -[{row['rel_type']}]-> {row['child']}"
        new_edges.add(edge_str)

    nodes_added = len(new_full_names) - len(existing_nodes)
    edges_added = len(new_edges) - len(existing_edges)

    return sorted(new_full_names), sorted(new_edges), nodes_added, edges_added


def process_fixtures(dry_run: bool = False):
    db = Neo4jClient()
    total_fixtures = 0
    total_nodes_added = 0
    total_edges_added = 0
    skipped = 0

    fixture_files = sorted(FIXTURES_DIR.rglob("*.json"))
    logger.info(f"Found {len(fixture_files)} fixture files in {FIXTURES_DIR}")

    for fpath in fixture_files:
        try:
            with open(fpath, encoding="utf-8") as f:
                fixture = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read {fpath.name}: {e}")
            skipped += 1
            continue

        if "ground_truth" not in fixture:
            logger.warning(f"Skipping {fpath.name}: no ground_truth field")
            skipped += 1
            continue

        new_nodes, new_edges, nodes_added, edges_added = expand_fixture(db, fixture)
        total_fixtures += 1
        total_nodes_added += nodes_added
        total_edges_added += edges_added

        label = fpath.relative_to(FIXTURES_DIR)
        logger.info(f"  {label}: +{nodes_added} nodes, +{edges_added} edges")

        if not dry_run:
            fixture["ground_truth"]["relevant_nodes"] = new_nodes
            fixture["ground_truth"]["expected_path"]  = new_edges
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(fixture, f, indent=2, ensure_ascii=False)
                f.write("\n")

    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{mode}Summary:")
    print(f"  Processed : {total_fixtures} fixtures  ({skipped} skipped)")
    print(f"  Nodes added: {total_nodes_added}")
    print(f"  Edges added: {total_edges_added}")
    if dry_run:
        print("\n  Re-run without --dry-run to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description="Expand relevant_nodes + expected_path in fixture JSONs from Neo4j traversal"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()
    process_fixtures(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
