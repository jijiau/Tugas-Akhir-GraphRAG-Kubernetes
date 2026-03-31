# src/chatbot/graph_agent.py
import json
import logging
import operator
from typing import TypedDict, List, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import PromptTemplate

from src.chatbot.llm_factory import get_thinker_llm, get_speaker_llm
from src.chatbot.prompts import INTENT_PROMPT, RESPONSE_PROMPT
from src.chatbot.custom_retriever import StatefulK8sRetriever
from src.memory.zep_store import ZepMemoryStore

logger = logging.getLogger(__name__)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    chat_history: str
    extracted_intent: dict  # Replaces raw cypher_query
    graph_context: str      # Replaces raw query_result
    error: Optional[str]

# --- Nodes ---
def retrieve_memory_node(state: AgentState):
    """Fetches bi-directional chat history from Zep."""
    try:
        zep = ZepMemoryStore()
        history = zep.get_history(session_id="default_session", limit=5)
        return {"chat_history": history}
    except Exception as e:
        logger.warning(f"Zep memory failed: {e}")
        return {"chat_history": "No history available."}

def extract_intent_node(state: AgentState):
    """
    The 'Thinker'. Reads history + question, resolves pronouns, 
    and outputs a strict JSON intent for the custom retriever.
    """
    if state.get("error"):
        return state

    try:
        llm = get_thinker_llm()
        
        # Langsung gunakan INTENT_PROMPT yang di-import
        chain = INTENT_PROMPT | llm
        
        response = chain.invoke({
            "chat_history": state["chat_history"],
            "question": state["question"]
        })
        
        raw_content = response.content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3].strip()
            
        intent_data = json.loads(raw_content)
        return {"extracted_intent": intent_data}
        
    except json.JSONDecodeError as e:
        logger.error(f"Thinker failed to output valid JSON: {e}")
        return {"error": "Failed to parse search intent from user query."}
    except Exception as e:
        logger.error(f"Intent extraction failed: {e}")
        return {"error": str(e)}
    
def execute_retrieval_node(state: AgentState):
    """Passes the extracted JSON intent to your deterministic Python retriever."""
    if state.get("error"):
        return {"graph_context": "Error in understanding intent. Cannot retrieve data."}
    
    try:
        retriever = StatefulK8sRetriever()
        intent = state["extracted_intent"]
        
        # custom_retriever.py handles the Vector + Cypher logic
        graph_data = retriever.retrieve_context(intent) 
        
        return {"graph_context": graph_data}
    except Exception as e:
        logger.error(f"Custom Retrieval failed: {e}")
        return {"graph_context": "Database retrieval failed.", "error": str(e)}

def generate_response_node(state: AgentState):
    """The 'Speaker'. Uses Groq + Graph Data to formulate the final YAML answer."""
    try:
        llm = get_speaker_llm()
        chain = RESPONSE_PROMPT | llm
        
        # If there was an earlier error, inform the user gracefully
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
        return {"messages": [AIMessage(content="I encountered an error generating the final YAML.")]}

def save_memory_node(state: AgentState):
    """Saves the completed conversation turn to Zep."""
    try:
        zep = ZepMemoryStore()
        user_msg = state["question"]
        ai_msg = state["messages"][-1].content if state["messages"] else ""
        zep.add_message(session_id="default_session", user_msg=user_msg, ai_msg=ai_msg)
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")
    return {}

# --- Graph Construction ---
def create_agent_graph():
    """Compiles the LangGraph state machine."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("memory", retrieve_memory_node)
    workflow.add_node("thinker", extract_intent_node)
    workflow.add_node("retriever", execute_retrieval_node)
    workflow.add_node("speaker", generate_response_node)
    workflow.add_node("saver", save_memory_node)
    
    workflow.set_entry_point("memory")
    workflow.add_edge("memory", "thinker")
    workflow.add_edge("thinker", "retriever")
    workflow.add_edge("retriever", "speaker")
    workflow.add_edge("speaker", "saver")
    workflow.add_edge("saver", END)
    
    return workflow.compile()