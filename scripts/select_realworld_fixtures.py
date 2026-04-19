# scripts/select_realworld_fixtures.py
"""
Evaluation Dataset Selection Script - GraphRAG Kubernetes
=========================================================
Pulls questions from HuggingFace `mcipriano/stackoverflow-kubernetes-questions`,
applies the 4-gate + 5-dimension scoring framework, and writes accepted questions
as annotated fixture JSONs to tests/fixtures/realworld/.

Usage:
    python scripts/select_realworld_fixtures.py \\
        --max-candidates 5000 \\
        --target 20 \\
        --output tests/fixtures/realworld \\
        --report data/selection_report.csv \\
        --dry-run          # score & report without writing fixtures

Requirements (pip install):
    datasets>=2.14.0       # HuggingFace datasets
    neo4j>=5.17.0          # G2 node existence check (optional; skip with --skip-neo4j)

Gate summary (from design doc):
    G1 HARD - API spec answerable (keyword heuristic)
    G2 HARD - Primary resource exists in Neo4j graph
    G3 SOFT - No deprecated API (extensions/v1beta1, policy/v1beta1, etc.)
    G4 SOFT - Not a duplicate of existing synthesized fixtures (−0.30 penalty)

Scoring dimensions (1-3 each, weighted, max = 3.0):
    D1 (30%) - Graph answerability
    D2 (25%) - Path annotability
    D3 (20%) - Question type fit
    D4 (15%) - StackOverflow answer quality
    D5 (10%) - Real-world representativeness

Acceptance threshold: total_score >= 2.0
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

# -- Project root on path ------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Ensure stdout/stderr use UTF-8 on Windows (avoids emoji mangling in console)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# -- Paths ----------------------------------------------------------------------
FIXTURES_DIR    = Path(__file__).parent.parent / "tests" / "fixtures"
REALWORLD_DIR   = FIXTURES_DIR / "realworld"
DEFAULT_REPORT  = Path(__file__).parent.parent / "data" / "selection_report.csv"

# -- HuggingFace dataset config ------------------------------------------------
HF_DATASET_ID   = "mcipriano/stackoverflow-kubernetes-questions"
HF_SPLIT        = "train"

# -- Selection thresholds / quotas ---------------------------------------------
SCORE_ACCEPT    = 2.0
SCORE_REVIEW    = 1.8   # manual review band
DUPLICATE_PENALTY = 0.30
MAX_PER_TYPE    = 8     # max accepted fixtures per fixture-type bucket
MAX_PER_RESOURCE = 5    # max accepted fixtures per primary resource

# -- Scoring weights -----------------------------------------------------------
WEIGHTS = dict(d1=0.30, d2=0.25, d3=0.20, d4=0.15, d5=0.10)

# ════════════════════════════════════════════════════════════════════════════════
# G1 - API Spec Scope Test
# ════════════════════════════════════════════════════════════════════════════════

# Phrases that indicate purely operational / tool questions -> FAIL G1
# Kept tight: only patterns that are *never* relevant to the K8s API spec.
# Removed overly-broad terms (pending, setup, eks, gke, aks, not ready, helm)
# that appear in many legitimate API-spec questions.
_OPERATIONAL_SIGNALS = [
    r"\binstall(ing|ation)?\b", r"\bkops\b", r"\beksctl\b",
    r"\bterraform\b", r"\bansible\b", r"\bjenkins\b",
    r"\bcrashloop\b", r"\bimagepullback\b",
    r"\bnode\s+not\s+ready\b", r"\bevicted\b", r"\bkubectl\s+exec\b",
    r"\bport.forward\b", r"\bssh\b", r"\bloadbalancer\s+ip\b",
    r"\bminikube.*install\b",
    r"\bdocker\s+build\b", r"\bpush.*registry\b",
]
_OPERATIONAL_RE = re.compile("|".join(_OPERATIONAL_SIGNALS), re.IGNORECASE)

# Phrases that signal API-level content -> strengthens G1 PASS
_API_SIGNALS = [
    r"\bapiVersion\b", r"\bkind:\s*\w+", r"\bspec\b", r"\bmetadata\b",
    r"\bdeployment\b", r"\bstatefulset\b", r"\bservice\b", r"\bconfigmap\b",
    r"\bsecret\b", r"\bdaemonset\b", r"\bingress\b", r"\bnetworkpolicy\b",
    r"\bpersistentvolume\b", r"\bpersistentvolumeclaim\b", r"\bpvc\b",
    r"\bclusterrole\b", r"\brole\b", r"\bserviceaccount\b",
    r"\bjob\b", r"\bcronjob\b", r"\bhpa\b", r"\bresourcequota\b",
    r"\byaml\b", r"\bmanifest\b", r"\bcontainer\s+spec\b",
]
_API_RE = re.compile("|".join(_API_SIGNALS), re.IGNORECASE)


def gate1_api_scope(question: str, answer: str) -> bool:
    """Return True if the question is answerable from the K8s API spec.

    Logic:
      - Fail if no API signal found in question+answer (purely off-topic).
      - Fail if a purely operational signal is found in the question title
        (install, crashloop, kubectl exec, etc.) AND no API signal in question.
      - Pass when API signals dominate, even if operational context is present
        (e.g. "How do I configure spec.replicas in an EKS Deployment?").
    """
    combined = f"{question} {answer}"
    has_api = bool(_API_RE.search(combined))
    if not has_api:
        return False
    # Only reject when operational signals appear without any API signal in
    # the question itself (answer may salvage it via has_api above).
    if _OPERATIONAL_RE.search(question) and not _API_RE.search(question):
        return False
    return True


# ════════════════════════════════════════════════════════════════════════════════
# G2 - Neo4j Node Existence Test
# ════════════════════════════════════════════════════════════════════════════════

# Well-known core K8s resources (all ingested from swagger definitions).
# Used as a fast local fallback when --skip-neo4j is set.
_KNOWN_RESOURCES: set[str] = {
    "Deployment", "DeploymentSpec", "Pod", "PodSpec", "PodTemplateSpec",
    "Service", "ServiceSpec", "ConfigMap", "Secret",
    "StatefulSet", "StatefulSetSpec", "DaemonSet", "DaemonSetSpec",
    "Ingress", "IngressSpec", "NetworkPolicy", "NetworkPolicySpec",
    "PersistentVolume", "PersistentVolumeClaim", "PersistentVolumeClaimSpec",
    "Volume", "VolumeMount", "Container", "EnvVar", "EnvVarSource",
    "ResourceRequirements", "ResourceQuota", "LimitRange",
    "HorizontalPodAutoscaler", "HPA",
    "Job", "JobSpec", "CronJob", "CronJobSpec",
    "Role", "RoleBinding", "ClusterRole", "ClusterRoleBinding", "ServiceAccount",
    "StorageClass", "Endpoints", "ReplicaSet", "Namespace",
    "Node", "NodeSpec", "Affinity", "Toleration",
    "Probe", "ExecAction", "HTTPGetAction", "TCPSocketAction",
    "SecretKeySelector", "ConfigMapKeySelector",
    "VolumeMount", "ContainerPort",
}

# Regex patterns to extract resource names from question text
_RESOURCE_PATTERN = re.compile(
    r"\b(Deployment|StatefulSet|DaemonSet|Pod|Service|ConfigMap|Secret|"
    r"Ingress|NetworkPolicy|PersistentVolumeClaim|PersistentVolume|PVC|PV|"
    r"Job|CronJob|HPA|HorizontalPodAutoscaler|ResourceQuota|LimitRange|"
    r"Role|ClusterRole|RoleBinding|ClusterRoleBinding|ServiceAccount|"
    r"StorageClass|Namespace|ReplicaSet|Node|Affinity|Toleration)\b",
    re.IGNORECASE,
)


def extract_primary_resource(question: str, answer: str) -> Optional[str]:
    """Extract the primary Kubernetes resource from question/answer text."""
    matches = _RESOURCE_PATTERN.findall(question + " " + answer)
    if not matches:
        return None
    # Return the most frequently mentioned resource (title-cased)
    from collections import Counter
    counts = Counter(m.title() for m in matches)
    # Normalize PVC -> PersistentVolumeClaim, HPA -> HorizontalPodAutoscaler
    norm = {"Pvc": "PersistentVolumeClaim", "Pv": "PersistentVolume", "Hpa": "HorizontalPodAutoscaler"}
    resource = counts.most_common(1)[0][0]
    return norm.get(resource, resource)


def gate2_node_exists(resource: Optional[str], neo4j_client=None) -> bool:
    """Return True if the resource exists in the Neo4j graph."""
    if resource is None:
        return False
    # Fast local check
    if resource in _KNOWN_RESOURCES or resource.rstrip("s") in _KNOWN_RESOURCES:
        return True
    # Optional live Neo4j check
    if neo4j_client:
        try:
            result = neo4j_client.execute_query(
                "MATCH (d:Definition) WHERE d.name CONTAINS $name RETURN d.name LIMIT 1",
                {"name": resource},
            )
            return bool(result)
        except Exception:
            pass
    return False


# ════════════════════════════════════════════════════════════════════════════════
# G3 - Deprecation & Stability Test (SOFT)
# ════════════════════════════════════════════════════════════════════════════════

_DEPRECATED_APIS = re.compile(
    r"extensions/v1beta1|apps/v1beta[12]|policy/v1beta1|"
    r"networking\.k8s\.io/v1beta1|apiextensions\.k8s\.io/v1beta1|"
    r"rbac\.authorization\.k8s\.io/v1alpha1|batch/v1beta1",
    re.IGNORECASE,
)
_STABLE_VERSIONS = re.compile(
    r"apps/v1|core/v1|networking\.k8s\.io/v1|batch/v1|rbac\.authorization\.k8s\.io/v1",
    re.IGNORECASE,
)


def gate3_deprecation(question: str, answer: str) -> bool:
    """Return True (PASS) if no deprecated APIs are referenced."""
    combined = f"{question} {answer}"
    if _DEPRECATED_APIS.search(combined):
        return False
    return True


# ════════════════════════════════════════════════════════════════════════════════
# G4 - Complementarity Test (SOFT)
# ════════════════════════════════════════════════════════════════════════════════

def _build_coverage_tracker() -> dict[tuple[str, str], bool]:
    """
    Load existing synthesized fixtures (41 + realworld) and record which
    (resource, fixture_type) pairs are already covered.
    """
    covered: dict[tuple[str, str], bool] = {}
    for path in FIXTURES_DIR.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            resource_full = data.get("resource", "")
            resource_short = resource_full.split(".")[-1] if "." in resource_full else resource_full
            ftype = data.get("type", "")
            covered[(resource_short, ftype)] = True
        except Exception:
            continue
    return covered


def gate4_complementarity(resource: str, fixture_type: str, coverage: dict) -> bool:
    """Return True (new coverage) if this (resource, type) pair is NOT yet covered."""
    return not coverage.get((resource, fixture_type), False)


# ════════════════════════════════════════════════════════════════════════════════
# 5-Dimension Scoring
# ════════════════════════════════════════════════════════════════════════════════

def _score_d1_graph_answerability(question: str, answer: str, resource: str) -> int:
    """D1 (30%): How completely can the graph answer this?"""
    combined = f"{question} {answer}"
    # Count API signals (more = more graph-answerable)
    api_hits = len(_API_RE.findall(combined))
    operational_hits = len(_OPERATIONAL_RE.findall(combined))
    # YAML / field-level discussion is a strong indicator of graph-answerability
    has_yaml = bool(re.search(r"apiVersion|kind:|spec:|metadata:", combined, re.IGNORECASE))
    if has_yaml and api_hits >= 4 and operational_hits == 0:
        return 3
    if api_hits >= 2 and operational_hits <= 1:
        return 2
    return 1


def _score_d2_path_annotability(question: str, answer: str) -> int:
    """D2 (25%): Can we write a precise expected_path?"""
    # Multi-resource questions mentioning relationships are harder to annotate
    resource_count = len(set(_RESOURCE_PATTERN.findall(question + " " + answer)))
    relation_words = re.findall(
        r"\b(relation|connect|link|between|manage|control|select|bind|mount|claim)\b",
        question + " " + answer,
        re.IGNORECASE,
    )
    yaml_fields = re.findall(r"\b\w+\.\w+\b", answer)  # dotted field references like spec.replicas
    if resource_count <= 2 and yaml_fields:
        return 3
    if resource_count <= 3 or relation_words:
        return 2
    return 1


def _score_d3_type_fit(question: str, answer: str) -> tuple[int, str]:
    """D3 (20%): Does it fit cleanly into one fixture type? Returns (score, type)."""
    q_lower = question.lower()
    a_lower = answer.lower()
    # yaml_gen: explicit request to create/write YAML
    if re.search(r"\b(create|write|generate|show|example)\s+(a|the|an)?\s*yaml\b", q_lower, re.IGNORECASE) \
            or re.search(r"apiVersion:", answer):
        return 3, "yaml_gen"
    # relationship: "what is the relationship / how does X relate to Y"
    if re.search(r"\b(relation|between|connect|link|how does .+ work with)\b", q_lower, re.IGNORECASE):
        return 3, "relationship"
    # conceptual: "what is / explain / difference between"
    if re.search(r"\b(what is|explain|difference between|when (should|to) use)\b", q_lower, re.IGNORECASE):
        return 3, "conceptual"
    # followup: context-dependent ("now add / also configure / additionally")
    if re.search(r"\b(also|additionally|now|next|furthermore)\b", q_lower, re.IGNORECASE):
        return 2, "followup"
    return 2, "conceptual"   # default: conceptual with minor adaptation


def _score_d4_so_quality(answer_score: int, question: str) -> int:
    """D4 (15%): StackOverflow community quality signal."""
    if answer_score >= 20:
        return 3
    if answer_score >= 5:
        return 2
    return 1


def _score_d5_representativeness(question: str) -> int:
    """D5 (10%): Is this a generic, environment-agnostic question?"""
    env_specific = re.compile(
        r"\bmy\s+(cluster|setup|env|project|company)\b|"
        r"\b(GKE|EKS|AKS|Rancher|OpenShift|on.?prem)\b|"
        r"\bspecific\s+to\b|\bonly\s+(in|for)\b",
        re.IGNORECASE,
    )
    if env_specific.search(question):
        return 1
    if re.search(r"\b(any|general|standard|how (do|to|can))\b", question, re.IGNORECASE):
        return 3
    return 2


def score_candidate(row: dict, coverage: dict) -> dict:
    """
    Apply all gates and 5-dimension scoring to a single StackOverflow row.

    Returns a result dict with 'status' in:
        'discard_g1', 'discard_g2', 'discard_g3', 'discard_score', 'reserve', 'accept', 'review'
    """
    # Dataset fields: 'Question', 'Answer', 'QuestionAuthor', 'AnswerAuthor'
    question = str(row.get("Question", "") or "").strip()
    answer   = str(row.get("Answer", "") or "").strip()
    so_score = 0   # dataset has no answer score field
    so_id    = str(row.get("QuestionAuthor", "unknown"))

    result = {
        "so_question_id": so_id,
        "question_raw":   question[:200],
        "answer_raw":     answer[:200],
        "so_answer_score": so_score,
        "status": "pending",
        "total_score": 0.0,
        "resource": None,
        "fixture_type": "conceptual",
        "penalty": 0.0,
        "d1": 0, "d2": 0, "d3": 0, "d4": 0, "d5": 0,
        "g3_pass": True, "g4_new": True,
    }

    # -- HARD GATES ------------------------------------------------------------
    if not gate1_api_scope(question, answer):
        result["status"] = "discard_g1"
        return result

    resource = extract_primary_resource(question, answer)
    result["resource"] = resource
    if not gate2_node_exists(resource):
        result["status"] = "discard_g2"
        return result

    # -- SOFT GATES ------------------------------------------------------------
    g3_pass = gate3_deprecation(question, answer)
    result["g3_pass"] = g3_pass
    if not g3_pass:
        result["status"] = "discard_g3"
        return result

    # Map to fixture type before G4 check
    d3_score, fixture_type = _score_d3_type_fit(question, answer)
    result["fixture_type"] = fixture_type

    g4_new = gate4_complementarity(resource, fixture_type, coverage)
    result["g4_new"] = g4_new
    penalty = 0.0 if g4_new else DUPLICATE_PENALTY

    # -- SCORING ---------------------------------------------------------------
    d1 = _score_d1_graph_answerability(question, answer, resource)
    d2 = _score_d2_path_annotability(question, answer)
    d4 = _score_d4_so_quality(so_score, question)
    d5 = _score_d5_representativeness(question)

    total = (
        d1 * WEIGHTS["d1"]
        + d2 * WEIGHTS["d2"]
        + d3_score * WEIGHTS["d3"]
        + d4 * WEIGHTS["d4"]
        + d5 * WEIGHTS["d5"]
        - penalty
    )

    result.update({
        "d1": d1, "d2": d2, "d3": d3_score, "d4": d4, "d5": d5,
        "penalty": penalty, "total_score": round(total, 4),
    })

    if total >= SCORE_ACCEPT:
        result["status"] = "accept"
    elif total >= SCORE_REVIEW:
        result["status"] = "review"
    else:
        result["status"] = "discard_score"

    return result


# ════════════════════════════════════════════════════════════════════════════════
# Diversity-aware selection (coverage quota enforcement)
# ════════════════════════════════════════════════════════════════════════════════

def select_with_diversity(scored: list[dict], target: int) -> list[dict]:
    """
    From all 'accept' candidates, select up to `target` using diversity quotas.
    Priority: fill uncovered (resource, type) pairs first, then sort by score.
    """
    # Pre-load existing coverage
    coverage = _build_coverage_tracker()

    candidates = sorted(
        [r for r in scored if r["status"] == "accept"],
        key=lambda x: (
            # Coverage of a "needed" slot -> highest priority
            not coverage.get((x["resource"], x["fixture_type"]), False),
            x["total_score"],
        ),
        reverse=True,
    )

    selected = []
    type_counts: defaultdict[str, int] = defaultdict(int)
    resource_counts: defaultdict[str, int] = defaultdict(int)

    for c in candidates:
        if len(selected) >= target:
            break
        ftype    = c["fixture_type"]
        resource = c["resource"] or "Unknown"
        if type_counts[ftype] >= MAX_PER_TYPE:
            continue
        if resource_counts[resource] >= MAX_PER_RESOURCE:
            continue
        selected.append(c)
        type_counts[ftype]    += 1
        resource_counts[resource] += 1
        # Mark as now-covered for subsequent iterations
        coverage[(resource, ftype)] = True

    return selected


# ════════════════════════════════════════════════════════════════════════════════
# Fixture writer
# ════════════════════════════════════════════════════════════════════════════════

def _build_fixture_id(question_raw: str, so_id: str) -> str:
    """Create a safe, snake_case fixture ID from the SO question title."""
    words = re.sub(r"[^a-z0-9\s]", "", question_raw[:60].lower()).split()
    slug  = "_".join(words[:6]) or f"q{so_id}"
    return slug


def _translate_question(question: str) -> str:
    """
    Placeholder: in production, call an LLM to translate question to Indonesian.
    Here we return the raw English question; replace with LLM call if needed.
    """
    return question.strip()[:300]


def write_fixture(candidate: dict, output_dir: Path) -> Path:
    """Write a selected candidate as a realworld fixture JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_id = _build_fixture_id(candidate["question_raw"], candidate["so_question_id"])

    # Avoid overwriting existing file
    path = output_dir / f"{fixture_id}.json"
    counter = 1
    while path.exists():
        path = output_dir / f"{fixture_id}_{counter}.json"
        counter += 1

    resource = candidate["resource"] or "Unknown"
    # Map short resource name to full Swagger definition name
    _RESOURCE_FULL = {
        "Deployment": "io.k8s.api.apps.v1.Deployment",
        "Pod": "io.k8s.api.core.v1.Pod",
        "Service": "io.k8s.api.core.v1.Service",
        "ConfigMap": "io.k8s.api.core.v1.ConfigMap",
        "Secret": "io.k8s.api.core.v1.Secret",
        "StatefulSet": "io.k8s.api.apps.v1.StatefulSet",
        "DaemonSet": "io.k8s.api.apps.v1.DaemonSet",
        "Ingress": "io.k8s.api.networking.v1.Ingress",
        "NetworkPolicy": "io.k8s.api.networking.v1.NetworkPolicy",
        "PersistentVolumeClaim": "io.k8s.api.core.v1.PersistentVolumeClaim",
        "PersistentVolume": "io.k8s.api.core.v1.PersistentVolume",
        "Job": "io.k8s.api.batch.v1.Job",
        "CronJob": "io.k8s.api.batch.v1.CronJob",
        "HorizontalPodAutoscaler": "io.k8s.api.autoscaling.v1.HorizontalPodAutoscaler",
        "ResourceQuota": "io.k8s.api.core.v1.ResourceQuota",
        "Role": "io.k8s.api.rbac.v1.Role",
        "ClusterRole": "io.k8s.api.rbac.v1.ClusterRole",
        "RoleBinding": "io.k8s.api.rbac.v1.RoleBinding",
        "ClusterRoleBinding": "io.k8s.api.rbac.v1.ClusterRoleBinding",
        "ServiceAccount": "io.k8s.api.core.v1.ServiceAccount",
    }
    resource_full = _RESOURCE_FULL.get(resource, f"io.k8s.api.core.v1.{resource}")
    scope = "Cluster" if resource in ("ClusterRole", "ClusterRoleBinding", "Node", "StorageClass", "PersistentVolume", "Namespace") else "Namespaced"

    fixture = {
        "id": fixture_id,
        "type": "realworld",
        "question": _translate_question(candidate["question_raw"]),
        "resource": resource_full,
        "scope": scope,
        "multi_hop": candidate["d2"] >= 2,  # multi-hop if path annotation is non-trivial
        # -- Selection metadata ------------------------------------------------
        "so_question_id": candidate["so_question_id"],
        "selection_score": candidate["total_score"],
        "selection_scores_breakdown": {
            "d1_graph_answerability": candidate["d1"],
            "d2_path_annotability":  candidate["d2"],
            "d3_type_fit":           candidate["d3"],
            "d4_so_quality":         candidate["d4"],
            "d5_representativeness": candidate["d5"],
            "g4_penalty":            -candidate["penalty"],
        },
        "selection_rationale": (
            f"SO answer score {candidate['so_answer_score']}. "
            f"D1={candidate['d1']} D2={candidate['d2']} D3={candidate['d3']} "
            f"D4={candidate['d4']} D5={candidate['d5']}. "
            f"G4 {'new coverage' if candidate['g4_new'] else 'duplicate (-0.30)'}."
        ),
        # -- Standard fixture fields (to be annotated manually or by LLM) -----
        "ground_truth": {
            "answer": candidate["answer_raw"][:500],
            "context": [],
            "relevant_nodes": [resource_full],
            "expected_path": [],
            "required_fields": [],
            "expected_yaml_keys": [],
        },
    }

    path.write_text(json.dumps(fixture, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ════════════════════════════════════════════════════════════════════════════════
# Report writer
# ════════════════════════════════════════════════════════════════════════════════

def write_report(all_scored: list[dict], selected: list[dict], report_path: Path) -> None:
    """Write full scoring CSV and selection summary."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "so_question_id", "so_answer_score", "status", "total_score",
        "resource", "fixture_type", "penalty", "d1", "d2", "d3", "d4", "d5",
        "g3_pass", "g4_new", "question_raw",
    ]
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_scored)

    # Summary to stdout
    counts = defaultdict(int)
    for r in all_scored:
        counts[r["status"]] += 1
    print("\n" + "=" * 60)
    print(f"  Selection Report - {len(all_scored)} candidates processed")
    print("=" * 60)
    print(f"  Discarded (G1 scope)   : {counts['discard_g1']:4d}")
    print(f"  Discarded (G2 no node) : {counts['discard_g2']:4d}")
    print(f"  Discarded (G3 deprec.) : {counts['discard_g3']:4d}")
    print(f"  Discarded (low score)  : {counts['discard_score']:4d}")
    print(f"  Manual review (1.8-2.0): {counts['review']:4d}")
    print(f"  Accepted candidates    : {counts['accept']:4d}")
    print(f"  ---------------------------------------------")
    print(f"  Selected (diversity)   : {len(selected):4d}")
    print(f"\n  Full report -> {report_path}")


# ════════════════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════════════════

def run_selection(
    max_candidates: int = 5000,
    target: int = 20,
    output_dir: Path = REALWORLD_DIR,
    report_path: Path = DEFAULT_REPORT,
    dry_run: bool = False,
    skip_neo4j: bool = True,
) -> list[dict]:
    """
    Full pipeline:
      1. Load HuggingFace dataset
      2. Apply gates + scoring to up to max_candidates rows
      3. Select diversity-balanced subset
      4. Write fixtures (unless dry_run)
      5. Write CSV report
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error(
            "HuggingFace `datasets` package not found.\n"
            "Install with: pip install datasets"
        )
        sys.exit(1)

    logger.info(f"Loading dataset {HF_DATASET_ID} (split={HF_SPLIT}, max={max_candidates}) …")
    try:
        ds = load_dataset(HF_DATASET_ID, split=HF_SPLIT)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Pre-load coverage tracker once (avoids re-reading fixtures per candidate)
    coverage = _build_coverage_tracker()
    logger.info(f"Existing fixture pairs in coverage tracker: {len(coverage)}")

    neo4j_client = None
    if not skip_neo4j:
        try:
            from src.graph.neo4j_client import Neo4jClient
            neo4j_client = Neo4jClient()
            logger.info("Neo4j client connected for G2 node checks.")
        except Exception as e:
            logger.warning(f"Neo4j unavailable - using local resource list only: {e}")

    all_scored: list[dict] = []
    for i, row in enumerate(ds):
        if i >= max_candidates:
            break
        result = score_candidate(row, coverage)
        all_scored.append(result)
        if i % 500 == 0:
            logger.info(f"  Processed {i:5d}/{max_candidates} …")

    selected = select_with_diversity(all_scored, target=target)

    if not dry_run:
        logger.info(f"Writing {len(selected)} fixture(s) to {output_dir} …")
        for c in selected:
            path = write_fixture(c, output_dir)
            logger.info(f"  ✓ {path.name}  (score={c['total_score']}, type={c['fixture_type']}, resource={c['resource']})")

    write_report(all_scored, selected, report_path)
    return selected


def main():
    parser = argparse.ArgumentParser(
        description="Select real-world evaluation fixtures from StackOverflow K8s dataset"
    )
    parser.add_argument("--max-candidates", type=int, default=5000,
                        help="Max SO rows to evaluate (default: 5000)")
    parser.add_argument("--target", type=int, default=20,
                        help="Target number of selected fixtures (default: 20)")
    parser.add_argument("--output", type=Path, default=REALWORLD_DIR,
                        help=f"Output directory for fixture JSONs (default: {REALWORLD_DIR})")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT,
                        help=f"Path for CSV selection report (default: {DEFAULT_REPORT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Score & report without writing fixture files")
    parser.add_argument("--skip-neo4j", action="store_true", default=True,
                        help="Use local resource list instead of live Neo4j for G2 (default: True)")
    args = parser.parse_args()

    run_selection(
        max_candidates=args.max_candidates,
        target=args.target,
        output_dir=args.output,
        report_path=args.report,
        dry_run=args.dry_run,
        skip_neo4j=args.skip_neo4j,
    )


if __name__ == "__main__":
    main()
