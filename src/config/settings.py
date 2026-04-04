import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    
    # Multi-Agent LLMs
    openai_api_key: str      # For "Thinker" (Intent Extraction)
    groq_api_key: str        # For "Speaker" (Response)
    
    # Model Names
    thinker_model: str = "gpt-4o-mini"
    speaker_model: str = "llama-3.1-8b-instant"
    
    # Project
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"   # abaikan env vars lama (ZEP_API_KEY, dll) yang masih ada di .env

settings = Settings()