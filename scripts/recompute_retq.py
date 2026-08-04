"""
Recompute RetQ metrics from existing JSONL sidecars using fixed measurement logic.

Bug fixed: leaf resources (Secret, ConfigMap, Toleration) have no child Definition
nodes → PATH_EDGES_QUERY returns [] → reasoning_path=[] → R=∅ → RetQ=0 spuriously,
even when the root node was correctly retrieved and the answer is correct.

Fix: include RootResource from graph_context JSON in retrieved set R before processing
reasoning_path. For non-empty paths the root already appears as the first parent token,
so this is a no-op for all other fixtures (verified: 0 side effects).

Usage:
  python scripts/recompute_retq.py                   # patch graphrag only
  python scripts/recompute_retq.py --mode vector      # patch vector only
  python scripts/recompute_retq.py --mode all         # patch both
  python scripts/recompute_retq.py --dry-run          # show changes without writing
"""
import sys
import re
import json
import csv
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DATA_DIR     = Path(__file__).parent.parent / "data"

_RELATION_RE = re.compile(r"-\[([^\]]+)\]->?")


def _node_tokens(step: str) -> list:
    cleaned = _RELATION_RE.sub(" ", step)
    return [t for t in cleaned.split() if t]


def compute_retq_fixed(
    reasoning_path: list,
    relevant_nodes: list,
    root_resource: str = "",
) -> dict:
    """
    Set-based Precision/Recall/F1 (Manning et al. 2008) with leaf-resource bug fix.

    R = {root_resource (if provided)} ∪ {nodes on reasoning_path}
    G = {short names of relevant_nodes from ground truth}
    """
    expected_nodes = set(n.split(".")[-1] for n in relevant_nodes)
    retrieved_nodes: list = []
    seen_nodes: set = set()

    # Include matched root node in R even when reasoning_path is empty.
    if root_resource:
        _rs = root_resource.split(".")[-1]
        seen_nodes.add(_rs)
        retrieved_nodes.append(_rs)

    for step in reasoning_path:
        for tok in _node_tokens(step):
            if tok not in seen_nodes:
                seen_nodes.add(tok)
                retrieved_nodes.append(tok)

    retrieved_set = set(retrieved_nodes)
    intersection  = retrieved_set & expected_nodes
    precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
    recall    = len(intersection) / len(expected_nodes) if expected_nodes else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision":           precision,
        "recall":              recall,
        "f1":                  f1,
        "retq_score":          f1,
        "n_retrieved_nodes":   len(retrieved_nodes),
        "n_relevant_nodes":    len(expected_nodes),
        "n_node_intersection": len(intersection),
    }


def load_fixtures() -> dict:
    """Return dict {fixture_id: fixture_dict} for all fixtures in tests/fixtures/."""
    fixtures: dict = {}
    for fp in FIXTURES_DIR.rglob("*.json"):
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
            fid = d.get("id")
            if fid:
                fixtures[fid] = d
        except Exception as exc:
            print(f"  [WARN] Could not load {fp.name}: {exc}")
    return fixtures


def patch_csv(csv_path: Path, retq_by_id: dict, dry_run: bool) -> int:
    """
    Patch retq_* columns (and n_retrieved_nodes, n_node_intersection) in csv_path.
    Returns count of rows actually changed.
    """
    if not csv_path.exists():
        print(f"    [SKIP] {csv_path.name} not found")
        return 0

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    changed = 0
    for row in rows:
        fid = row.get("id")
        if fid not in retq_by_id:
            continue
        new = retq_by_id[fid]
        old_f1 = float(row.get("retq_retq_score") or 0)
        new_f1 = new["retq_score"]
        if abs(new_f1 - old_f1) < 1e-9:
            continue
        row["retq_precision"]      = f"{new['precision']:.6f}"
        row["retq_recall"]         = f"{new['recall']:.6f}"
        row["retq_f1"]             = f"{new['f1']:.6f}"
        row["retq_retq_score"]     = f"{new['retq_score']:.6f}"
        row["n_retrieved_nodes"]   = new["n_retrieved_nodes"]
        row["n_node_intersection"] = new["n_node_intersection"]
        changed += 1
        print(f"      {fid:<50} retq_f1 {old_f1:.4f} -> {new_f1:.4f}")

    if not dry_run and changed:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="graphrag",
                        choices=["graphrag", "vector", "all"],
                        help="Which mode JSONL to process (default: graphrag)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print changes without writing files")
    args = parser.parse_args()

    modes = ["graphrag", "vector"] if args.mode == "all" else [args.mode]

    print("Loading fixtures …")
    fixtures = load_fixtures()
    print(f"  {len(fixtures)} fixtures loaded\n")

    for mode in modes:
        print(f"-- Mode: {mode} --")
        jsonl_path = DATA_DIR / f"eval_cases_{mode}.jsonl"
        if not jsonl_path.exists():
            print(f"  [SKIP] {jsonl_path.name} not found\n")
            continue

        retq_by_id: dict = {}
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row     = json.loads(line)
                fid     = row["id"]
                fixture = fixtures.get(fid)
                if not fixture:
                    continue

                relevant_nodes = fixture.get("ground_truth", {}).get("relevant_nodes", [])
                reasoning_path = row.get("reasoning_path", [])
                graph_context  = row.get("graph_context", "")

                _root = ""
                try:
                    _gc = json.loads(graph_context) if graph_context else {}
                    if isinstance(_gc, dict):
                        _root = _gc.get("RootResource", "")
                except Exception:
                    _root = ""

                retq_by_id[fid] = compute_retq_fixed(reasoning_path, relevant_nodes, _root)

        print(f"  Recomputed RetQ for {len(retq_by_id)} fixtures")

        total_changed = 0
        for csv_name in (f"eval_results_{mode}.csv", f"eval_results_{mode}_final.csv"):
            csv_path = DATA_DIR / csv_name
            print(f"  Patching {csv_name}:")
            n = patch_csv(csv_path, retq_by_id, dry_run=args.dry_run)
            print(f"    -> {n} rows changed")
            total_changed += n

        # Aggregate summary
        all_new_f1 = [v["retq_score"] for v in retq_by_id.values()]
        avg = sum(all_new_f1) / len(all_new_f1) if all_new_f1 else 0.0
        print(f"  Mean RetQ (new, n={len(all_new_f1)}): {avg:.4f}\n")

    if args.dry_run:
        print("[DRY RUN] No files written.")
    else:
        print("Done. CSVs patched in-place.")


if __name__ == "__main__":
    main()
