# main.py — patch untuk session_id management yang benar
# Merge ini dengan main.py kamu yang sudah ada

import uuid
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from src.chatbot.graph_agent import create_agent_graph

st.set_page_config(page_title="K8s GraphRAG Thesis", layout="wide")

# ── Session state initialization ────────────────────────────────────────────
# Dijalankan SEKALI saat browser tab pertama kali dibuka.
# Streamlit menjamin st.session_state persisten selama tab tidak di-refresh.

if "session_id" not in st.session_state:
    # UUID unik per browser session — tidak berubah saat rerender
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history_display" not in st.session_state:
    # List pesan untuk ditampilkan di UI (terpisah dari Zep)
    st.session_state.chat_history_display = []

if "agent_graph" not in st.session_state:
    # Compile graph sekali — tidak di-recompile setiap rerender
    st.session_state.agent_graph = create_agent_graph()

# ── UI ───────────────────────────────────────────────────────────────────────
st.title("K8s GraphRAG Assistant")
st.caption(f"Session ID: `{st.session_state.session_id}`")  # untuk debug, bisa dihapus nanti

# Tampilkan riwayat chat dari session state
for msg in st.session_state.chat_history_display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input pengguna
if prompt := st.chat_input("Tanyakan tentang Kubernetes..."):
    # Tampilkan pesan user di UI
    st.session_state.chat_history_display.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Jalankan agent graph dengan session_id yang persisten
    with st.chat_message("assistant"):
        with st.spinner("Memproses..."):
            result = st.session_state.agent_graph.invoke({
                "question": prompt,
                "session_id": st.session_state.session_id,  # ← diteruskan ke graph
                "messages": [],
                "chat_history": "",
                "extracted_intent": {},
                "graph_context": "",
                "error": None,
            })

        ai_response = result["messages"][-1].content if result["messages"] else "Terjadi error."
        st.markdown(ai_response)

    # Simpan respons AI ke display history
    st.session_state.chat_history_display.append({"role": "assistant", "content": ai_response})