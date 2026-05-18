from langchain_openai import ChatOpenAI
from src.config.settings import settings

def get_thinker_llm():
    """
    Returns the 'Thinker' model (OpenAI).
    Why: Higher reasoning capability for Cypher query generation.
    """
    return ChatOpenAI(
        model=settings.thinker_model,
        temperature=0.0, # Deterministic for code gen
        api_key=settings.openai_api_key,
        max_retries=3,   # retry on transient connection errors
        timeout=30,      # prevent indefinite hangs
    )

def get_speaker_llm():
    """
    Returns the 'Speaker' model (OpenAI GPT-4o-mini).
    Why: Better instruction following and lower hallucination rate than Groq llama.
    """
    return ChatOpenAI(
        model=settings.speaker_model,
        temperature=0.1,
        api_key=settings.openai_api_key,
        max_retries=2,
        timeout=30,
    )