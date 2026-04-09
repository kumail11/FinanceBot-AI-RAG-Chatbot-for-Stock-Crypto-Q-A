# ================================================
# FinanceBot - Pydantic Schemas
# ================================================
# Request/Response models for the API

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ---- Chat Models ----
class ChatRequest(BaseModel):
    # User Chat Message
    message: str = Field(..., min_length=1, max_length=2000, description="User question")
    session_id: Optional[str] = Field(default=None, description="Chat session ID for history")

class ChatResponse(BaseModel):
    # BOT Response
    answer: str = Field(..., description="AI generated answer")
    sources: list[str] = Field(default=[], description="Data sources used")
    data_used: Optional[dict] = Field(default=None, description="Real-time data used in answer")
    session_id: str = Field(..., description="Chat session ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ---- Crypto Models ----
class CryptoPrice(BaseModel):
    name: str
    symbol: str
    current_price_usd: float
    market_cap: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    total_volume: Optional[float] = None

# ---- Stock Models ----
class StockQuote(BaseModel):
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[str] = None
    volume: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None

# ---- News Models ----
class NewsArticle(BaseModel):
    headline: str
    summary: str
    source: str
    url: str
    datetime: str
    sentiment: Optional[str] = None  # bullish / bearish / neutral
    sentiment_score: Optional[float] = None

# ---- Health Check ----
class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    services: dict = {}