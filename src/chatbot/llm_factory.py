from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from src.config.settings import settings

def get_thinker_llm():
    """
    Returns the 'Thinker' model (OpenAI).
    Why: Higher reasoning capability for Cypher query generation.
    """
    return ChatOpenAI(
        model=settings.thinker_model,
        temperature=0.0, # Deterministic for code gen
        api_key=settings.openai_api_key
    )

def get_speaker_llm():
    """
    Returns the 'Speaker' model (Groq).
    Why: Low latency, low cost for natural language generation.
    """
    return ChatGroq(
        model=settings.speaker_model,
        temperature=0.3, # Slightly creative for conversation
        api_key=settings.groq_api_key
    )