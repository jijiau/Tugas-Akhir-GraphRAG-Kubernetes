import streamlit as st
import uuid
from dotenv import load_dotenv # Tambahkan ini
load_dotenv() # Dan jalankan ini

from src.chatbot.graph_agent import create_agent_graph

st.set_page_config(page_title="K8s GraphRAG Thesis", layout="wide")

st.title("🛡️ Kubernetes Swagger GraphRAG")
st.caption("Multi-Agent Architecture: OpenAI (Thinker) + Groq (Speaker)")

# Initialize Graph
@st.cache_resource
def load_agent():
    return create_agent_graph()

agent = load_agent()

# Menjaga sesi unik untuk Zep Memory
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about K8s API (e.g., 'How to create a Deployment?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consulting Kubernetes Graph..."):
            try:
                # Invoke Agent dengan State yang Benar
                state = agent.invoke({
                    "messages": [],
                    "question": prompt,
                    "chat_history": "",
                    "extracted_intent": {}, 
                    "graph_context": "",
                    "error": None
                })
                
                # Mengambil respons dari node terakhir (speaker)
                if "messages" in state and state["messages"]:
                    response = state["messages"][-1].content
                else:
                    response = "Sistem gagal menghasilkan respons."
                    
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"System Error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})