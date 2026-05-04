# src/chatbot/custom_retriever.py
import json
import logging
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_index import VectorIndexManager
from src.graph.queries import (
    EXACT_MATCH_QUERY,
    SCHEMA_DEPS_QUERY,
    PATH_EDGES_QUERY,
    HYBRID_VECTOR_GRAPH_QUERY,
)

logger = logging.getLogger(__name__)

# ── Intent-aware depth mapping ────────────────────────────────────────────────
# Depth limits are derived from K8s schema graph structural properties,
# NOT from the evaluation dataset:
#
#   "explain" / "followup" → depth 2
#     Rationale: depth 1–2 nodes are resource-specific (shared by 2–3 resources).
#     Depth 3+ introduces generic shared types (PodSpec shared by 23+ resources)
#     that add noise for definitional questions.
#
#   "generate_yaml" / "trace_relationship" → depth 3
#     Rationale: YAML generation needs depth 1 (spec), depth 2 (spec fields),
#     depth 3 (container-level fields like image/ports/env).
#     Relationship traversal in K8s reaches cross-resource bridges at depth 2–3
#     (e.g. Deployment→DeploymentSpec→PodTemplateSpec→PodSpec).
#     Depth 4+ is dominated by generic utility types (Quantity, IntOrString,
#     LocalObjectReference) shared by 19–136 resources — informationally worthless
#     for distinguishing any specific relationship.
#
_DEPTH_BY_INTENT = {
    "explain":            2,
    "followup":           2,
    "generate_yaml":      3,
    "trace_relationship": 3,
    "planning":           3,
}
_DEFAULT_DEPTH = 3   # safe fallback for unknown intent types


class StatefulK8sRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    # ── Public entry point ────────────────────────────────────────────────────

    def retrieve_context(
        self,
        intent_data: dict,
        intent_type: str = "explain",
        max_depth: int | None = None,
    ) -> tuple[str, list[str]]:
        """
        Two-phase retrieval with intent-aware depth control:
          Phase 1 — Exact name match (precision-first).
          Phase 2 — Vector similarity fallback (recall).

        max_depth is resolved in priority order:
          1. Explicit caller override (max_depth argument)
          2. Intent-derived from _DEPTH_BY_INTENT mapping
          3. _DEFAULT_DEPTH fallback

        Returns:
            (graph_context_json, reasoning_path)
            reasoning_path: list of "Parent -[REL]-> Child" strings
        """
        # ── Resolve depth ─────────────────────────────────────────────────────
        depth = max_depth if max_depth is not None \
            else _DEPTH_BY_INTENT.get(intent_type, _DEFAULT_DEPTH)
        logger.info(f"[Retriever] intent_type='{intent_type}' → max_depth={depth}")

        primary = intent_data.get("primary_resource", "")
        related = intent_data.get("related_concepts", [])

        try:
            # ── Phase 1: Exact match ──────────────────────────────────────────
            root_name = self._exact_match(primary)

            if root_name:
                logger.info(f"[Retriever] Exact match: '{primary}' → '{root_name}'")
                record = self._schema_deps(root_name, depth)
            else:
                # ── Phase 2: Vector search ────────────────────────────────────
                logger.info(f"[Retriever] No exact match for '{primary}', using vector search")
                search_query = f"{primary} {' '.join(related)} Kubernetes"
                embedding    = self.vector_mgr.generate_embedding(search_query)
                record       = self._vector_deps(embedding, depth)
                if record:
                    root_name = record.get("RootResource", "")

            if not record:
                return "Tidak ada skema Kubernetes yang relevan di dalam Knowledge Graph.", []

            # ── Clean SchemaDependencies ──────────────────────────────────────
            deps = record.get("SchemaDependencies") or []
            record["SchemaDependencies"] = [d for d in deps if d is not None]

            # ── Build reasoning path (proper parent → child chain) ────────────
            reasoning_path = self._build_reasoning_path(root_name, depth)

            graph_context = json.dumps(record, indent=2, ensure_ascii=False)

            # ── Planning: also retrieve up to 2 related concepts and merge ────
            if intent_type == "planning" and related:
                for extra_resource in related[:2]:
                    try:
                        extra_root = self._exact_match(extra_resource)
                        if not extra_root:
                            continue
                        extra_record = self._schema_deps(extra_root, depth)
                        if not extra_record:
                            continue
                        extra_deps = extra_record.get("SchemaDependencies") or []
                        extra_record["SchemaDependencies"] = [d for d in extra_deps if d is not None]
                        extra_path = self._build_reasoning_path(extra_root, depth)
                        graph_context += "\n" + json.dumps(extra_record, indent=2, ensure_ascii=False)
                        seen_steps = set(reasoning_path)
                        for step in extra_path:
                            if step not in seen_steps:
                                reasoning_path.append(step)
                                seen_steps.add(step)
                        logger.info(f"[Retriever] Planning: merged context for '{extra_root}'")
                    except Exception as ex:
                        logger.warning(f"[Retriever] Planning extra retrieval failed for '{extra_resource}': {ex}")

            return graph_context, reasoning_path

        except Exception as e:
            logger.error(f"[Retriever] Graph traversal failed: {e}")
            return f"Error retrieving context from Neo4j: {str(e)}", []

    # ── Private helpers ───────────────────────────────────────────────────────

    def _exact_match(self, primary: str) -> str | None:
        """Returns the canonical node name if an exact match exists, else None."""
        if not primary:
            return None
        rows = self.db.execute_query(EXACT_MATCH_QUERY, {"primary_resource": primary})
        return rows[0]["name"] if rows else None

    def _schema_deps(self, root_name: str, max_depth: int) -> dict | None:
        """Fetch schema dependencies for a known root node name."""
        cypher = SCHEMA_DEPS_QUERY.format(max_depth=max_depth)
        rows   = self.db.execute_query(cypher, {"root_name": root_name})
        return dict(rows[0]) if rows else None

    def _vector_deps(self, embedding: list, max_depth: int) -> dict | None:
        """Fetch schema dependencies via vector similarity."""
        cypher = HYBRID_VECTOR_GRAPH_QUERY.format(max_depth=max_depth)
        rows   = self.db.execute_query(cypher, {"embedding": embedding})
        return dict(rows[0]) if rows else None

    def _build_reasoning_path(self, root_name: str, max_depth: int) -> list[str]:
        """
        Returns a deduplicated list of actual parent→child edge strings, e.g.:
          "Deployment -[HAS_PROPERTY]-> DeploymentSpec"
          "DeploymentSpec -[HAS_PROPERTY]-> PodTemplateSpec"
          "PodTemplateSpec -[HAS_PROPERTY]-> PodSpec"

        Uses PATH_EDGES_QUERY which extracts real intermediate nodes from
        graph paths — not root-to-leaf shortcuts.
        """
        if not root_name:
            return []
        try:
            cypher = PATH_EDGES_QUERY.format(max_depth=max_depth)
            rows   = self.db.execute_query(cypher, {"root_name": root_name})
            seen   = set()
            path   = []
            for row in rows:
                edge = f"{row['parent']} -[{row['rel_type']}]-> {row['child']}"
                if edge not in seen:
                    seen.add(edge)
                    path.append(edge)
            return path
        except Exception as e:
            logger.warning(f"[Retriever] Could not build reasoning path: {e}")
            return []
