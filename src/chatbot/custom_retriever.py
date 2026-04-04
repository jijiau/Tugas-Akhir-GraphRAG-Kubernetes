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


class StatefulK8sRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    # ── Public entry point ────────────────────────────────────────────────────

    def retrieve_context(self, intent_data: dict, max_depth: int = 4) -> tuple[str, list[str]]:
        """
        Two-phase retrieval:
          Phase 1 — Exact name match (precision-first).
          Phase 2 — Vector similarity fallback (recall).

        Returns:
            (graph_context_json, reasoning_path)
            reasoning_path: list of "Parent -[REL]-> Child" strings (proper chain)
        """
        primary = intent_data.get("primary_resource", "")
        related  = intent_data.get("related_concepts", [])

        try:
            # ── Phase 1: Exact match ──────────────────────────────────────────
            root_name = self._exact_match(primary)

            if root_name:
                logger.info(f"[Retriever] Exact match: '{primary}' → '{root_name}'")
                record = self._schema_deps(root_name, max_depth)
            else:
                # ── Phase 2: Vector search ────────────────────────────────────
                logger.info(f"[Retriever] No exact match for '{primary}', using vector search")
                search_query = f"{primary} {' '.join(related)} Kubernetes"
                embedding    = self.vector_mgr.generate_embedding(search_query)
                record       = self._vector_deps(embedding, max_depth)
                if record:
                    root_name = record.get("RootResource", "")

            if not record:
                return "Tidak ada skema Kubernetes yang relevan di dalam Knowledge Graph.", []

            # ── Clean SchemaDependencies ──────────────────────────────────────
            deps = record.get("SchemaDependencies") or []
            record["SchemaDependencies"] = [d for d in deps if d is not None]

            # ── Build reasoning path (proper parent → child chain) ────────────
            reasoning_path = self._build_reasoning_path(root_name, max_depth)

            graph_context = json.dumps(record, indent=2, ensure_ascii=False)
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
                edge = f"{row['parent']} -[HAS_PROPERTY]-> {row['child']}"
                if edge not in seen:
                    seen.add(edge)
                    path.append(edge)
            return path
        except Exception as e:
            logger.warning(f"[Retriever] Could not build reasoning path: {e}")
            return []
