# =============================================================================
# app/core/config.py: central settings for the whole application
# -----------------------------------------------------------------------------
# Every tunable value (API keys, model names, Pinecone index, retry limits,
# file paths) lives here in ONE place. Values are read from environment
# variables or from the `.env` file in the project root, so secrets never have
# to be written into the code.
#
# Example: the line `GROQ_API_KEY=gsk_...` in `.env` fills `groq_api_key`
# below (pydantic-settings matches names case-insensitively).
# =============================================================================
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root folder. This file is app/core/config.py, so we go up two levels
# (core -> app -> project root). Used to build absolute paths below.
BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # ---- General ------------------------------------------------------------
    app_name: str = "Enterprise IT Support Agentic RAG Copilot"  # shown in the UI and /api/health
    app_env: str = "development"

    # ---- Which AI providers to use -------------------------------------------
    # LLM = the model that routes, grades, rewrites and writes answers.
    # Embeddings = the model that turns text into vectors for Pinecone.
    llm_provider: str = "groq"  # groq | openai
    embedding_provider: str = "huggingface"  # huggingface | openai

    # ---- API keys and model names --------------------------------------------
    groq_api_key: str = ""                  # free key from console.groq.com
    groq_model: str = "openai/gpt-oss-20b"  # Groq-hosted model used when llm_provider=groq
    openai_api_key: str = ""                # only needed if a provider is set to "openai"
    tavily_api_key: str = ""                # web search used as a fallback
    pinecone_api_key: str = ""              # vector database holding the company documents

    # ---- Pinecone vector database --------------------------------------------
    pinecone_index_name: str = "fde-it-support-rag"  # the "table" that stores vectors
    pinecone_namespace: str = "company-it-kb"        # a partition inside that index

    # Embedding model. The default runs locally on your PC (free, 384 numbers
    # per chunk). Use "text-embedding-3-small" with embedding_provider=openai.
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_model: str = "gpt-4o-mini"  # used only when llm_provider=openai

    # ---- Agent behaviour -----------------------------------------------------
    top_k: int = 4        # how many document chunks to fetch from Pinecone per search
    max_retries: int = 1  # how many times the agent may rewrite the query and try again

    # ---- Security and file locations -----------------------------------------
    admin_api_key: str = "change-me"  # password required to upload documents via /api/ingest
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")    # SQLite log of every question
    upload_dir: str = str(BASE_DIR / "uploads")                 # where uploaded files are saved
    sample_kb_dir: str = str(BASE_DIR / "data" / "sample_kb")   # demo documents for ingest_sample_kb.py

    # Tell pydantic-settings to read the .env file and ignore unknown keys in it.
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")




# @lru_cache makes this return the SAME Settings object every time, so the
# .env file is read only once, no matter how many modules call get_settings().
@lru_cache
def get_settings() -> Settings:
    return Settings()
