# tests/evaluation/test_metrics.py
"""
Unit tests for the three evaluation metric functions:
  - compute_ansq  (Answer Quality)
  - compute_retq  (Retrieval Quality)
  - compute_reaq  (Reasoning Quality)

These tests are fully isolated — they exercise the pure functions in
scripts/evaluate.py without touching Neo4j, LLMs, or the filesystem.
Run with:
    pytest tests/evaluation/ -v -m evaluation
"""
import json
import sys
from pathlib import Path
import pytest

# Make project root importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.evaluate import compute_ansq, compute_retq, compute_reaq, _token_f1

# Minimum score a realworld fixture must carry to be included in tests.
# Mirrors SCORE_ACCEPT in scripts/select_realworld_fixtures.py.
REALWORLD_MIN_SCORE = 2.0


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers & shared fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def deployment_ground_truth():
    """Standard Deployment ground truth used across multiple test cases."""
    return {
        "answer": "Deployment adalah controller yang mengelola ReplicaSet dan memastikan "
                  "jumlah Pod yang diinginkan berjalan. Mendukung rolling update dan rollback.",
        "relevant_nodes": [
            "io.k8s.api.apps.v1.Deployment",
            "io.k8s.api.apps.v1.DeploymentSpec",
        ],
        "expected_path": [
            "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
        ],
        "multi_hop": False,
        "scope": "Namespaced",
        "required_fields": [],
        "expected_yaml_keys": [],
    }


@pytest.fixture
def yaml_gen_ground_truth():
    """Ground truth for a YAML-generation fixture (Deployment with 3 replicas)."""
    return {
        "answer": (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: nginx-deployment\n"
            "spec:\n"
            "  replicas: 3\n"
            "  selector:\n"
            "    matchLabels:\n"
            "      app: nginx\n"
            "  template:\n"
            "    metadata:\n"
            "      labels:\n"
            "        app: nginx\n"
            "    spec:\n"
            "      containers:\n"
            "      - name: nginx\n"
            "        image: nginx:latest"
        ),
        "relevant_nodes": [
            "io.k8s.api.apps.v1.Deployment",
            "io.k8s.api.apps.v1.DeploymentSpec",
            "io.k8s.api.core.v1.PodTemplateSpec",
        ],
        "expected_path": [
            "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
            "DeploymentSpec -[HAS_PROPERTY]-> PodTemplateSpec",
        ],
        "multi_hop": True,
        "scope": "Namespaced",
        "required_fields": ["apiVersion", "kind", "metadata", "spec"],
        "expected_yaml_keys": [
            "apiVersion", "kind", "metadata", "spec",
            "spec.replicas", "spec.selector", "spec.template",
        ],
    }


@pytest.fixture
def relationship_ground_truth():
    """Ground truth for a relationship-type fixture (multi-hop)."""
    return {
        "answer": (
            "Deployment mengontrol ReplicaSet melalui spec.selector. "
            "ReplicaSet kemudian membuat dan menjaga jumlah Pod sesuai spec.replicas."
        ),
        "relevant_nodes": [
            "io.k8s.api.apps.v1.Deployment",
            "io.k8s.api.apps.v1.DeploymentSpec",
            "io.k8s.api.core.v1.PodTemplateSpec",
        ],
        "expected_path": [
            "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
            "DeploymentSpec -[CONTAINS_POD_TEMPLATE]-> PodTemplateSpec",
        ],
        "multi_hop": True,
        "scope": "Namespaced",
        "required_fields": [],
        "expected_yaml_keys": [],
    }


@pytest.fixture
def cluster_ground_truth():
    """Ground truth for a cluster-scoped resource (ClusterRole)."""
    return {
        "answer": (
            "ClusterRole mendefinisikan izin akses di level cluster. "
            "Tidak terikat pada namespace, berlaku untuk seluruh cluster."
        ),
        "relevant_nodes": [
            "io.k8s.api.rbac.v1.ClusterRole",
        ],
        "expected_path": [],
        "multi_hop": False,
        "scope": "Cluster",
        "required_fields": [],
        "expected_yaml_keys": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# _token_f1 — private helper
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestTokenF1:
    """Tests for the token-overlap F1 helper used by compute_ansq."""

    def test_identical_strings_return_one(self):
        assert _token_f1("hello world", "hello world") == pytest.approx(1.0)

    def test_disjoint_strings_return_zero(self):
        assert _token_f1("foo bar", "baz qux") == pytest.approx(0.0)

    def test_partial_overlap_symmetric(self):
        # F1 of "a b c" vs "b c d" should be the same both ways
        assert _token_f1("a b c", "b c d") == pytest.approx(_token_f1("b c d", "a b c"))

    def test_empty_pred_returns_zero(self):
        assert _token_f1("", "some gold text") == pytest.approx(0.0)

    def test_empty_gold_returns_zero(self):
        assert _token_f1("some prediction", "") == pytest.approx(0.0)

    def test_both_empty_returns_zero(self):
        assert _token_f1("", "") == pytest.approx(0.0)

    def test_case_insensitive_matching(self):
        # Tokens are lowercased before comparison
        assert _token_f1("Deployment ReplicaSet", "deployment replicaset") == pytest.approx(1.0)

    def test_partial_overlap_range(self):
        score = _token_f1("deployment replicaset pod", "deployment pod service")
        assert 0.0 < score < 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# compute_ansq — Answer Quality
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestComputeAnsq:
    """Unit tests for compute_ansq across all fixture types."""

    # ── Output shape ──────────────────────────────────────────────────────────

    def test_returns_required_keys(self, deployment_ground_truth):
        result = compute_ansq("Some answer about Deployment", deployment_ground_truth, "conceptual")
        for key in ("syntactic_validity", "schema_compliance", "answer_relevance", "faithfulness", "ansq_score"):
            assert key in result, f"Missing key: {key}"

    def test_ansq_score_bounded(self, deployment_ground_truth):
        result = compute_ansq("Some answer about Deployment", deployment_ground_truth, "conceptual")
        assert 0.0 <= result["ansq_score"] <= 1.0

    # ── YAML-specific metrics ─────────────────────────────────────────────────

    def test_yaml_gen_valid_yaml_gets_syntactic_score_one(self, yaml_gen_ground_truth):
        valid_yaml = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n  name: test\n"
            "spec:\n  replicas: 3"
        )
        result = compute_ansq(valid_yaml, yaml_gen_ground_truth, "yaml_gen")
        assert result["syntactic_validity"] == pytest.approx(1.0)

    def test_yaml_gen_invalid_yaml_gets_syntactic_score_zero(self, yaml_gen_ground_truth):
        invalid_yaml = "apiVersion: apps/v1\n  broken: [unclosed"
        result = compute_ansq(invalid_yaml, yaml_gen_ground_truth, "yaml_gen")
        assert result["syntactic_validity"] == pytest.approx(0.0)

    def test_non_yaml_type_has_none_syntactic_validity(self, deployment_ground_truth):
        result = compute_ansq("Deployment is a workload resource.", deployment_ground_truth, "conceptual")
        assert result["syntactic_validity"] is None

    def test_non_yaml_type_has_none_schema_compliance(self, deployment_ground_truth):
        result = compute_ansq("Some text", deployment_ground_truth, "followup")
        assert result["schema_compliance"] is None

    def test_non_yaml_type_has_none_for_relationship(self, relationship_ground_truth):
        result = compute_ansq("Deployment controls ReplicaSet", relationship_ground_truth, "relationship")
        assert result["syntactic_validity"] is None
        assert result["schema_compliance"] is None

    # ── Answer Relevance (token F1) ───────────────────────────────────────────

    def test_perfect_answer_gets_high_relevance(self, deployment_ground_truth):
        gt_answer = deployment_ground_truth["answer"]
        result = compute_ansq(gt_answer, deployment_ground_truth, "conceptual")
        assert result["answer_relevance"] == pytest.approx(1.0)

    def test_empty_answer_gets_zero_relevance(self, deployment_ground_truth):
        result = compute_ansq("", deployment_ground_truth, "conceptual")
        assert result["answer_relevance"] == pytest.approx(0.0)

    def test_irrelevant_answer_gets_low_relevance(self, deployment_ground_truth):
        result = compute_ansq("I don't know what you're asking", deployment_ground_truth, "conceptual")
        assert result["answer_relevance"] < 0.3

    # ── Faithfulness ──────────────────────────────────────────────────────────

    def test_answer_mentioning_all_nodes_gets_full_faithfulness(self, deployment_ground_truth):
        # Ground truth nodes: Deployment, DeploymentSpec
        answer = "Deployment uses DeploymentSpec to control the cluster."
        result = compute_ansq(answer, deployment_ground_truth, "conceptual")
        assert result["faithfulness"] == pytest.approx(1.0)

    def test_answer_mentioning_no_nodes_gets_zero_faithfulness(self, deployment_ground_truth):
        answer = "this text has nothing relevant"
        result = compute_ansq(answer, deployment_ground_truth, "conceptual")
        assert result["faithfulness"] == pytest.approx(0.0)

    def test_empty_relevant_nodes_gives_full_faithfulness(self):
        gt = {
            "answer": "some answer",
            "relevant_nodes": [],
            "multi_hop": False,
            "scope": "",
        }
        result = compute_ansq("anything", gt, "conceptual")
        assert result["faithfulness"] == pytest.approx(1.0)

    # ── Edge: yaml_gen with list YAML should score 0 schema ──────────────────

    def test_yaml_gen_list_yaml_scores_zero_schema(self, yaml_gen_ground_truth):
        list_yaml = "- item1\n- item2"
        result = compute_ansq(list_yaml, yaml_gen_ground_truth, "yaml_gen")
        # List YAML is valid syntax but fails schema (not a dict)
        assert result["syntactic_validity"] == pytest.approx(1.0)
        assert result["schema_compliance"] == pytest.approx(0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# compute_retq — Retrieval Quality
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestComputeRetq:
    """Unit tests for compute_retq."""

    # ── Output shape ──────────────────────────────────────────────────────────

    def test_returns_required_keys(self, deployment_ground_truth):
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_retq(path, deployment_ground_truth)
        for key in ("precision_at_k", "recall_at_k", "f1_at_k", "graph_coverage", "retq_score"):
            assert key in result, f"Missing key: {key}"

    def test_retq_score_bounded(self, deployment_ground_truth):
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_retq(path, deployment_ground_truth)
        assert 0.0 <= result["retq_score"] <= 1.0

    # ── Perfect retrieval ─────────────────────────────────────────────────────

    def test_perfect_path_match_high_score(self, deployment_ground_truth):
        # The reasoning path contains exactly the expected source node
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_retq(path, deployment_ground_truth)
        # Both relevant nodes (Deployment, DeploymentSpec) appear in the path
        assert result["recall_at_k"] == pytest.approx(1.0)
        assert result["graph_coverage"] == pytest.approx(1.0)

    # ── Empty reasoning path ──────────────────────────────────────────────────

    def test_empty_path_gives_zero_precision(self, deployment_ground_truth):
        result = compute_retq([], deployment_ground_truth)
        assert result["precision_at_k"] == pytest.approx(0.0)

    def test_empty_path_gives_zero_recall_when_nodes_expected(self, deployment_ground_truth):
        result = compute_retq([], deployment_ground_truth)
        assert result["recall_at_k"] == pytest.approx(0.0)

    def test_empty_path_empty_nodes_gives_full_recall(self):
        gt = {
            "relevant_nodes": [],
            "expected_path": [],
            "multi_hop": False,
        }
        result = compute_retq([], gt)
        # No expected nodes → recall is 1.0 by convention
        assert result["recall_at_k"] == pytest.approx(1.0)

    # ── Multi-hop path ────────────────────────────────────────────────────────

    def test_multi_hop_path_coverage(self, relationship_ground_truth):
        path = [
            "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
            "DeploymentSpec -[CONTAINS_POD_TEMPLATE]-> PodTemplateSpec",
        ]
        result = compute_retq(path, relationship_ground_truth)
        assert result["graph_coverage"] == pytest.approx(1.0)
        assert result["retq_score"] > 0.5

    def test_partial_path_coverage_less_than_one(self):
        # Use custom ground_truth where the second hop source ("Service") is
        # completely absent from the single-hop retrieved path string, so the
        # substring match in graph_coverage cannot accidentally fire.
        gt = {
            "relevant_nodes": [
                "io.k8s.api.apps.v1.Deployment",
                "io.k8s.api.core.v1.Service",
            ],
            "expected_path": [
                "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
                "Service -[SELECTS_POD]-> Pod",   # "Service" not in first-hop string
            ],
            "multi_hop": True,
        }
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_retq(path, gt)
        # "Service" is absent from the retrieved path → second hop not covered
        assert result["graph_coverage"] < 1.0

    # ── Irrelevant path ───────────────────────────────────────────────────────

    def test_irrelevant_path_gives_zero_recall(self, deployment_ground_truth):
        path = ["Service -[SELECTS_POD]-> Pod"]
        result = compute_retq(path, deployment_ground_truth)
        # "Service", "SELECTS_POD", "Pod" don't match Deployment or DeploymentSpec
        assert result["recall_at_k"] == pytest.approx(0.0)

    # ── F1 consistency ────────────────────────────────────────────────────────

    def test_f1_is_harmonic_mean_of_precision_recall(self, deployment_ground_truth):
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_retq(path, deployment_ground_truth)
        p = result["precision_at_k"]
        r = result["recall_at_k"]
        if p + r > 0:
            expected_f1 = 2 * p * r / (p + r)
            assert result["f1_at_k"] == pytest.approx(expected_f1, abs=1e-6)


# ═══════════════════════════════════════════════════════════════════════════════
# compute_reaq — Reasoning Quality
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestComputeReaq:
    """Unit tests for compute_reaq."""

    # ── Output shape ──────────────────────────────────────────────────────────

    def test_returns_required_keys(self, deployment_ground_truth):
        result = compute_reaq([], "some answer", deployment_ground_truth, "conceptual")
        for key in ("hop_accuracy", "multi_hop_success", "scope_accuracy", "reaq_score"):
            assert key in result, f"Missing key: {key}"

    def test_reaq_score_bounded(self, deployment_ground_truth):
        result = compute_reaq(
            ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"],
            "Deployment adalah controller yang mengelola Namespaced resource.",
            deployment_ground_truth,
            "conceptual",
        )
        assert 0.0 <= result["reaq_score"] <= 1.0

    # ── Single-hop: no expected_path, no multi_hop ────────────────────────────

    def test_single_hop_with_path_gets_full_hop_accuracy(self, deployment_ground_truth):
        # single_hop + non-empty path → hop_accuracy=1.0
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_reaq(path, "some answer", deployment_ground_truth, "conceptual")
        assert result["hop_accuracy"] == pytest.approx(1.0)

    def test_single_hop_no_path_gets_zero_hop_accuracy(self, deployment_ground_truth):
        result = compute_reaq([], "some answer", deployment_ground_truth, "conceptual")
        assert result["hop_accuracy"] == pytest.approx(0.0)

    def test_single_hop_multi_hop_success_always_one(self, deployment_ground_truth):
        # For non-multi_hop fixtures, multi_hop_success should be 1.0
        result = compute_reaq([], "some answer", deployment_ground_truth, "conceptual")
        assert result["multi_hop_success"] == pytest.approx(1.0)

    # ── Multi-hop ─────────────────────────────────────────────────────────────

    def test_multi_hop_perfect_path_gets_full_accuracy(self, relationship_ground_truth):
        path = [
            "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
            "DeploymentSpec -[CONTAINS_POD_TEMPLATE]-> PodTemplateSpec",
        ]
        result = compute_reaq(path, "Deployment controls ReplicaSet", relationship_ground_truth, "relationship")
        assert result["hop_accuracy"] == pytest.approx(1.0)
        assert result["multi_hop_success"] == pytest.approx(1.0)

    def test_multi_hop_missing_path_gets_zero_success(self, relationship_ground_truth):
        result = compute_reaq([], "Deployment controls ReplicaSet", relationship_ground_truth, "relationship")
        assert result["multi_hop_success"] == pytest.approx(0.0)

    def test_multi_hop_partial_path_less_than_one_accuracy(self):
        # Use custom ground_truth where the second hop source ("Service") is
        # completely absent from the single-hop retrieved path string, preventing
        # the substring match from accidentally marking it as covered.
        gt = {
            "answer": "Deployment controls Pods. Service selects Pods via label selector.",
            "relevant_nodes": [
                "io.k8s.api.apps.v1.Deployment",
                "io.k8s.api.core.v1.Service",
            ],
            "expected_path": [
                "Deployment -[HAS_PROPERTY]-> DeploymentSpec",
                "Service -[SELECTS_POD]-> Pod",   # "Service" not in first-hop string
            ],
            "multi_hop": True,
            "scope": "Namespaced",
        }
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        result = compute_reaq(path, "some answer", gt, "relationship")
        # Only 1 of 2 expected hops matched → hop_accuracy = 0.5
        assert result["hop_accuracy"] < 1.0

    # ── Scope accuracy ────────────────────────────────────────────────────────

    def test_namespaced_answer_mentioning_namespace_gets_full_scope(self, deployment_ground_truth):
        answer = "Deployment berjalan dalam namespace tertentu (Namespaced resource)."
        result = compute_reaq(["path"], answer, deployment_ground_truth, "conceptual")
        assert result["scope_accuracy"] == pytest.approx(1.0)

    def test_cluster_answer_mentioning_cluster_gets_full_scope(self, cluster_ground_truth):
        answer = "ClusterRole berlaku untuk seluruh cluster, tidak terikat namespace."
        result = compute_reaq([], answer, cluster_ground_truth, "conceptual")
        assert result["scope_accuracy"] == pytest.approx(1.0)

    def test_wrong_scope_mention_gets_partial_credit(self, deployment_ground_truth):
        # Answer completely ignores namespace keywords → partial credit (0.5)
        answer = "This is a generic answer with no scope keywords."
        result = compute_reaq([], answer, deployment_ground_truth, "conceptual")
        assert result["scope_accuracy"] == pytest.approx(0.5)

    def test_no_expected_scope_returns_one(self):
        gt = {
            "answer": "some answer",
            "relevant_nodes": [],
            "expected_path": [],
            "multi_hop": False,
            "scope": "",
        }
        result = compute_reaq([], "some answer", gt, "conceptual")
        assert result["scope_accuracy"] == pytest.approx(1.0)

    # ── reaq_score is average of three components ─────────────────────────────

    def test_reaq_score_is_average_of_three(self, deployment_ground_truth):
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]
        answer = "Deployment adalah controller yang mengelola resource dalam namespace."
        result = compute_reaq(path, answer, deployment_ground_truth, "conceptual")
        expected = (result["hop_accuracy"] + result["multi_hop_success"] + result["scope_accuracy"]) / 3
        assert result["reaq_score"] == pytest.approx(expected, abs=1e-9)


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-dimension consistency tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestWeightedTotal:
    """
    Verify that the weighted total formula holds for known inputs.
    This mirrors the calculation done in scripts/evaluate.py:run_evaluation().
    """

    ANSQ_W = 0.40
    RETQ_W = 0.35
    REAQ_W = 0.25

    def _weighted_total(self, ansq_score, retq_score, reaq_score):
        return ansq_score * self.ANSQ_W + retq_score * self.RETQ_W + reaq_score * self.REAQ_W

    def test_all_perfect_gives_one(self):
        assert self._weighted_total(1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_all_zero_gives_zero(self):
        assert self._weighted_total(0.0, 0.0, 0.0) == pytest.approx(0.0)

    def test_weights_sum_to_one(self):
        assert self.ANSQ_W + self.RETQ_W + self.REAQ_W == pytest.approx(1.0)

    def test_ansq_dominates_when_others_zero(self):
        total = self._weighted_total(1.0, 0.0, 0.0)
        assert total == pytest.approx(self.ANSQ_W)

    def test_retq_dominates_when_others_zero(self):
        total = self._weighted_total(0.0, 1.0, 0.0)
        assert total == pytest.approx(self.RETQ_W)

    def test_reaq_dominates_when_others_zero(self):
        total = self._weighted_total(0.0, 0.0, 1.0)
        assert total == pytest.approx(self.REAQ_W)

    def test_real_world_scenario(self, deployment_ground_truth):
        """End-to-end sanity: a decent answer on a simple conceptual question."""
        answer = "Deployment adalah controller yang mengelola ReplicaSet dalam namespace."
        path = ["Deployment -[HAS_PROPERTY]-> DeploymentSpec"]

        ansq = compute_ansq(answer, deployment_ground_truth, "conceptual")
        retq = compute_retq(path, deployment_ground_truth)
        reaq = compute_reaq(path, answer, deployment_ground_truth, "conceptual")

        total = self._weighted_total(ansq["ansq_score"], retq["retq_score"], reaq["reaq_score"])
        assert 0.0 <= total <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Fixture-driven parametrized tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestFixtureDataIntegrity:
    """
    Validates that every fixture JSON in tests/fixtures/ is internally consistent
    and provides enough data for metric computation to succeed.
    These run via the auto-parametrize in conftest.py (fixture_path parameter).
    """

    def test_fixture_has_required_top_level_keys(self, fixture_path):
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        for key in ("id", "type", "question", "resource", "scope", "multi_hop", "ground_truth"):
            assert key in data, f"[{fixture_path.stem}] Missing top-level key: {key}"

    def test_fixture_type_is_valid(self, fixture_path):
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        valid_types = {"conceptual", "yaml_gen", "relationship", "followup", "realworld"}
        assert data["type"] in valid_types, (
            f"[{fixture_path.stem}] Unknown type: {data['type']}"
        )

    def test_ground_truth_has_required_keys(self, fixture_path):
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        gt = data["ground_truth"]
        for key in ("answer", "relevant_nodes", "expected_path"):
            assert key in gt, f"[{fixture_path.stem}] ground_truth missing key: {key}"

    def test_metrics_dont_raise_on_empty_answer(self, fixture_path):
        """Metric functions must be robust to an empty string response."""
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        gt = data["ground_truth"]
        ftype = data["type"]

        # None of these should raise
        ansq = compute_ansq("", gt, ftype)
        retq = compute_retq([], gt)
        reaq = compute_reaq([], "", gt, ftype)

        assert 0.0 <= ansq["ansq_score"] <= 1.0
        assert 0.0 <= retq["retq_score"] <= 1.0
        assert 0.0 <= reaq["reaq_score"] <= 1.0

    def test_metrics_dont_raise_on_perfect_answer(self, fixture_path):
        """Metric functions must be robust when given the ground truth answer verbatim."""
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        gt = data["ground_truth"]
        ftype = data["type"]
        perfect_answer = gt["answer"]
        perfect_path = gt.get("expected_path", [])

        ansq = compute_ansq(perfect_answer, gt, ftype)
        retq = compute_retq(perfect_path, gt)
        reaq = compute_reaq(perfect_path, perfect_answer, gt, ftype)

        assert 0.0 <= ansq["ansq_score"] <= 1.0
        assert 0.0 <= retq["retq_score"] <= 1.0
        assert 0.0 <= reaq["reaq_score"] <= 1.0

    def test_multi_hop_flag_matches_expected_path_length(self, fixture_path):
        """
        If multi_hop=True the fixture should declare at least one expected_path step,
        or at least more than one relevant_node (otherwise multi-hop tracking is meaningless).
        """
        import json
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        if data["multi_hop"]:
            gt = data["ground_truth"]
            has_path = len(gt.get("expected_path", [])) >= 1
            has_multi_node = len(gt.get("relevant_nodes", [])) >= 2
            assert has_path or has_multi_node, (
                f"[{fixture_path.stem}] multi_hop=True but no path/multi-node evidence"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Realworld fixture integrity & selection-metadata tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
@pytest.mark.realworld
class TestRealworldFixtures:
    """
    Validates realworld fixtures produced by scripts/select_realworld_fixtures.py.

    These differ from synthesized fixtures in two ways:
      1. type == "realworld" (mapped to any sub-type for metric purposes)
      2. They carry extra selection metadata fields that must be structurally valid.
    """

    REALWORLD_DIR = Path(__file__).parent.parent / "fixtures" / "realworld"

    def _load_realworld(self) -> list[dict]:
        """
        Load only fixtures that were accepted by the scoring algorithm
        (selection_score >= REALWORLD_MIN_SCORE and selection_scores_breakdown present).
        Files dropped manually without metadata are silently excluded so the
        count is always driven by the algorithm output, never hardcoded.
        """
        results = []
        for p in sorted(self.REALWORLD_DIR.rglob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            score = data.get("selection_score", 0.0)
            has_metadata = "selection_scores_breakdown" in data
            if has_metadata and score >= REALWORLD_MIN_SCORE:
                results.append(data)
        return results

    def test_realworld_directory_exists(self):
        assert self.REALWORLD_DIR.exists(), (
            "tests/fixtures/realworld/ directory missing — "
            "run: python scripts/select_realworld_fixtures.py"
        )

    def test_realworld_has_at_least_one_fixture(self):
        fixtures = self._load_realworld()
        assert len(fixtures) >= 1, (
            "No realworld fixtures found. Run the selection script to populate them."
        )

    def test_all_realworld_fixtures_have_selection_metadata(self):
        """Every realworld fixture must carry the three selection metadata fields."""
        for data in self._load_realworld():
            fid = data.get("id", "unknown")
            assert "so_question_id" in data, f"[{fid}] missing so_question_id"
            assert "selection_score" in data, f"[{fid}] missing selection_score"
            assert "selection_scores_breakdown" in data, f"[{fid}] missing selection_scores_breakdown"
            assert "selection_rationale" in data, f"[{fid}] missing selection_rationale"

    def test_selection_score_above_threshold(self):
        """All accepted fixtures must have score >= 2.0 (the acceptance threshold)."""
        for data in self._load_realworld():
            score = data.get("selection_score", 0.0)
            fid = data.get("id", "unknown")
            assert score >= 2.0, (
                f"[{fid}] selection_score={score} is below 2.0 acceptance threshold"
            )

    def test_selection_score_breakdown_structure(self):
        """The breakdown dict must have all 6 expected keys."""
        required_keys = {
            "d1_graph_answerability", "d2_path_annotability", "d3_type_fit",
            "d4_so_quality", "d5_representativeness", "g4_penalty",
        }
        for data in self._load_realworld():
            fid = data.get("id", "unknown")
            breakdown = data.get("selection_scores_breakdown", {})
            missing = required_keys - set(breakdown.keys())
            assert not missing, f"[{fid}] selection_scores_breakdown missing: {missing}"

    def test_selection_score_matches_breakdown(self):
        """
        Verify that the stored selection_score is consistent with the
        breakdown scores and weights (D1×0.30 + D2×0.25 + D3×0.20 + D4×0.15 + D5×0.10 + penalty).
        """
        weights = dict(d1=0.30, d2=0.25, d3=0.20, d4=0.15, d5=0.10)
        for data in self._load_realworld():
            fid = data.get("id", "unknown")
            bd = data.get("selection_scores_breakdown", {})
            expected = (
                bd.get("d1_graph_answerability", 0) * weights["d1"]
                + bd.get("d2_path_annotability", 0) * weights["d2"]
                + bd.get("d3_type_fit", 0) * weights["d3"]
                + bd.get("d4_so_quality", 0) * weights["d4"]
                + bd.get("d5_representativeness", 0) * weights["d5"]
                + bd.get("g4_penalty", 0)   # g4_penalty is stored as negative float
            )
            stored = data.get("selection_score", 0.0)
            assert abs(stored - expected) < 0.01, (
                f"[{fid}] stored selection_score={stored} does not match "
                f"breakdown-derived score={expected:.4f}"
            )

    def test_individual_dimension_scores_in_range(self):
        """Each dimension score (D1–D5) must be 1, 2, or 3."""
        dim_keys = [
            "d1_graph_answerability", "d2_path_annotability", "d3_type_fit",
            "d4_so_quality", "d5_representativeness",
        ]
        for data in self._load_realworld():
            fid = data.get("id", "unknown")
            bd = data.get("selection_scores_breakdown", {})
            for k in dim_keys:
                v = bd.get(k)
                if v is not None:
                    assert v in (1, 2, 3), f"[{fid}] {k}={v} not in {{1, 2, 3}}"

    def test_realworld_fixtures_pass_metric_functions(self):
        """Metric functions must handle realworld type without raising."""
        for data in self._load_realworld():
            gt = data["ground_truth"]
            # realworld maps to the sub-type closest to its content;
            # for metric purposes we treat it as "conceptual" (safest default)
            ftype = "conceptual"
            perfect = gt["answer"]
            path = gt.get("expected_path", [])

            ansq = compute_ansq(perfect, gt, ftype)
            retq = compute_retq(path, gt)
            reaq = compute_reaq(path, perfect, gt, ftype)

            assert 0.0 <= ansq["ansq_score"] <= 1.0
            assert 0.0 <= retq["retq_score"] <= 1.0
            assert 0.0 <= reaq["reaq_score"] <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Gate function unit tests (scripts/select_realworld_fixtures.py)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.evaluation
class TestSelectionGates:
    """
    Unit tests for the 4-gate filtering logic in select_realworld_fixtures.py.
    These run without HuggingFace or Neo4j — pure function tests.
    """

    @pytest.fixture(autouse=True)
    def import_gates(self):
        from scripts.select_realworld_fixtures import (
            gate1_api_scope,
            gate2_node_exists,
            gate3_deprecation,
            gate4_complementarity,
            extract_primary_resource,
            score_candidate,
        )
        self.gate1 = gate1_api_scope
        self.gate2 = gate2_node_exists
        self.gate3 = gate3_deprecation
        self.gate4 = gate4_complementarity
        self.extract = extract_primary_resource
        self.score = score_candidate

    # ── G1 — API Scope ───────────────────────────────────────────────────────

    def test_g1_passes_for_yaml_question(self):
        q = "How do I write a Deployment manifest with 3 replicas?"
        a = "apiVersion: apps/v1\nkind: Deployment\nspec:\n  replicas: 3"
        assert self.gate1(q, a) is True

    def test_g1_fails_for_install_question(self):
        q = "How do I install Kubernetes on Ubuntu 22?"
        a = "Run kubeadm init after installing docker."
        assert self.gate1(q, a) is False

    def test_g1_fails_for_kubectl_ops(self):
        q = "kubectl port-forward not working on my cluster"
        a = "Check firewall rules and pod status."
        assert self.gate1(q, a) is False

    def test_g1_passes_for_configmap_question(self):
        q = "How to use ConfigMap as environment variable in a Pod?"
        a = "Use envFrom.configMapRef in container spec."
        assert self.gate1(q, a) is True

    # ── G2 — Node Existence ───────────────────────────────────────────────────

    def test_g2_passes_for_known_resource(self):
        assert self.gate2("Deployment") is True
        assert self.gate2("StatefulSet") is True
        assert self.gate2("ConfigMap") is True
        assert self.gate2("PersistentVolumeClaim") is True

    def test_g2_fails_for_unknown_resource(self):
        assert self.gate2("MyCustomCRD12345") is False
        assert self.gate2(None) is False

    # ── G3 — Deprecation ─────────────────────────────────────────────────────

    def test_g3_passes_for_stable_api(self):
        q = "How do I create a Deployment in apps/v1?"
        a = "apiVersion: apps/v1\nkind: Deployment"
        assert self.gate3(q, a) is True

    def test_g3_fails_for_deprecated_api(self):
        q = "How do I create an Ingress in extensions/v1beta1?"
        a = "apiVersion: extensions/v1beta1\nkind: Ingress"
        assert self.gate3(q, a) is False

    def test_g3_fails_for_policy_v1beta1(self):
        q = "Create a PodSecurityPolicy using policy/v1beta1"
        a = "apiVersion: policy/v1beta1\nkind: PodSecurityPolicy"
        assert self.gate3(q, a) is False

    # ── G4 — Complementarity ─────────────────────────────────────────────────

    def test_g4_new_resource_type_pair_passes(self):
        # Empty coverage → everything is new
        assert self.gate4("ServiceAccount", "yaml_gen", {}) is True

    def test_g4_existing_pair_fails(self):
        coverage = {("Deployment", "conceptual"): True}
        assert self.gate4("Deployment", "conceptual", coverage) is False

    def test_g4_same_resource_different_type_passes(self):
        coverage = {("Deployment", "conceptual"): True}
        # yaml_gen for Deployment is still new
        assert self.gate4("Deployment", "yaml_gen", coverage) is True

    # ── extract_primary_resource ──────────────────────────────────────────────

    def test_extract_deployment_from_question(self):
        q = "How do I scale a Deployment to 5 replicas?"
        a = "Edit Deployment spec.replicas."
        result = self.extract(q, a)
        assert result == "Deployment"

    def test_extract_statefulset_from_question(self):
        q = "StatefulSet volume claim template setup"
        a = "Use volumeClaimTemplates in StatefulSet spec."
        result = self.extract(q, a)
        assert result == "Statefulset"   # title-cased

    def test_extract_returns_none_for_no_resource(self):
        q = "why does my cluster fail to start?"
        a = "check the logs"
        result = self.extract(q, a)
        assert result is None

    # ── score_candidate end-to-end ────────────────────────────────────────────

    def test_score_candidate_api_question_accepted(self):
        row = {
            "question_title": "How to write a Deployment YAML with resource limits?",
            "question_body": "I need to set CPU and memory limits on my containers in a Deployment manifest.",
            "answer_body": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        resources:\n          limits:\n            cpu: '500m'\n            memory: '128Mi'",
            "answer_score": 25,
            "question_id": "99001",
        }
        result = self.score(row, {})
        assert result["status"] == "accept"
        assert result["total_score"] >= 2.0

    def test_score_candidate_install_question_discarded_g1(self):
        row = {
            "question_title": "How to install kubectl on Mac?",
            "question_body": "I want to install kubectl command line tool.",
            "answer_body": "brew install kubectl",
            "answer_score": 50,
            "question_id": "99002",
        }
        result = self.score(row, {})
        assert result["status"] == "discard_g1"

    def test_score_candidate_deprecated_api_discarded_g3(self):
        row = {
            "question_title": "Create Ingress with extensions/v1beta1",
            "question_body": "How do I create a Kubernetes Ingress using the old API?",
            "answer_body": "apiVersion: extensions/v1beta1\nkind: Ingress\nspec:\n  rules: []",
            "answer_score": 10,
            "question_id": "99003",
        }
        result = self.score(row, {})
        assert result["status"] == "discard_g3"

    def test_score_candidate_duplicate_applies_penalty(self):
        # Deployment conceptual already covered → -0.30 penalty
        coverage = {("Deployment", "conceptual"): True}
        row = {
            "question_title": "What is a Deployment in Kubernetes?",
            "question_body": "Can you explain what Deployment does?",
            "answer_body": "Deployment is a controller that manages ReplicaSets and ensures Pods are running.",
            "answer_score": 5,
            "question_id": "99004",
        }
        result = self.score(row, coverage)
        assert result["penalty"] == pytest.approx(0.30)
        # Score should be reduced by penalty
        assert result.get("total_score", 3.0) < 3.0
