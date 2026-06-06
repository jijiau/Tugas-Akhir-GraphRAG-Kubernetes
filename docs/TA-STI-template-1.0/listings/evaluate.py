import re
import math

_SCOPE_Q_KEYWORDS = [
    "scope", "scoped", "namespaced", "cluster-scoped", "cluster-wide",
    "namespace-level", "cluster-level", "lingkup", "cakupan",
    "bisa diakses lintas", "seluruh cluster", "non-namespaced",
]

_K8S_TERM_RE = re.compile(
    r'\b(?:'
    r'[A-Z][a-z]+(?:[A-Z][a-zA-Z]+)+'
    r'|Deployment|StatefulSet|DaemonSet|ReplicaSet|CronJob|Ingress'
    r'|ConfigMap|Secret|Namespace|ServiceAccount|Endpoints|Pod|Service'
    r'|Node|ResourceQuota|LimitRange|NetworkPolicy|StorageClass'
    r'|Role|ClusterRole|RoleBinding|ClusterRoleBinding'
    r'|HorizontalPodAutoscaler|PersistentVolume|PersistentVolumeClaim'
    r'|apiVersion|kubectl|namespace[sd]?|pod[sd]?|deployment[sd]?|service[sd]?'
    r'|configmap[sd]?|secret[sd]?|ingress(?:es)?|statefulset[sd]?|daemonset[sd]?'
    r'|replicaset[sd]?|cronjob[sd]?|job[sd]?|persistentvolume(?:claim)?[sd]?'
    r'|clusterrole(?:binding)?[sd]?|rolebinding[sd]?|serviceaccount[sd]?'
    r'|networkpolicy|hpa|pvc|pv|rbac'
    r')\b'
)


def _token_f1(pred: str, gold: str) -> float:
    pred_tokens = set(pred.lower().split())
    gold_tokens = set(gold.lower().split())
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = pred_tokens & gold_tokens
    precision = len(common) / len(pred_tokens)
    recall    = len(common) / len(gold_tokens)
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0


def _cosine_similarity(embedder, text1: str, text2: str) -> float:
    import numpy as np
    e1 = embedder.embed_query(text1)
    e2 = embedder.embed_query(text2)
    v1, v2 = np.array(e1), np.array(e2)
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / denom) if denom > 0 else 0.0


def _effective_type(fixture_type: str, ground_truth: dict) -> str:
    if fixture_type == "realworld":
        return ground_truth.get("realworld_subtype", "realworld")
    return fixture_type


def _extract_yaml_block(text: str) -> str:
    if "```yaml" in text:
        parts = text.split("```yaml", 1)
        if len(parts) > 1:
            yaml_lines = parts[1].split("```")[0].strip().splitlines()
            return "\n".join(yaml_lines).strip()
    if "```" in text:
        parts = text.split("```", 1)
        if len(parts) > 1:
            yaml_lines = parts[1].split("```")[0].strip().splitlines()
            return "\n".join(yaml_lines).strip()
    return text.strip()


def compute_ansq(
    answer: str,
    ground_truth: dict,
    fixture_type: str,
    embedder=None,
    ablation_mode: str | None = None,
) -> dict:
    scores = {}
    fixture_type = _effective_type(fixture_type, ground_truth)

    if fixture_type == "yaml_gen":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml
            yaml.safe_load(yaml_candidate)
            scores["syntactic_validity"] = 1.0
        except Exception:
            scores["syntactic_validity"] = 0.0
    else:
        scores["syntactic_validity"] = None

    if fixture_type == "yaml_gen":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml
            import kubernetes_validate
            data = yaml.safe_load(yaml_candidate)
            if isinstance(data, dict):
                kubernetes_validate.validate(data, "1.29", strict=False)
                scores["schema_compliance"] = 1.0
            else:
                scores["schema_compliance"] = 0.0
        except ImportError:
            scores["schema_compliance"] = None
        except Exception:
            scores["schema_compliance"] = 0.0
    else:
        scores["schema_compliance"] = None

    gt_answer = ground_truth.get("answer", "")
    if embedder is not None and gt_answer:
        scores["answer_relevance"] = _cosine_similarity(embedder, answer, gt_answer)
    else:
        scores["answer_relevance"] = _token_f1(answer, gt_answer)

    def _node_matches(node: str, answer_lower: str) -> bool:
        nl = node.lower()
        return nl in answer_lower or nl + "s" in answer_lower or nl + "es" in answer_lower

    faith_source = ground_truth.get("key_nodes") or ground_truth.get("relevant_nodes", [])
    gt_nodes = [n.split(".")[-1] for n in faith_source]
    hit = sum(1 for n in gt_nodes if _node_matches(n, answer.lower()))
    scores["faithfulness"] = hit / len(gt_nodes) if gt_nodes else 1.0

    if fixture_type == "yaml_gen" and ablation_mode is not None and ablation_mode != "no_yaml_layer3":
        yaml_candidate = _extract_yaml_block(answer)
        try:
            import yaml as _yaml
            _data = _yaml.safe_load(yaml_candidate)
            if isinstance(_data, dict):
                from src.validation.yaml_validator import YAMLValidator
                _kind = _data.get("kind", "")
                _vresult = YAMLValidator().validate(yaml_candidate, _kind)
                scores["layer3_compliance"] = None if _vresult["syntax_errors"] \
                    else (1.0 if not _vresult["missing_fields"] else 0.0)
            else:
                scores["layer3_compliance"] = None
        except Exception:
            scores["layer3_compliance"] = None
    else:
        scores["layer3_compliance"] = None

    applicable = [v for v in scores.values() if v is not None]
    scores["ansq_score"] = sum(applicable) / len(applicable) if applicable else 0.0
    return scores


def compute_retq(reasoning_path: list, ground_truth: dict) -> dict:
    _RELATION_RE = re.compile(r"-\[([^\]]+)\]->?")

    def _node_tokens(step: str) -> list:
        cleaned = _RELATION_RE.sub(" ", step)
        return [t for t in cleaned.split() if t]

    expected_nodes = set(n.split(".")[-1] for n in ground_truth.get("relevant_nodes", []))
    retrieved_nodes, seen_nodes = [], set()
    for step in reasoning_path:
        for tok in _node_tokens(step):
            if tok not in seen_nodes:
                seen_nodes.add(tok)
                retrieved_nodes.append(tok)
    retrieved_set = set(retrieved_nodes)

    intersection = retrieved_set & expected_nodes
    precision = len(intersection) / len(retrieved_set) if retrieved_set else 0.0
    recall    = len(intersection) / len(expected_nodes) if expected_nodes else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    expected_path = ground_truth.get("expected_path", [])
    graph_coverage = (
        len([p for p in expected_path
             if any(p.split(" -[")[0] in step for step in reasoning_path)])
        / len(expected_path) if expected_path else 1.0
    )

    k = len(retrieved_nodes)
    dcg = sum(
        (1.0 / math.log2(i + 2))
        for i, node in enumerate(retrieved_nodes)
        if node in expected_nodes
    )
    ideal_hits = min(len(expected_nodes), k) if k > 0 else 0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    ndcg_at_k = dcg / idcg if idcg > 0 else (1.0 if not expected_nodes else 0.0)

    if expected_path:
        matched_edges = sum(
            1 for ep in expected_path
            if any(ep in step or step in ep for step in reasoning_path)
        )
        edge_coverage = matched_edges / len(expected_path)
    else:
        edge_coverage = 1.0

    retq_score = (precision + recall + f1 + graph_coverage + ndcg_at_k + edge_coverage) / 6

    return {
        "precision_at_k": precision,
        "recall_at_k": recall,
        "f1_at_k": f1,
        "graph_coverage": graph_coverage,
        "ndcg_at_k": ndcg_at_k,
        "edge_coverage": edge_coverage,
        "retq_score": retq_score,
    }


def compute_reaq(
    reasoning_path: list,
    answer: str,
    ground_truth: dict,
    fixture_type: str,
    graph_context: str = "",
    fixture_scope: str = "",
    question: str = "",
    k8s_vocabulary: set = None,
    cgg_mode: bool = False,
) -> dict:
    fixture_type  = _effective_type(fixture_type, ground_truth)
    expected_path = ground_truth.get("expected_path", [])
    multi_hop     = ground_truth.get("multi_hop", False)

    if expected_path and multi_hop:
        matched = sum(
            1 for ep in expected_path
            if any(ep.split(" -[")[0] in step for step in reasoning_path)
        )
        hop_accuracy = matched / len(expected_path)
    else:
        hop_accuracy = 1.0 if reasoning_path else 0.0

    multi_hop_success = 1.0 if (multi_hop and reasoning_path) or (not multi_hop) else 0.0

    question_lower = question.lower()
    scope_relevant = (
        any(kw in question_lower for kw in _SCOPE_Q_KEYWORDS)
        or fixture_scope == "Cluster"
    )

    if not scope_relevant:
        scope_accuracy = 1.0
    else:
        _NAMESPACED_POSITIVE = ["namespaced", "dalam namespace", "di namespace",
                                 "namespace-scoped", "namespace tertentu"]
        _NAMESPACED_NEGATIVE = ["cluster-scoped", "cluster-wide", "seluruh cluster",
                                 "tidak terikat namespace", "non-namespaced"]
        _CLUSTER_POSITIVE    = ["cluster-scoped", "cluster-wide", "seluruh cluster",
                                 "tidak terikat namespace", "non-namespaced", "lintas namespace"]
        _CLUSTER_NEGATIVE    = ["namespaced", "dalam namespace", "namespace-scoped"]

        answer_lower = answer.lower()
        if fixture_scope == "Namespaced":
            correct_hit = any(kw in answer_lower for kw in _NAMESPACED_POSITIVE)
            wrong_hit   = any(kw in answer_lower for kw in _NAMESPACED_NEGATIVE)
            scope_accuracy = 1.0 if (correct_hit and not wrong_hit) else (0.0 if wrong_hit else 0.5)
        elif fixture_scope == "Cluster":
            correct_hit = any(kw in answer_lower for kw in _CLUSTER_POSITIVE)
            wrong_hit   = any(kw in answer_lower for kw in _CLUSTER_NEGATIVE)
            scope_accuracy = 1.0 if (correct_hit and not wrong_hit) else (0.0 if wrong_hit else 0.5)
        else:
            scope_accuracy = 1.0

    if cgg_mode:
        from src.validation.cgg_validator import cgg_grounding_score
        grounding_score, hallucination_rate = cgg_grounding_score(answer, graph_context)
    else:
        answer_terms = set(t.lower() for t in _K8S_TERM_RE.findall(answer))
        if answer_terms:
            if k8s_vocabulary:
                grounded = sum(1 for t in answer_terms if t in k8s_vocabulary)
            else:
                ctx_lower = graph_context.lower()
                grounded  = sum(1 for t in answer_terms if t in ctx_lower)
            hallucination_rate = 1.0 - grounded / len(answer_terms)
        else:
            hallucination_rate = 0.0
        grounding_score = 1.0 - hallucination_rate

    reaq_score = (hop_accuracy + multi_hop_success + scope_accuracy + grounding_score) / 4

    return {
        "hop_accuracy":       hop_accuracy,
        "multi_hop_success":  multi_hop_success,
        "scope_accuracy":     scope_accuracy,
        "hallucination_rate": hallucination_rate,
        "grounding_score":    grounding_score,
        "reaq_score":         reaq_score,
    }
