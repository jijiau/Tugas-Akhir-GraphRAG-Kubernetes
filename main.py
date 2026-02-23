import streamlit as st
from src.chatbot.graph_agent import create_agent_graph
from src.config.settings import settings

st.set_page_config(page_title="K8s GraphRAG Thesis", layout="wide")

st.title("🛡️ Kubernetes Swagger GraphRAG")
st.caption("Multi-Agent Architecture: OpenAI (Thinker) + Groq (Speaker)")

# Initialize Graph
@st.cache_resource
def load_agent():
    return create_agent_graph()

agent = load_agent()

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
                # Invoke Agent
                state = agent.invoke({
                    "messages": [],
                    "question": prompt,
                    "graph_context": "",
                    "cypher_query": "",
                    "query_result": "",
                    "chat_history": "",
                    "error": None
                })
                response = state["messages"][-1].content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"System Error: {e}")