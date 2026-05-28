"""
src/validation/cgg_validator.py
Citation-Grounded Generation (CGG) post-processor.

Checks K8s terms extracted from the model's answer against the graph_context
that was actually retrieved for the specific query — not the global K8s vocabulary.

This is stricter than global-vocabulary grounding: a term that exists in the K8s
schema but was NOT retrieved for this query is counted as a hallucination.
The hypothesis is that this better reflects whether the model's answer is anchored
to the retrieved context rather than to prior LLM training knowledge.
"""
import re

# Same pattern as evaluate.py _K8S_TERM_RE — kept in sync manually.
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


def extract_k8s_terms(text: str) -> set[str]:
    """Extract K8s API terms from text, returned as a lowercase set."""
    return set(t.lower() for t in _K8S_TERM_RE.findall(text))


def cgg_grounding_score(answer: str, graph_context: str) -> tuple[float, float]:
    """
    CGG post-processor: check K8s terms in answer against retrieved graph_context.

    Args:
        answer:        The model's generated answer text.
        graph_context: The context string returned by the retriever for this query.

    Returns:
        (grounding_score, hallucination_rate) — both in [0, 1].
        grounding_score = 1 - hallucination_rate.
        When no K8s terms are found in the answer, returns (1.0, 0.0).
    """
    answer_terms = extract_k8s_terms(answer)
    if not answer_terms:
        return 1.0, 0.0

    ctx_lower = graph_context.lower()
    grounded = sum(1 for t in answer_terms if t in ctx_lower)
    hallucination_rate = 1.0 - grounded / len(answer_terms)
    return 1.0 - hallucination_rate, hallucination_rate
