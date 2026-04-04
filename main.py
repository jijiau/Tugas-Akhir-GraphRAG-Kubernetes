import uuid
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from src.chatbot.graph_agent import create_agent_graph

st.set_page_config(
    page_title="K8s GraphRAG Assistant",
    page_icon="⎈",
    layout="wide",
)

# ── Session state initialization ──────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []
if "agent_graph" not in st.session_state:
    st.session_state.agent_graph = create_agent_graph()


# ── Retrieval Trace visualization ─────────────────────────────────────────────

def _parse_edges(reasoning_path: list[str]) -> list[tuple[str, str, str]]:
    """Parse 'Parent -[REL]-> Child' strings into (parent, rel, child) tuples."""
    edges = []
    for step in reasoning_path:
        if " -[" in step and "]-> " in step:
            parent, rest = step.split(" -[", 1)
            rel, child   = rest.split("]-> ", 1)
            edges.append((parent.strip(), rel.strip(), child.strip()))
    return edges


def _bfs_depth(edges: list[tuple]) -> dict[str, int]:
    """Assign depth to each node via BFS from the root."""
    if not edges:
        return {}
    parents  = {e[0] for e in edges}
    children = {e[2] for e in edges}
    roots    = parents - children
    root     = next(iter(roots)) if roots else edges[0][0]

    depth_map = {root: 0}
    queue     = [root]
    while queue:
        current = queue.pop(0)
        for p, r, c in edges:
            if p == current and c not in depth_map:
                depth_map[c] = depth_map[current] + 1
                queue.append(c)
    return depth_map


def _build_dot(edges: list[tuple], depth_map: dict[str, int],
               max_edges: int = 25) -> str:
    """Build Graphviz DOT string, colour-coded by depth level."""
    # Limit edges shown in graph to avoid clutter; prefer shallow edges
    shown = sorted(edges, key=lambda e: depth_map.get(e[0], 99))[:max_edges]

    # Depth → (fill colour, font colour)
    palette = {
        0: ("#1e3a5f", "white"),   # root — dark navy
        1: ("#2563eb", "white"),   # depth 1 — blue
        2: ("#3b82f6", "white"),   # depth 2 — medium blue
        3: ("#60a5fa", "black"),   # depth 3 — sky blue
        4: ("#bfdbfe", "black"),   # depth 4+ — pale blue
    }

    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  graph [bgcolor="transparent", pad="0.5", ranksep="0.8", nodesep="0.4"];',
        '  node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=9, color="#64748b", arrowsize=0.8];',
        "",
    ]

    # Nodes
    seen_nodes = set()
    for p, r, c in shown:
        for node in (p, c):
            if node not in seen_nodes:
                seen_nodes.add(node)
                d     = min(depth_map.get(node, 4), 4)
                fill, font = palette[d]
                bold  = ", penwidth=2" if d == 0 else ""
                lines.append(
                    f'  "{node}" [fillcolor="{fill}", fontcolor="{font}"{bold}];'
                )
    lines.append("")

    # Edges
    for p, r, c in shown:
        lines.append(f'  "{p}" -> "{c}";')

    lines.append("}")
    return "\n".join(lines)


def render_retrieval_trace(reasoning_path: list[str], graph_context_json: str):
    """Render the Retrieval Trace section inside an expander."""
    if not reasoning_path:
        return

    edges     = _parse_edges(reasoning_path)
    depth_map = _bfs_depth(edges)
    if not edges:
        return

    root      = next((n for n, d in depth_map.items() if d == 0), "?")
    max_depth = max(depth_map.values(), default=0)
    n_nodes   = len(depth_map)
    n_edges   = len(edges)

    with st.expander("🧭 Retrieval Trace — Alur Pencarian Graph", expanded=False):

        # ── Metrics row ──────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔵 Root Resource", root)
        c2.metric("📍 Nodes", n_nodes)
        c3.metric("🔗 Unique Edges", n_edges)
        c4.metric("🌊 Max Depth", max_depth)

        st.divider()

        # ── Tabs: Graph | Table ───────────────────────────────────────────────
        tab_graph, tab_table, tab_legend = st.tabs(
            ["🗺️ Graph Visualization", "📋 Edge Table", "🎨 Keterangan Warna"]
        )

        with tab_graph:
            if n_edges > 25:
                st.caption(
                    f"Menampilkan 25 edge terdekat dari root (dari {n_edges} total). "
                    "Lihat tab **Edge Table** untuk daftar lengkap."
                )
            dot = _build_dot(edges, depth_map, max_edges=25)
            st.graphviz_chart(dot, use_container_width=True)

        with tab_table:
            import pandas as pd
            rows = [
                {
                    "Depth": depth_map.get(p, "?"),
                    "Parent Node": p,
                    "Relationship": rel,
                    "Child Node": c,
                }
                for p, rel, c in edges
            ]
            df = pd.DataFrame(rows).sort_values(["Depth", "Parent Node"])
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Depth":        st.column_config.NumberColumn("Depth", width="small"),
                    "Parent Node":  st.column_config.TextColumn("Parent Node"),
                    "Relationship": st.column_config.TextColumn("Relationship", width="medium"),
                    "Child Node":   st.column_config.TextColumn("Child Node"),
                },
            )
            st.caption(f"Total {n_edges} unique edges | {n_nodes} nodes | max depth {max_depth}")

        with tab_legend:
            st.markdown("""
| Warna | Depth | Artinya |
|-------|-------|---------|
| 🟦 **Navy gelap** | 0 | Root resource (hasil pencarian utama) |
| 🔵 **Biru** | 1 | Properti langsung (e.g. `spec`, `status`) |
| 🔷 **Biru sedang** | 2 | Sub-properti (e.g. `PodTemplateSpec`) |
| 🩵 **Biru muda** | 3 | Detail lanjut (e.g. `PodSpec`) |
| 🌐 **Biru pucat** | 4 | Leaf node (e.g. `Container`, `Volume`) |

**Cara membaca graph:**
- Arah panah = arah relasi schema (parent → child)
- Semakin ke kanan = semakin dalam di dalam definisi Kubernetes
- Node berwarna navy adalah resource yang ditemukan untuk menjawab pertanyaanmu
            """)


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("⎈ K8s GraphRAG Assistant")
st.caption("Chatbot berbasis Knowledge Graph untuk dokumentasi Kubernetes")

# Tampilkan riwayat chat
for msg in st.session_state.chat_history_display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("reasoning_path"):
            render_retrieval_trace(msg["reasoning_path"], msg.get("graph_context", ""))

# Input pengguna
if prompt := st.chat_input("Tanyakan tentang Kubernetes... (contoh: Apa itu Deployment?)"):
    st.session_state.chat_history_display.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Menelusuri Knowledge Graph..."):
            result = st.session_state.agent_graph.invoke({
                "question":       prompt,
                "session_id":     st.session_state.session_id,
                "messages":       [],
                "chat_history":   "",
                "extracted_intent": {},
                "graph_context":  "",
                "reasoning_path": [],
                "error":          None,
            })

        ai_response    = result["messages"][-1].content if result.get("messages") else "Terjadi error."
        reasoning_path = result.get("reasoning_path") or []
        graph_context  = result.get("graph_context", "")

        st.markdown(ai_response)
        render_retrieval_trace(reasoning_path, graph_context)

    st.session_state.chat_history_display.append({
        "role":           "assistant",
        "content":        ai_response,
        "reasoning_path": reasoning_path,
        "graph_context":  graph_context,
    })
