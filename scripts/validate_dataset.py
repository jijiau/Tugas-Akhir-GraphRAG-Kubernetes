# scripts/validate_dataset.py
"""
Dataset Validity Script — Lima upaya validitas dataset (tanpa Neo4j wajib).

Upaya:
  1. source_reference  — tambah URL docs resmi K8s / SO ke setiap fixture
  2. so_metadata       — tambah so_url + ekstrak so_answer_score dari realworld fixture
  3. yaml_validation   — validasi sintaksis + skema YAML ground truth (yaml_gen)
  4. traceability      — generate traceability_matrix.csv (coverage framework)
  5. path_validation   — verifikasi expected_path ke Neo4j (OPSIONAL, skip jika offline)

Output:
  - Fixture JSON diperbarui in-place
  - data/traceability_matrix.csv
  - data/fixture_validation_report.csv
  - data/dataset_validity_summary.txt

Usage:
  python scripts/validate_dataset.py           # semua upaya, path skip jika Neo4j offline
  python scripts/validate_dataset.py --skip-neo4j   # paksa skip path validation
  python scripts/validate_dataset.py --dry-run       # tidak tulis file apapun
"""
import sys
import json
import csv
import re
import argparse
import logging
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DATA_DIR     = Path(__file__).parent.parent / "data"


# ── 1. Source reference mapping ───────────────────────────────────────────────
_K8S_DOCS = {
    "Deployment":               "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
    "StatefulSet":              "https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/",
    "DaemonSet":                "https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/",
    "Job":                      "https://kubernetes.io/docs/concepts/workloads/controllers/job/",
    "CronJob":                  "https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/",
    "ReplicaSet":               "https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/",
    "Pod":                      "https://kubernetes.io/docs/concepts/workloads/pods/",
    "PodSpec":                  "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#PodSpec",
    "Container":                "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#Container",
    "ContainerPort":            "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#ContainerPort",
    "Service":                  "https://kubernetes.io/docs/concepts/services-networking/service/",
    "Ingress":                  "https://kubernetes.io/docs/concepts/services-networking/ingress/",
    "NetworkPolicy":            "https://kubernetes.io/docs/concepts/services-networking/network-policies/",
    "PersistentVolume":         "https://kubernetes.io/docs/concepts/storage/persistent-volumes/",
    "PersistentVolumeClaim":    "https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims",
    "StorageClass":             "https://kubernetes.io/docs/concepts/storage/storage-classes/",
    "Volume":                   "https://kubernetes.io/docs/concepts/storage/volumes/",
    "ConfigMap":                "https://kubernetes.io/docs/concepts/configuration/configmap/",
    "Secret":                   "https://kubernetes.io/docs/concepts/configuration/secret/",
    "ServiceAccount":           "https://kubernetes.io/docs/concepts/security/service-accounts/",
    "Role":                     "https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole",
    "ClusterRole":              "https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole",
    "RoleBinding":              "https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding",
    "ClusterRoleBinding":       "https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding",
    "HorizontalPodAutoscaler":  "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/",
    "ResourceQuota":            "https://kubernetes.io/docs/concepts/policy/resource-quotas/",
    "Namespace":                "https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/",
    "Node":                     "https://kubernetes.io/docs/concepts/architecture/nodes/",
}

_API_REF_BASE = "https://kubernetes.io/docs/reference/kubernetes-api/"
_API_GROUP = {
    "rbac":        "authorization-resources/",
    "networking":  "service-resources/",
    "storage":     "config-and-storage-resources/",
    "batch":       "workload-resources/",
    "autoscaling": "workload-resources/",
}

def _api_ref(fqn: str) -> str:
    for key, path in _API_GROUP.items():
        if key in fqn:
            return _API_REF_BASE + path
    return _API_REF_BASE + "workload-resources/"

def _source_ref(fixture: dict) -> str:
    fqn  = fixture.get("resource", "")
    kind = fqn.split(".")[-1] if fqn else ""
    if fixture.get("type") == "realworld":
        so_id = fixture.get("so_question_id", "")
        if so_id:
            return f"https://stackoverflow.com/questions/{so_id}"
    return _K8S_DOCS.get(kind, _API_REF_BASE)


# ── 2. SO metadata extraction ─────────────────────────────────────────────────
_SO_SCORE_RE = re.compile(r"SO (?:answer )?score\s+(\d+)", re.IGNORECASE)
_SO_VOTES_RE = re.compile(r"(\d+)\s+(?:up)?votes?", re.IGNORECASE)

def _extract_so_score(fixture: dict) -> int | None:
    """Extract SO answer score from selection_rationale text."""
    rationale = fixture.get("selection_rationale", "")
    m = _SO_SCORE_RE.search(rationale)
    return int(m.group(1)) if m else None


# ── 3. YAML ground truth validation ──────────────────────────────────────────
def _validate_yaml_gt(fixture: dict) -> dict:
    """Validate YAML in ground_truth.answer (yaml_gen and realworld with YAML)."""
    result = {"syntactic": None, "schema": None, "error": ""}
    answer = fixture.get("ground_truth", {}).get("answer", "")
    if "apiVersion:" not in answer:
        return result

    import yaml
    try:
        data = yaml.safe_load(answer)
        result["syntactic"] = True
    except Exception as e:
        result["syntactic"] = False
        result["error"] = str(e)[:120]
        return result

    try:
        import kubernetes_validate
        if isinstance(data, dict):
            kubernetes_validate.validate(data, "1.29", strict=False)
            result["schema"] = True
        else:
            result["schema"] = False
    except ImportError:
        result["schema"] = None  # library not installed
    except Exception as e:
        result["schema"] = False
        result["error"] = str(e)[:120]

    return result


# ── 4. Traceability domain mapping ────────────────────────────────────────────
_DOMAIN = {
    "Deployment": "Workload",   "StatefulSet": "Workload",
    "DaemonSet":  "Workload",   "Job":         "Workload",
    "CronJob":    "Workload",   "ReplicaSet":  "Workload",
    "Pod":        "Workload",   "PodSpec":     "Workload",
    "Container":  "Workload",   "ContainerPort": "Workload",
    "Service":    "Networking", "Ingress":     "Networking",
    "NetworkPolicy": "Networking",
    "ConfigMap":  "Configuration", "Secret":  "Configuration",
    "PersistentVolume": "Storage", "PersistentVolumeClaim": "Storage",
    "StorageClass": "Storage",  "Volume":     "Storage",
    "ServiceAccount": "Access Control", "Role": "Access Control",
    "ClusterRole": "Access Control",    "RoleBinding": "Access Control",
    "ClusterRoleBinding": "Access Control",
    "HorizontalPodAutoscaler": "Autoscaling",
    "ResourceQuota": "Policy",
    "Namespace":  "Cluster",    "Node": "Cluster",
}


# ── 5. Neo4j path validation (optional) ───────────────────────────────────────
_EDGE_RE = re.compile(r"^(.+?) -\[(.+?)\]-> (.+)$")

def _check_neo4j() -> object | None:
    """Return Neo4jClient if reachable, else None (no timeout hang)."""
    try:
        from src.graph.neo4j_client import Neo4jClient
        db = Neo4jClient()
        db.execute_query("RETURN 1", {})
        logger.info("[Neo4j] Connection OK — path validation enabled")
        return db
    except Exception as e:
        logger.warning(f"[Neo4j] Offline ({e.__class__.__name__}). Path validation skipped.")
        return None

def _validate_paths(fixture: dict, db) -> dict:
    """Returns {edge_str: True/False/None}. None = query error."""
    results = {}
    for edge_str in fixture.get("ground_truth", {}).get("expected_path", []):
        m = _EDGE_RE.match(edge_str.strip())
        if not m:
            results[edge_str] = None
            continue
        parent, rel, child = m.groups()
        try:
            rows = db.execute_query(
                "MATCH (a:Definition {name:$p})-[r]->(b:Definition {name:$c}) "
                "WHERE type(r)=$r RETURN count(r) AS cnt",
                {"p": parent, "c": child, "r": rel},
            )
            results[edge_str] = bool(rows and rows[0]["cnt"] > 0)
        except Exception:
            results[edge_str] = None
    return results


# ── Main ───────────────────────────────────────────────────────────────────────
def run(dry_run: bool = False, skip_neo4j: bool = False):
    db = None if skip_neo4j else _check_neo4j()

    all_fixtures = sorted(FIXTURES_DIR.rglob("*.json"))
    logger.info(f"Processing {len(all_fixtures)} fixtures...")

    traceability_rows = []
    path_rows         = []
    yaml_rows         = []
    updated_count     = 0

    for fpath in all_fixtures:
        fixture = json.loads(fpath.read_text(encoding="utf-8"))
        fid     = fixture.get("id", fpath.stem)
        ftype   = fixture.get("type", "")
        fqn     = fixture.get("resource", "")
        kind    = fqn.split(".")[-1] if fqn else ""

        changed = False

        # ── 1. source_reference & api_reference ──────────────────────────────
        src = _source_ref(fixture)
        api = _api_ref(fqn)
        if fixture.get("source_reference") != src:
            fixture["source_reference"] = src;  changed = True
        if fixture.get("api_reference") != api:
            fixture["api_reference"]    = api;  changed = True

        # ── 2. SO metadata ────────────────────────────────────────────────────
        if ftype == "realworld":
            so_id = fixture.get("so_question_id", "")
            so_url = f"https://stackoverflow.com/questions/{so_id}" if so_id else ""
            if fixture.get("so_url") != so_url and so_url:
                fixture["so_url"] = so_url;  changed = True
            score = _extract_so_score(fixture)
            if score is not None and fixture.get("so_answer_score") != score:
                fixture["so_answer_score"] = score;  changed = True

        # ── 3. YAML validation ────────────────────────────────────────────────
        yv = _validate_yaml_gt(fixture)
        if yv["syntactic"] is not None:
            yaml_rows.append({
                "fixture_id":    fid,
                "type":          ftype,
                "resource_kind": kind,
                "syntactic":     "PASS" if yv["syntactic"] else "FAIL",
                "schema":        ("PASS" if yv["schema"] else
                                  ("N/A"  if yv["schema"] is None else "FAIL")),
                "error":         yv["error"],
            })

        # ── 5. Path validation (Neo4j, optional) ─────────────────────────────
        path_results = {}
        if db is not None:
            path_results = _validate_paths(fixture, db)
            for edge_str, valid in path_results.items():
                status = ("VALID" if valid is True else
                          "NOT_IN_GRAPH" if valid is False else "UNKNOWN")
                path_rows.append({
                    "fixture_id": fid, "type": ftype,
                    "edge": edge_str, "status": status,
                })
        else:
            for edge_str in fixture.get("ground_truth", {}).get("expected_path", []):
                path_rows.append({
                    "fixture_id": fid, "type": ftype,
                    "edge": edge_str, "status": "PENDING_NEO4J",
                })

        # ── 4. Traceability row ───────────────────────────────────────────────
        n_paths   = len(path_rows) and len([r for r in path_rows if r["fixture_id"]==fid])
        ep        = fixture.get("ground_truth", {}).get("expected_path", [])
        traceability_rows.append({
            "fixture_id":      fid,
            "type":            ftype,
            "resource_kind":   kind,
            "domain":          _DOMAIN.get(kind, "Other"),
            "scope":           fixture.get("scope", ""),
            "multi_hop":       fixture.get("multi_hop", False),
            "source_reference": fixture.get("source_reference", ""),
            "api_reference":   fixture.get("api_reference", ""),
            "expected_paths":  len(ep),
            "yaml_syntactic":  yv.get("syntactic"),
            "yaml_schema":     yv.get("schema"),
            "so_question_id":  fixture.get("so_question_id", ""),
            "so_answer_score": fixture.get("so_answer_score", ""),
            "so_url":          fixture.get("so_url", ""),
            "gt_nodes_count":  len(fixture.get("ground_truth", {}).get("relevant_nodes", [])),
        })

        # ── Write updated fixture ─────────────────────────────────────────────
        if changed and not dry_run:
            fpath.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
            updated_count += 1

    # ── Write output files ─────────────────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not dry_run:
        def _write_csv(path, rows):
            if not rows: return
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)

        _write_csv(DATA_DIR / "traceability_matrix.csv",       traceability_rows)
        _write_csv(DATA_DIR / "fixture_validation_report.csv", path_rows)
        _write_csv(DATA_DIR / "yaml_gt_validation.csv",        yaml_rows)
        logger.info("CSV files saved to data/")

    # ── Summary ───────────────────────────────────────────────────────────────
    n_valid   = sum(1 for r in path_rows if r["status"] == "VALID")
    n_invalid = sum(1 for r in path_rows if r["status"] == "NOT_IN_GRAPH")
    n_pending = sum(1 for r in path_rows if r["status"] == "PENDING_NEO4J")

    yaml_syn_pass = sum(1 for r in yaml_rows if r["syntactic"] == "PASS")
    yaml_sch_pass = sum(1 for r in yaml_rows if r["schema"] == "PASS")

    domain_counts = Counter(r["domain"] for r in traceability_rows)
    type_counts   = Counter(r["type"]   for r in traceability_rows)

    W = 65
    lines = [
        "=" * W,
        "  DATASET VALIDITY SUMMARY",
        "=" * W,
        f"  Total fixtures          : {len(traceability_rows)}",
        f"  Fixtures updated        : {updated_count}",
        "",
        "  --- Expected Path Validation ---",
    ]
    if n_pending:
        lines.append(f"  PENDING (Neo4j offline) : {n_pending}  -- run again with Neo4j ON")
    else:
        n_total = len(path_rows)
        lines += [
            f"  Total edges checked     : {n_total}",
            f"  VALID (in graph)        : {n_valid}  ({n_valid/n_total*100:.1f}%)" if n_total else "  No edges",
            f"  NOT_IN_GRAPH            : {n_invalid}",
        ]
    lines += [
        "",
        "  --- YAML Ground Truth Validation ---",
        f"  Fixtures with YAML GT   : {len(yaml_rows)}",
        f"  Syntactic PASS          : {yaml_syn_pass}/{len(yaml_rows)}",
        f"  Schema    PASS          : {yaml_sch_pass}/{len(yaml_rows)}",
        "",
        "  --- Coverage by Fixture Type ---",
    ]
    for t, n in sorted(type_counts.items()):
        lines.append(f"    {t:<24}: {n:>3}")
    lines += ["", "  --- Coverage by K8s Domain ---"]
    for d, n in sorted(domain_counts.items()):
        lines.append(f"    {d:<24}: {n:>3}")
    lines.append("=" * W)

    summary = "\n".join(lines)
    print("\n" + summary)
    if not dry_run:
        (DATA_DIR / "dataset_validity_summary.txt").write_text(summary, encoding="utf-8")

    # ── Traceability matrix print ──────────────────────────────────────────────
    print()
    print("  TRACEABILITY MATRIX")
    print(f"  {'Fixture ID':<45} {'Type':<13} {'Domain':<16} {'Resource':<28} {'Paths':>5} {'Multi':>5} {'YAML':>6}")
    print(f"  {'-'*120}")
    for r in traceability_rows:
        yaml_s = ("SYN+SCH" if r["yaml_schema"] is True else
                  "SYN_OK"  if r["yaml_syntactic"] is True else
                  "FAIL"    if r["yaml_syntactic"] is False else
                  "-")
        print(
            f"  {r['fixture_id']:<45} {r['type']:<13} {r['domain']:<16}"
            f" {r['resource_kind']:<28} {r['expected_paths']:>5}"
            f" {str(r['multi_hop']):>5} {yaml_s:>6}"
        )

    if yaml_rows:
        print()
        print("  YAML GT VALIDATION DETAIL")
        print(f"  {'Fixture ID':<45} {'Type':<13} {'Syntactic':>9} {'Schema':>7} {'Error'}")
        print(f"  {'-'*110}")
        for r in yaml_rows:
            print(f"  {r['fixture_id']:<45} {r['type']:<13} {r['syntactic']:>9} {r['schema']:>7}  {r['error'][:50]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",    action="store_true")
    p.add_argument("--skip-neo4j", action="store_true")
    args = p.parse_args()
    run(dry_run=args.dry_run, skip_neo4j=args.skip_neo4j)
