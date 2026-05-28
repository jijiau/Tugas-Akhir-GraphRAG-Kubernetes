import uuid
import re
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from src.chatbot.graph_agent import create_agent_graph

st.set_page_config(
    page_title="K8s GraphRAG Assistant",
    page_icon=None,
    layout="wide",
)

# ── Constants ──────────────────────────────────────────────────────────────────

_INTENT_LABELS = {
    "explain":            "Penjelasan",
    "generate_yaml":      "Generate YAML",
    "trace_relationship": "Relasi Resource",
    "followup":           "Follow-up",
}

_API_VERSION_MAP = {
    "Pod": "v1", "Service": "v1", "ConfigMap": "v1", "Secret": "v1",
    "PersistentVolumeClaim": "v1", "PersistentVolume": "v1",
    "Namespace": "v1", "ServiceAccount": "v1", "Endpoints": "v1",
    "Node": "v1", "ResourceQuota": "v1", "LimitRange": "v1",
    "Deployment": "apps/v1", "StatefulSet": "apps/v1",
    "DaemonSet": "apps/v1", "ReplicaSet": "apps/v1",
    "Job": "batch/v1", "CronJob": "batch/v1",
    "HorizontalPodAutoscaler": "autoscaling/v2",
    "Ingress": "networking.k8s.io/v1", "NetworkPolicy": "networking.k8s.io/v1",
    "Role": "rbac.authorization.k8s.io/v1",
    "ClusterRole": "rbac.authorization.k8s.io/v1",
    "RoleBinding": "rbac.authorization.k8s.io/v1",
    "ClusterRoleBinding": "rbac.authorization.k8s.io/v1",
    "StorageClass": "storage.k8s.io/v1",
}

_K8S_DOCS_MAP = {
    "Deployment":              "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/deployment-v1/",
    "Pod":                     "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/",
    "Service":                 "https://kubernetes.io/docs/reference/kubernetes-api/service-resources/service-v1/",
    "StatefulSet":             "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/stateful-set-v1/",
    "DaemonSet":               "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/daemon-set-v1/",
    "ReplicaSet":              "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/replica-set-v1/",
    "Job":                     "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/job-v1/",
    "CronJob":                 "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/cron-job-v1/",
    "ConfigMap":               "https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/config-map-v1/",
    "Secret":                  "https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/secret-v1/",
    "PersistentVolume":        "https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/persistent-volume-v1/",
    "PersistentVolumeClaim":   "https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/persistent-volume-claim-v1/",
    "StorageClass":            "https://kubernetes.io/docs/reference/kubernetes-api/config-and-storage-resources/storage-class-v1/",
    "Ingress":                 "https://kubernetes.io/docs/reference/kubernetes-api/service-resources/ingress-v1/",
    "NetworkPolicy":           "https://kubernetes.io/docs/reference/kubernetes-api/policy-resources/network-policy-v1/",
    "HorizontalPodAutoscaler": "https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/",
    "ServiceAccount":          "https://kubernetes.io/docs/reference/kubernetes-api/authentication-resources/service-account-v1/",
    "Role":                    "https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/role-v1/",
    "ClusterRole":             "https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-v1/",
    "RoleBinding":             "https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/role-binding-v1/",
    "ClusterRoleBinding":      "https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-binding-v1/",
    "Namespace":               "https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/namespace-v1/",
    "Node":                    "https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/node-v1/",
    "ResourceQuota":           "https://kubernetes.io/docs/reference/kubernetes-api/policy-resources/resource-quota-v1/",
    "Endpoints":               "https://kubernetes.io/docs/reference/kubernetes-api/service-resources/endpoints-v1/",
}

# ── Session state ──────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history_display" not in st.session_state:
    st.session_state.chat_history_display = []
if "agent_graph" not in st.session_state:
    st.session_state.agent_graph = create_agent_graph()
if "sessions" not in st.session_state:
    _now = datetime.now().strftime("%H:%M")
    st.session_state.sessions = {
        st.session_state.session_id: {
            "label": "Percakapan Baru",
            "display_history": [],
            "created_at": _now,
        }
    }


# ── Helper functions ───────────────────────────────────────────────────────────

def _get_session_label(display_history: list) -> str:
    for msg in display_history:
        if msg["role"] == "user":
            text = msg["content"]
            return text if len(text) <= 40 else text[:37] + "..."
    return "Percakapan Baru"


def _confidence_info(reasoning_path: list) -> tuple[str, str, str]:
    """Return (label, bg_color, fg_color) based on graph traversal depth."""
    n = len(reasoning_path)
    if n == 0:
        return "Pengetahuan Umum LLM", "#fef3c7", "#92400e"
    if n <= 3:
        return "Sebagian dari Graph", "#e0f2fe", "#0369a1"
    return "Dari Knowledge Graph", "#d1fae5", "#065f46"


def _render_intent_row(extracted_intent: dict, reasoning_path: list):
    """Show intent type badge and confidence indicator above the response."""
    if not extracted_intent:
        return

    intent_type  = extracted_intent.get("intent_type", "")
    primary      = extracted_intent.get("primary_resource", "")
    intent_label = _INTENT_LABELS.get(intent_type, intent_type)
    conf_label, conf_bg, conf_fg = _confidence_info(reasoning_path)

    col_intent, col_conf = st.columns([3, 2])
    with col_intent:
        st.markdown(
            f'<span style="background:#dbeafe;color:#1e40af;padding:3px 10px;'
            f'border-radius:4px;font-size:12px;font-weight:600">{intent_label}</span>'
            f'&nbsp;&nbsp;<span style="color:#6b7280;font-size:13px">{primary}</span>',
            unsafe_allow_html=True,
        )
    with col_conf:
        st.markdown(
            f'<span style="background:{conf_bg};color:{conf_fg};padding:3px 10px;'
            f'border-radius:4px;font-size:12px">{conf_label}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


def _render_response_with_yaml(content: str):
    """Render response text, using st.code() for yaml blocks to enable copy button."""
    parts = re.split(r'```yaml\s*\n(.*?)```', content, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                st.markdown(part)
        else:
            st.code(part.rstrip(), language="yaml")


# ── Retrieval Trace visualization ──────────────────────────────────────────────

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
    """
    Assign depth to each node via BFS from ALL roots.
    Multi-entity retrieval (generate_yaml/planning) produces reasoning paths
    rooted at multiple resources, so we must seed BFS from every root.
    """
    if not edges:
        return {}
    parents  = {e[0] for e in edges}
    children = {e[2] for e in edges}
    roots    = parents - children
    if not roots:
        roots = {edges[0][0]}  # cyclic fallback

    depth_map = {r: 0 for r in roots}
    queue     = list(roots)
    while queue:
        current = queue.pop(0)
        for p, _, c in edges:
            if p == current and c not in depth_map:
                depth_map[c] = depth_map[current] + 1
                queue.append(c)

    # Safety net for disconnected subgraphs — every node must have an int depth
    # so the DataFrame in render_retrieval_trace stays mono-typed (Int64).
    fallback_depth = (max(depth_map.values()) + 1) if depth_map else 0
    for p, _, c in edges:
        for node in (p, c):
            if node not in depth_map:
                depth_map[node] = fallback_depth
    return depth_map


def _build_dot(edges: list[tuple], depth_map: dict[str, int],
               max_edges: int = 25) -> str:
    """Build Graphviz DOT string, colour-coded by depth level."""
    shown = sorted(edges, key=lambda e: depth_map.get(e[0], 99))[:max_edges]

    palette = {
        0: ("#1e3a5f", "white"),
        1: ("#2563eb", "white"),
        2: ("#3b82f6", "white"),
        3: ("#60a5fa", "black"),
        4: ("#bfdbfe", "black"),
    }

    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  graph [bgcolor="transparent", pad="0.5", ranksep="0.8", nodesep="0.4"];',
        '  node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=9, color="#64748b", arrowsize=0.8];',
        "",
    ]

    seen_nodes = set()
    for p, _, c in shown:
        for node in (p, c):
            if node not in seen_nodes:
                seen_nodes.add(node)
                d          = min(depth_map.get(node, 4), 4)
                fill, font = palette[d]
                bold       = ", penwidth=2" if d == 0 else ""
                lines.append(
                    f'  "{node}" [fillcolor="{fill}", fontcolor="{font}"{bold}];'
                )
    lines.append("")

    for p, _, c in shown:
        lines.append(f'  "{p}" -> "{c}";')

    lines.append("}")
    return "\n".join(lines)


def render_retrieval_trace(reasoning_path: list[str]):
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
    api_ver   = _API_VERSION_MAP.get(root, "—")

    with st.expander("Retrieval Trace — Alur Pencarian Graph", expanded=False):

        # ── Metrics row ──────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Root Resource", root)
        c2.metric("API Version",   api_ver)
        c3.metric("Nodes",         n_nodes)
        c4.metric("Unique Edges",  n_edges)
        c5.metric("Max Depth",     max_depth)

        st.divider()

        # ── Tabs ─────────────────────────────────────────────────────────────
        tab_graph, tab_table, tab_sources, tab_legend = st.tabs(
            ["Graph Visualization", "Edge Table", "Sumber Referensi", "Keterangan Warna"]
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
                    "Depth":        depth_map.get(p, pd.NA),
                    "Parent Node":  p,
                    "Relationship": rel,
                    "Child Node":   c,
                }
                for p, rel, c in edges
            ]
            df = pd.DataFrame(rows)
            # Force nullable integer dtype so st.dataframe NumberColumn never
            # receives mixed int+str (PyArrow ArrowInvalid).
            df["Depth"] = df["Depth"].astype("Int64")
            df = df.sort_values(["Depth", "Parent Node"], na_position="last")
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
            st.caption(
                f"Total {n_edges} unique edges | {n_nodes} nodes | max depth {max_depth}"
            )

        with tab_sources:
            all_nodes = {node for p, _, c in edges for node in (p, c)}
            refs = {n: _K8S_DOCS_MAP[n] for n in all_nodes if n in _K8S_DOCS_MAP}
            if refs:
                st.caption("Dokumentasi resmi Kubernetes untuk resource yang ditemukan:")
                for name in sorted(refs):
                    url     = refs[name]
                    api     = _API_VERSION_MAP.get(name, "")
                    version = f" `{api}`" if api else ""
                    st.markdown(f"- [{name}]({url}){version}")
            else:
                st.caption(
                    "Tidak ada resource utama yang cocok dengan dokumentasi kubernetes.io "
                    "pada jalur ini."
                )

        with tab_legend:
            st.markdown("""
| Warna | Depth | Artinya |
|-------|-------|---------|
| **Navy gelap** | 0 | Root resource (hasil pencarian utama) |
| **Biru** | 1 | Properti langsung (e.g. `spec`, `status`) |
| **Biru sedang** | 2 | Sub-properti (e.g. `PodTemplateSpec`) |
| **Biru muda** | 3 | Detail lanjut (e.g. `PodSpec`) |
| **Biru pucat** | 4 | Leaf node (e.g. `Container`, `Volume`) |

**Cara membaca graph:**
- Arah panah = arah relasi schema (parent → child)
- Semakin ke kanan = semakin dalam di dalam definisi Kubernetes
- Node berwarna navy adalah resource yang ditemukan untuk menjawab pertanyaanmu
            """)


def render_assistant_message(content: str, extracted_intent: dict,
                             reasoning_path: list):
    """Render a full assistant turn: intent badge, response with yaml copy, retrieval trace."""
    _render_intent_row(extracted_intent, reasoning_path)
    _render_response_with_yaml(content)
    render_retrieval_trace(reasoning_path)


# ── UI ─────────────────────────────────────────────────────────────────────────

def _switch_session(sid: str):
    cur_id = st.session_state.session_id
    st.session_state.sessions[cur_id]["display_history"] = (
        st.session_state.chat_history_display
    )
    st.session_state.sessions[cur_id]["label"] = _get_session_label(
        st.session_state.chat_history_display
    )
    st.session_state.session_id = sid
    st.session_state.chat_history_display = list(
        st.session_state.sessions[sid]["display_history"]
    )


with st.sidebar:
    st.header("Riwayat Percakapan")

    if st.button("Chat Baru", use_container_width=True):
        cur_id = st.session_state.session_id
        st.session_state.sessions[cur_id]["display_history"] = (
            st.session_state.chat_history_display
        )
        st.session_state.sessions[cur_id]["label"] = _get_session_label(
            st.session_state.chat_history_display
        )
        new_id = str(uuid.uuid4())
        _now = datetime.now().strftime("%H:%M")
        st.session_state.sessions[new_id] = {
            "label": "Percakapan Baru",
            "display_history": [],
            "created_at": _now,
        }
        st.session_state.session_id = new_id
        st.session_state.chat_history_display = []
        st.rerun()

    st.divider()

    for sid, data in reversed(list(st.session_state.sessions.items())):
        is_active = (sid == st.session_state.session_id)
        label = f"[Aktif] {data['label']}" if is_active else data["label"]
        st.button(
            label,
            key=f"sess_{sid}",
            use_container_width=True,
            disabled=is_active,
            on_click=_switch_session,
            args=(sid,),
        )
        st.caption(data["created_at"])


st.title("K8s GraphRAG Assistant")
st.caption("Chatbot berbasis Knowledge Graph untuk dokumentasi Kubernetes")

# Render conversation history
for msg in st.session_state.chat_history_display:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_assistant_message(
                msg["content"],
                msg.get("extracted_intent", {}),
                msg.get("reasoning_path", []),
            )
        else:
            st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Tanyakan tentang Kubernetes..."):
    st.session_state.chat_history_display.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Menelusuri Knowledge Graph..."):
            result = st.session_state.agent_graph.invoke({
                "question":         prompt,
                "session_id":       st.session_state.session_id,
                "messages":         [],
                "chat_history":     "",
                "extracted_intent": {},
                "graph_context":    "",
                "reasoning_path":   [],
                "error":            None,
            })

        ai_response      = result["messages"][-1].content if result.get("messages") else "Terjadi error."
        reasoning_path   = result.get("reasoning_path") or []
        graph_context    = result.get("graph_context", "")
        extracted_intent = result.get("extracted_intent") or {}

        render_assistant_message(ai_response, extracted_intent, reasoning_path)

    st.session_state.chat_history_display.append({
        "role":             "assistant",
        "content":          ai_response,
        "reasoning_path":   reasoning_path,
        "graph_context":    graph_context,
        "extracted_intent": extracted_intent,
    })
