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

# Groq free-tier limit: 6,000 tokens/minute.
# Template overhead (~500 tokens) + question (~100) + response budget (~1,500)
# leaves ~3,900 tokens for retrieved_data.  At ~4 chars/token → 15,600 chars.
# Use 12,000 chars to stay comfortably under the hard per-request limit.
GROQ_MAX_CONTEXT_CHARS = 12_000

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
    session_id: str
    chat_history: str
    extracted_intent: dict
    graph_context: str
    reasoning_path: Optional[List[str]]   # ← hop-by-hop traversal trace
    intent_type: Optional[str]            # ← "explain"|"generate_yaml"|"trace_relationship"|"followup"
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
        intent_type = intent_data.get("intent_type", "explain")
        return {"extracted_intent": intent_data, "intent_type": intent_type}

    except json.JSONDecodeError as e:
        logger.error(f"Thinker failed to output valid JSON: {e}")
        return {"error": "Failed to parse search intent from user query."}
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return {"error": str(e)}


def _make_retrieval_node(ablation_mode: str | None = None):
    """Returns an execute_retrieval_node closure bound to ablation_mode."""
    def execute_retrieval_node(state: AgentState):
        """Passes the extracted JSON intent to the deterministic Python retriever."""
        if state.get("error"):
            return {"graph_context": "Error in understanding intent. Cannot retrieve data.", "reasoning_path": []}

        try:
            retriever = StatefulK8sRetriever()
            intent_type = state.get("intent_type") or "explain"
            graph_context, reasoning_path = retriever.retrieve_context(
                state["extracted_intent"],
                intent_type=intent_type,
                ablation_mode=ablation_mode,
            )
            return {"graph_context": graph_context, "reasoning_path": reasoning_path}
        except Exception as e:
            logger.error(f"Custom Retrieval failed: {e}")
            return {
                "graph_context": "Database retrieval failed.",
                "reasoning_path": [],
                "error": str(e)
            }
    return execute_retrieval_node


def generate_response_node(state: AgentState):
    """The 'Speaker'. Uses LLM + Graph Data to formulate the final answer."""
    try:
        # Handle upstream errors in Python — never let the LLM see raw error strings
        # (K8s spec descriptions legitimately contain words like "error"/"failed",
        # so we only guard on the specific strings the code actually produces).
        _ERROR_STRINGS = (
            "Database retrieval failed.",
            "Error in understanding intent. Cannot retrieve data.",
        )
        raw_ctx = state.get("graph_context") or ""
        if state.get("error") or any(e in raw_ctx for e in _ERROR_STRINGS):
            return {"messages": [AIMessage(content=(
                "Maaf, saya tidak dapat menarik konteks dari Knowledge Graph saat ini. "
                "Mohon perjelas spesifikasi resource yang Anda cari."
            ))]}

        llm = get_speaker_llm()
        chain = RESPONSE_PROMPT | llm

        # Truncate graph_context to avoid 413 Payload Too Large on Groq free tier.
        raw_context = raw_ctx  # reuse value computed above
        if len(raw_context) > GROQ_MAX_CONTEXT_CHARS:
            raw_context = raw_context[:GROQ_MAX_CONTEXT_CHARS] + "\n... [context truncated]"
            logger.debug(f"graph_context truncated to {GROQ_MAX_CONTEXT_CHARS} chars")

        # Fix 5: Prevent false "followup" context note in new sessions with no real history.
        chat_history = state["chat_history"]
        intent_type = state.get("intent_type") or "explain"
        _EMPTY_HISTORY = ("", "Belum ada riwayat percakapan.")
        if intent_type == "followup" and chat_history.strip() in _EMPTY_HISTORY:
            intent_type = "explain"

        response = chain.invoke({
            "chat_history": chat_history,
            "retrieved_data": raw_context,
            "question": state["question"],
            "intent_type": intent_type
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
def create_agent_graph(ablation_mode: str | None = None):
    """Compiles the LangGraph state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("memory",    retrieve_memory_node)
    workflow.add_node("thinker",   extract_intent_node)
    workflow.add_node("retriever", _make_retrieval_node(ablation_mode))
    workflow.add_node("speaker",   generate_response_node)
    workflow.add_node("saver",     save_memory_node)

    workflow.set_entry_point("memory")
    workflow.add_edge("memory",    "thinker")
    workflow.add_edge("thinker",   "retriever")
    workflow.add_edge("retriever", "speaker")
    workflow.add_edge("speaker",   "saver")
    workflow.add_edge("saver",     END)

    return workflow.compile()
