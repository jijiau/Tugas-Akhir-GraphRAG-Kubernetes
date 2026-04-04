# src/chatbot/graph_agent.py
import json
import logging
import operator
from typing import TypedDict, List, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, BaseMessage

from src.chatbot.llm_factory import get_thinker_llm, get_speaker_llm
from src.chatbot.prompts import INTENT_PROMPT, RESPONSE_PROMPT
from src.chatbot.custom_retriever import StatefulK8sRetriever
from src.memory.zep_store import ZepMemoryStore

logger = logging.getLogger(__name__)

# Singleton ZepMemoryStore
_zep_store = None

def get_zep() -> ZepMemoryStore:
    global _zep_store
    if _zep_store is None:
        _zep_store = ZepMemoryStore()
    return _zep_store

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    session_id: str          # ← ditambahkan: diteruskan dari Streamlit
    chat_history: str
    extracted_intent: dict
    graph_context: str
    error: Optional[str]

# --- Nodes ---

def retrieve_memory_node(state: AgentState):
    """Fetches conversation history from Zep."""
    session_id = state.get("session_id", "default_session")
    try:
        history = get_zep().get_history(session_id=session_id, limit=5)
        return {"chat_history": history or "Belum ada riwayat percakapan."}
    except Exception as e:
        logger.warning(f"Zep memory failed: {e}")
        return {"chat_history": "Belum ada riwayat percakapan."}


def extract_intent_node(state: AgentState):
    """
    The 'Thinker'. Reads history + question, resolves pronouns,
    and outputs a strict JSON intent for the custom retriever.
    """
    if state.get("error"):
        return state

    try:
        llm = get_thinker_llm()
        chain = INTENT_PROMPT | llm
        response = chain.invoke({
            "chat_history": state["chat_history"],
            "question": state["question"]
        })

        raw_content = response.content.strip()
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
            raw_content = raw_content.strip()

        intent_data = json.loads(raw_content)
        return {"extracted_intent": intent_data}

    except json.JSONDecodeError as e:
        logger.error(f"Thinker failed to output valid JSON: {e}")
        return {"error": "Failed to parse search intent from user query."}
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return {"error": str(e)}


def execute_retrieval_node(state: AgentState):
    """Passes the extracted JSON intent to the deterministic Python retriever."""
    if state.get("error"):
        return {"graph_context": "Error in understanding intent. Cannot retrieve data."}

    try:
        retriever = StatefulK8sRetriever()
        graph_data = retriever.retrieve_context(state["extracted_intent"])
        return {"graph_context": graph_data}
    except Exception as e:
        logger.error(f"Custom Retrieval failed: {e}")
        return {"graph_context": "Database retrieval failed.", "error": str(e)}


def generate_response_node(state: AgentState):
    """The 'Speaker'. Uses LLM + Graph Data to formulate the final answer."""
    try:
        llm = get_speaker_llm()
        chain = RESPONSE_PROMPT | llm

        if state.get("error"):
            return {"messages": [AIMessage(content=f"System error: {state['error']}")]}

        response = chain.invoke({
            "chat_history": state["chat_history"],
            "retrieved_data": state["graph_context"],
            "question": state["question"]
        })
        return {"messages": [AIMessage(content=response.content)]}
    except Exception as e:
        logger.error(f"Response Gen failed: {e}")
        return {"messages": [AIMessage(content="Terjadi error saat membuat respons.")]}


def save_memory_node(state: AgentState):
    """Saves the completed conversation turn to Zep."""
    session_id = state.get("session_id", "default_session")
    try:
        user_msg = state["question"]
        ai_msg = state["messages"][-1].content if state["messages"] else ""
        if user_msg and ai_msg:
            get_zep().add_message(
                session_id=session_id,
                user_msg=user_msg,
                ai_msg=ai_msg
            )
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")
    return {}


# --- Graph Construction ---
def create_agent_graph():
    """Compiles the LangGraph state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("memory",    retrieve_memory_node)
    workflow.add_node("thinker",   extract_intent_node)
    workflow.add_node("retriever", execute_retrieval_node)
    workflow.add_node("speaker",   generate_response_node)
    workflow.add_node("saver",     save_memory_node)

    workflow.set_entry_point("memory")
    workflow.add_edge("memory",    "thinker")
    workflow.add_edge("thinker",   "retriever")
    workflow.add_edge("retriever", "speaker")
    workflow.add_edge("speaker",   "saver")
    workflow.add_edge("saver",     END)

    return workflow.compile()