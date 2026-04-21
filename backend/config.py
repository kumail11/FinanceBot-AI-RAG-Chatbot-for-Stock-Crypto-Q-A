# =====================================================
# FinanceBot - Configuration Manager
# All keys and settings can be managed from this file
# =====================================================

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    # ---- Groq (Fast LLM) ----
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ---- CoinGecko (Free Crypto Data) ----
    COINGECKO_BASE_URL: str = os.getenv("COINGECKO_BASE_URL", "")

    # ---- Alpha Vantage (Free Stock Data) ----
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"

    # ---- Finnhub (Free News Data) ----
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # ---- ChromaDB ----
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "finance_knowledge")

    # ---- App ----
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()