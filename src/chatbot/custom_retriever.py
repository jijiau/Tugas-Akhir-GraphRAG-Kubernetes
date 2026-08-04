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
    _ALL_EDGE_TYPES,
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

# Intents yang memerlukan traversal multi-entity (primary + related_concepts).
# trace_relationship dikeluarkan karena penambahan entity kedua menyebabkan
# precision penalty di RetQ (lebih banyak node diambil dari yang relevan).
_MULTI_ENTITY_INTENTS = {"planning", "generate_yaml"}


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
        ablation_mode: str | None = None,
        question: str = "",
    ) -> tuple[str, list[str]]:
        """
        Two-phase retrieval with intent-aware depth control:
          Phase 1 — Exact name match (precision-first).
          Phase 2 — Vector similarity fallback (recall).

        max_depth is resolved in priority order:
          1. ablation_mode override ('depth_2' / 'depth_3')
          2. Explicit caller override (max_depth argument)
          3. Intent-derived from _DEPTH_BY_INTENT mapping
          4. _DEFAULT_DEPTH fallback

        Context traversal uses ALL 18 edge types by default (F14). The
        'has_property_only' ablation restricts it to HAS_PROPERTY alone, to
        isolate the semantic-edge contribution (thesis T1).

        `question` (F15): when provided, the Phase-2 vector fallback embeds the
        raw user question — symmetric with the Vector baseline — instead of a
        keyword soup. This locks the embedded-text variable so the only
        GraphRAG-vs-Vector difference is graph traversal. Phase-1 exact match
        still uses the extracted intent (ablated separately by A1/no_phase1).

        ablation_mode values (ablation study only — None in production):
          'no_phase1'         A1: skip exact match, go straight to vector
          'no_multihop'       A2: seed node only, no schema_deps traversal
          'depth_2'           A3: override all intents to depth=2
          'depth_3'           A4: override all intents to depth=3
          'no_multi_entity'   A6c: disable multi-entity retrieval for all intents
          'has_property_only' A7: restrict context traversal to HAS_PROPERTY (F14)

        Returns:
            (graph_context_json, reasoning_path)
            reasoning_path: list of "Parent -[REL]-> Child" strings
        """
        # ── Resolve depth ─────────────────────────────────────────────────────
        # ablation_mode 'depth_N' (e.g. 'depth_1', 'depth_4') overrides all intents.
        if ablation_mode is not None and ablation_mode.startswith('depth_'):
            try:
                depth = int(ablation_mode.split('_', 1)[1])
            except (IndexError, ValueError):
                depth = max_depth if max_depth is not None \
                    else _DEPTH_BY_INTENT.get(intent_type, _DEFAULT_DEPTH)
        else:
            depth = max_depth if max_depth is not None \
                else _DEPTH_BY_INTENT.get(intent_type, _DEFAULT_DEPTH)

        # ── Resolve context edge-set (F14) ────────────────────────────────────
        # Default: all 18 edge types. Ablation A7 isolates HAS_PROPERTY only.
        edge_types = "HAS_PROPERTY" if ablation_mode == "has_property_only" else _ALL_EDGE_TYPES
        logger.info(f"[Retriever] intent_type='{intent_type}' ablation='{ablation_mode}' → max_depth={depth} edges={'HAS_PROPERTY' if edge_types=='HAS_PROPERTY' else 'ALL_18'}")

        primary = intent_data.get("primary_resource", "")
        related = intent_data.get("related_concepts", [])

        try:
            # ── Phase 1: Exact match (A1: skipped) ───────────────────────────
            if ablation_mode == 'no_phase1':
                root_name = None
            else:
                root_name = self._exact_match(primary)

            if root_name:
                logger.info(f"[Retriever] Exact match: '{primary}' → '{root_name}'")
                if ablation_mode == 'no_multihop':
                    # A2: seed node only — no multi-hop traversal
                    record = {"RootResource": root_name, "SchemaDependencies": []}
                else:
                    record = self._schema_deps(root_name, depth, edge_types)
            else:
                # ── Phase 2: Vector search ────────────────────────────────────
                logger.info(f"[Retriever] No exact match for '{primary}', using vector search")
                # F15: embed the raw user question (symmetric with the Vector
                # baseline) so the only GraphRAG-vs-Vector difference is graph
                # traversal. Fall back to the entity keyword string only when no
                # question is supplied (defensive — e.g. legacy callers).
                search_query = question.strip() if question and question.strip() \
                    else f"{primary} {' '.join(related)} Kubernetes"
                embedding    = self.vector_mgr.generate_embedding(search_query)
                record       = self._vector_deps(embedding, depth, edge_types)
                if record:
                    root_name = record.get("RootResource", "")
                    if ablation_mode == 'no_multihop':
                        record = {
                            "RootResource": root_name,
                            "Description": record.get("Description", ""),
                            "SchemaDependencies": [],
                        }

            if not record:
                return "No relevant Kubernetes schema found in the Knowledge Graph.", []

            # ── Clean SchemaDependencies ──────────────────────────────────────
            deps = record.get("SchemaDependencies") or []
            record["SchemaDependencies"] = [d for d in deps if d is not None]

            # ── Build reasoning path (A2: skipped) ───────────────────────────
            if ablation_mode == 'no_multihop':
                reasoning_path = []
            else:
                reasoning_path = self._build_reasoning_path(root_name, depth, edge_types)

            graph_context = json.dumps(record, indent=2, ensure_ascii=False)

            # ── Multi-entity: retrieve up to 2 related concepts and merge ────────
            # Applies to planning and generate_yaml (A6c disables entirely).
            # These intents often span 2+ resources not reachable within 3 hops
            # from primary alone (e.g. HPA→Deployment, Secret→Container).
            effective_multi_entity = (
                set() if ablation_mode == 'no_multi_entity' else _MULTI_ENTITY_INTENTS
            )
            if intent_type in effective_multi_entity and related:
                for extra_resource in related[:2]:
                    try:
                        extra_root = self._exact_match(extra_resource)
                        if not extra_root:
                            continue
                        extra_record = self._schema_deps(extra_root, depth, edge_types)
                        if not extra_record:
                            continue
                        extra_deps = extra_record.get("SchemaDependencies") or []
                        extra_record["SchemaDependencies"] = [d for d in extra_deps if d is not None]
                        extra_path = self._build_reasoning_path(extra_root, depth, edge_types)
                        graph_context += "\n" + json.dumps(extra_record, indent=2, ensure_ascii=False)
                        seen_steps = set(reasoning_path)
                        for step in extra_path:
                            if step not in seen_steps:
                                reasoning_path.append(step)
                                seen_steps.add(step)
                        logger.info(f"[Retriever] Multi-entity ({intent_type}): merged context for '{extra_root}'")
                    except Exception as ex:
                        logger.warning(f"[Retriever] Multi-entity extra retrieval failed for '{extra_resource}': {ex}")

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

    def _schema_deps(self, root_name: str, max_depth: int,
                     edge_types: str = _ALL_EDGE_TYPES) -> dict | None:
        """Fetch schema dependencies for a known root node name.

        edge_types (F14): relationship types to traverse for the LLM context.
        Defaults to all 18; 'HAS_PROPERTY' under the has_property_only ablation.
        """
        cypher = SCHEMA_DEPS_QUERY.format(max_depth=max_depth, all_edges=edge_types)
        rows   = self.db.execute_query(cypher, {"root_name": root_name})
        return dict(rows[0]) if rows else None

    def _vector_deps(self, embedding: list, max_depth: int,
                     edge_types: str = _ALL_EDGE_TYPES) -> dict | None:
        """Fetch schema dependencies via vector similarity.

        edge_types (F14): see _schema_deps.
        """
        cypher = HYBRID_VECTOR_GRAPH_QUERY.format(max_depth=max_depth, all_edges=edge_types)
        rows   = self.db.execute_query(cypher, {"embedding": embedding})
        return dict(rows[0]) if rows else None

    def _build_reasoning_path(self, root_name: str, max_depth: int,
                              edge_types: str = _ALL_EDGE_TYPES) -> list[str]:
        """
        Returns a deduplicated list of actual parent→child edge strings, e.g.:
          "Deployment -[HAS_PROPERTY]-> DeploymentSpec"
          "DeploymentSpec -[HAS_PROPERTY]-> PodTemplateSpec"
          "PodTemplateSpec -[HAS_PROPERTY]-> PodSpec"

        Uses PATH_EDGES_QUERY which extracts real intermediate nodes from
        graph paths — not root-to-leaf shortcuts.

        edge_types (F14): edge-set for the path. Defaults to all 18; restricted
        to 'HAS_PROPERTY' under the has_property_only ablation so RetQ and
        path_coverage reflect the reduced traversal (T1 retrieval evidence).
        """
        if not root_name:
            return []
        try:
            cypher = PATH_EDGES_QUERY.format(max_depth=max_depth, all_edges=edge_types)
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
