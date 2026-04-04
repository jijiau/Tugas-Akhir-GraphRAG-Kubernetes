import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chatbot.custom_retriever import StatefulK8sRetriever
from dotenv import load_dotenv

load_dotenv()

def debug_graph_retrieval(primary_resource: str = "Deployment", related: list = None):
    retriever = StatefulK8sRetriever()

    mock_intent = {
        "primary_resource": primary_resource,
        "related_concepts": related or [],
    }

    print(f"\n🔍 Testing retrieval for: '{mock_intent['primary_resource']}'")
    print("-" * 60)

    context, reasoning_path = retriever.retrieve_context(mock_intent)

    if "Error" in str(context) or "Tidak ada" in str(context):
        print(f"❌ RETRIEVAL FAILED!\nDetail: {context}")
        return

    # ── Graph Context ─────────────────────────────────────────────────────────
    try:
        parsed = json.loads(context)
    except Exception:
        parsed = {}

    root     = parsed.get("RootResource", "?")
    score    = parsed.get("VectorSimilarityScore", 0)
    deps     = parsed.get("SchemaDependencies", [])
    is_exact = score == 1.0

    match_label = "✅ EXACT MATCH" if is_exact else f"🔀 VECTOR MATCH (score={score:.4f})"
    print(f"{match_label}  →  Root: {root}\n")

    if root.lower() != primary_resource.lower() and not is_exact:
        print(f"  ⚠️  Perhatian: query '{primary_resource}' → root '{root}'")
        print(f"     (vector search tidak menemukan exact match)\n")

    # ── Schema Dependencies summary ───────────────────────────────────────────
    print(f"📦 Schema Dependencies ({len(deps)} node, max depth={max(d['path_depth'] for d in deps) if deps else 0}):")
    by_depth = {}
    for d in deps:
        by_depth.setdefault(d["path_depth"], []).append(d["child_resource"])
    for depth in sorted(by_depth):
        nodes = ", ".join(sorted(set(by_depth[depth])))
        print(f"  Depth {depth}: {nodes}")

    # ── Reasoning Path ────────────────────────────────────────────────────────
    print(f"\n🧭 Reasoning Path — actual parent→child chain ({len(reasoning_path)} unique edges):")
    if reasoning_path:
        for i, step in enumerate(reasoning_path, 1):
            print(f"  {i:>2}. {step}")
    else:
        print("  (kosong)")

    # ── Statistik ─────────────────────────────────────────────────────────────
    print(f"\n📊 Ringkasan:")
    print(f"  Root resource  : {root} ({'exact' if is_exact else 'vector'})")
    print(f"  Schema deps    : {len(deps)} node")
    print(f"  Unique edges   : {len(reasoning_path)} (reasoning path)")
    unique_parents = len(set(s.split(' -[')[0] for s in reasoning_path))
    print(f"  Unique parents : {unique_parents}")


if __name__ == "__main__":
    resources = [
        ("Deployment", []),
        ("StatefulSet", ["PVC", "storage"]),
        ("Service", ["selector", "port"]),
    ]
    for name, rel in resources:
        debug_graph_retrieval(name, rel)
        print()
