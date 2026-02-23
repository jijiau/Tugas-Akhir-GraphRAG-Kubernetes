import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    
    # Zep Memory
    zep_api_key: str
    zep_base_url: str
    
    # Multi-Agent LLMs
    openai_api_key: str      # For "Thinker" (Cypher Generation)
    groq_api_key: str        # For "Speaker" (Response & Intent)
    
    # Model Names
    thinker_model: str = "gpt-4o-mini"
    speaker_model: str = "llama3-8b-8192"
    
    # Project
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()