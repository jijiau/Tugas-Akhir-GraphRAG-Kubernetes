from typing import TypedDict, List, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import operator
import logging

from src.chatbot.llm_factory import get_thinker_llM, get_speaker_llm
from src.chatbot.prompts import CYPHER_PROMPT, RESPONSE_PROMPT
from src.graph.neo4j_client import Neo4jClient
from src.memory.zep_store import ZepMemoryStore

logger = logging.getLogger(__name__)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    graph_context: str
    cypher_query: str
    query_result: str
    chat_history: str
    error: Optional[str]

# --- Nodes ---
def retrieve_memory_node(state: AgentState):
    """Fetches chat history from Zep."""
    try:
        zep = ZepMemoryStore()
        # Get last 5 turns for context
        history = zep.get_history(session_id="default_session", limit=5)
        return {"chat_history": history}
    except Exception as e:
        logger.warning(f"Zep memory failed: {e}")
        return {"chat_history": "No history available."}

def generate_cypher_node(state: AgentState):
    """Uses OpenAI (Thinker) to write Cypher. Includes Fallback."""
    try:
        llm = get_thinker_llm()
        chain = CYPHER_PROMPT | llm
        response = chain.invoke({
            "question": state["question"],
            "graph_context_summary": "K8s Resources, Endpoints, Fields"
        })
        return {"cypher_query": response.content.strip()}
    except Exception as e:
        logger.error(f"OpenAI Cypher Gen failed: {e}. Falling back to Groq.")
        # Fallback Mechanism
        try:
            llm = get_speaker_llm() # Use Groq as backup
            chain = CYPHER_PROMPT | llm
            response = chain.invoke({
                "question": state["question"],
                "graph_context_summary": "K8s Resources, Endpoints, Fields"
            })
            return {"cypher_query": response.content.strip()}
        except Exception as fallback_err:
            return {"error": f"Failed to generate query: {fallback_err}"}

def execute_cypher_node(state: AgentState):
    """Runs Cypher on Neo4j."""
    if state.get("error"):
        return {"query_result": "Error occurred in previous step."}
    
    try:
        db = Neo4jClient()
        # Security: Basic sanitization could be added here
        result = db.execute_query(state["cypher_query"])
        # Convert result to string for LLM
        data = [record.data() for record in result]
        return {"query_result": str(data)}
    except Exception as e:
        logger.error(f"Neo4j Execution failed: {e}")
        return {"query_result": "Database execution failed.", "error": str(e)}

def generate_response_node(state: AgentState):
    """Uses Groq (Speaker) to formulate final answer."""
    try:
        llm = get_speaker_llm()
        chain = RESPONSE_PROMPT | llm
        response = chain.invoke({
            "chat_history": state["chat_history"],
            "retrieved_data": state["query_result"],
            "question": state["question"]
        })
        return {"messages": [AIMessage(content=response.content)]}
    except Exception as e:
        logger.error(f"Response Gen failed: {e}")
        return {"messages": [AIMessage(content="I encountered an error generating the response.")]}

def save_memory_node(state: AgentState):
    """Saves conversation to Zep."""
    try:
        zep = ZepMemoryStore()
        # Extract last user and AI message
        user_msg = state["question"]
        ai_msg = state["messages"][-1].content if state["messages"] else ""
        zep.add_message(session_id="default_session", user_msg=user_msg, ai_msg=ai_msg)
    except Exception as e:
        logger.warning(f"Failed to save memory: {e}")
    return {}

# --- Graph Construction ---
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("memory", retrieve_memory_node)
    workflow.add_node("thinker", generate_cypher_node)
    workflow.add_node("executor", execute_cypher_node)
    workflow.add_node("speaker", generate_response_node)
    workflow.add_node("saver", save_memory_node)
    
    # Add Edges
    workflow.set_entry_point("memory")
    workflow.add_edge("memory", "thinker")
    workflow.add_edge("thinker", "executor")
    workflow.add_edge("executor", "speaker")
    workflow.add_edge("speaker", "saver")
    workflow.add_edge("saver", END)
    
    return workflow.compile()