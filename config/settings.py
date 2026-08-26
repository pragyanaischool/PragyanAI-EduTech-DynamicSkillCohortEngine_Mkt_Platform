"""
Centralized settings manager reading from Streamlit Secrets (st.secrets).
"""

import os
import streamlit as st


def get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves a configuration key from st.secrets,
    falling back to os.environ if running outside active Streamlit context (e.g. CI/scripts).
    """
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


class Settings:
    # Groq LLM Settings
    GROQ_API_KEY: str = get_secret("GROQ_API_KEY", "")
    GROQ_MODEL: str = get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Storage & Persistence Paths
    DATABASE_PATH: str = get_secret("DATABASE_PATH", "storage/pragyanai.db")
    FAISS_INDEX_PATH: str = get_secret("FAISS_INDEX_PATH", "storage/vectors/faiss_index")

    # Business Logic Defaults
    MIN_QUORUM: int = int(get_secret("MIN_QUORUM", "5"))
    DEFAULT_PLATFORM_MARGIN_PCT: float = float(get_secret("PLATFORM_MARGIN_PCT", "20.0"))


settings = Settings()
