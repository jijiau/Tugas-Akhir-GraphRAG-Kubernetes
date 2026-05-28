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
# Batas kedalaman diturunkan dari properti struktural graf skema K8s,
# bukan dari dataset evaluasi:
#
#   "explain" / "followup" → depth 2
#     Node di depth 1–2 bersifat resource-specific (dirujuk oleh 2–3 resource).
#     Depth 3+ memasukkan tipe generik bersama (PodSpec dipakai oleh 23+ resource)
#     yang menambah noise untuk pertanyaan definisi.
#
#   "generate_yaml" / "trace_relationship" / "planning" → depth 3
#     YAML generation butuh depth 3 untuk menjangkau field container-level
#     (image, ports, env). Depth 4+ didominasi utility types (Quantity, IntOrString)
#     yang dipakai oleh 19–136 resource — tidak informatif untuk membedakan relasi.
#
_DEPTH_BY_INTENT = {
    "explain":            2,
    "followup":           2,
    "generate_yaml":      3,
    "trace_relationship": 3,
    "planning":           3,
}
_DEFAULT_DEPTH = 3

# trace_relationship dikeluarkan dari multi-entity karena penambahan entity kedua
# menyebabkan precision penalty di RetQ (lebih banyak node dari yang relevan).
_MULTI_ENTITY_INTENTS = {"planning", "generate_yaml"}


class StatefulK8sRetriever:
    def __init__(self):
        self.db = Neo4jClient()
        self.vector_mgr = VectorIndexManager()

    def retrieve_context(
        self,
        intent_data: dict,
        intent_type: str = "explain",
        max_depth: int | None = None,
        ablation_mode: str | None = None,
    ) -> tuple[str, list[str]]:
        """
        Two-phase retrieval with intent-aware depth control:
          Phase 1 — Exact name match (precision-first).
          Phase 2 — Vector similarity fallback (recall).

        Depth resolution priority:
          1. ablation_mode override ('depth_2' / 'depth_3')
          2. Explicit max_depth argument
          3. _DEPTH_BY_INTENT mapping
          4. _DEFAULT_DEPTH fallback

        ablation_mode (None in production):
          'no_phase1'       A1: skip exact match
          'no_multihop'     A2: seed node only, no traversal
          'depth_2'         A3: force depth=2
          'depth_3'         A4: force depth=3
          'no_multi_entity' A6c: disable multi-entity retrieval
        """
        if ablation_mode is not None and ablation_mode.startswith('depth_'):
            try:
                depth = int(ablation_mode.split('_', 1)[1])
            except (IndexError, ValueError):
                depth = max_depth if max_depth is not None \
                    else _DEPTH_BY_INTENT.get(intent_type, _DEFAULT_DEPTH)
        else:
            depth = max_depth if max_depth is not None \
                else _DEPTH_BY_INTENT.get(intent_type, _DEFAULT_DEPTH)

        primary = intent_data.get("primary_resource", "")
        related = intent_data.get("related_concepts", [])

        try:
            # Phase 1: Exact match (A1: skipped)
            if ablation_mode == 'no_phase1':
                root_name = None
            else:
                root_name = self._exact_match(primary)

            if root_name:
                if ablation_mode == 'no_multihop':
                    record = {"RootResource": root_name, "SchemaDependencies": []}
                else:
                    record = self._schema_deps(root_name, depth)
            else:
                # Phase 2: Vector search
                search_query = f"{primary} {' '.join(related)} Kubernetes"
                embedding    = self.vector_mgr.generate_embedding(search_query)
                record       = self._vector_deps(embedding, depth)
                if record:
                    root_name = record.get("RootResource", "")
                    if ablation_mode == 'no_multihop':
                        record = {
                            "RootResource": root_name,
                            "Description": record.get("Description", ""),
                            "SchemaDependencies": [],
                        }

            if not record:
                return "Tidak ada skema Kubernetes yang relevan di dalam Knowledge Graph.", []

            deps = record.get("SchemaDependencies") or []
            record["SchemaDependencies"] = [d for d in deps if d is not None]

            if ablation_mode == 'no_multihop':
                reasoning_path = []
            else:
                reasoning_path = self._build_reasoning_path(root_name, depth)

            graph_context = json.dumps(record, indent=2, ensure_ascii=False)

            # Multi-entity retrieval: gabungkan konteks dari hingga 2 related_concepts.
            # Diperlukan untuk planning/generate_yaml yang mencakup 2+ resource
            # yang tidak dapat dicapai dalam 3 hop dari primary saja.
            effective_multi_entity = (
                set() if ablation_mode == 'no_multi_entity' else _MULTI_ENTITY_INTENTS
            )
            if intent_type in effective_multi_entity and related:
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
                    except Exception as ex:
                        logger.warning(f"[Retriever] Multi-entity failed for '{extra_resource}': {ex}")

            return graph_context, reasoning_path

        except Exception as e:
            logger.error(f"[Retriever] Graph traversal failed: {e}")
            return f"Error retrieving context from Neo4j: {str(e)}", []

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
        Returns deduplicated list of actual parent→child edge strings, e.g.:
          "Deployment -[HAS_PROPERTY]-> DeploymentSpec"
          "DeploymentSpec -[HAS_PROPERTY]-> PodTemplateSpec"

        Menggunakan PATH_EDGES_QUERY yang mengekstrak node perantara nyata
        dari jalur graf — bukan pintasan langsung root ke leaf.
        """
        if not root_name:
            return []
        try:
            cypher = PATH_EDGES_QUERY.format(max_depth=max_depth)
            rows   = self.db.execute_query(cypher, {"root_name": root_name})
            seen, path = set(), []
            for row in rows:
                edge = f"{row['parent']} -[{row['rel_type']}]-> {row['child']}"
                if edge not in seen:
                    seen.add(edge)
                    path.append(edge)
            return path
        except Exception as e:
            logger.warning(f"[Retriever] Could not build reasoning path: {e}")
            return []
