"""
================================================
FinanceBot — AI RAG Chatbot for Stock/Crypto
================================================

Created by: Muhammad Kumail
GitHub: https://github.com/kumail11
Linkedin: https://www.linkedin.com/in/mohammad-kumail786/
Tech Stack: FastAPI + LangChain + ChromaDB + Free APIs

Free APIs Used:
- CoinGecko (Crypto Data)
- Alpha Vantage (Stock Data)
- Finnhub (News)
- OpenRouter/Groq (LLM)
- VADER (Sentiment - Local)
- HuggingFace Embeddings (Local)

Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import uvicorn

from config import settings
from models.schemas import ChatRequest, ChatResponse, HealthResponse
from services.chat_service import process_chat, chat_sessions
from services.rag_service import seed_knowledge_base
from services.data_service import (
  get_crypto_price,
  get_stock_quote,
  get_trending_crypto,
  get_crypto_market_overview,
  get_company_news,
  get_market_news,
)

# ============================================
# APP LIFESPAN — Startup & Shutdown
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
  """App start hone pe knowledge base seed karo"""
  print("🚀 FinanceBot starting up...")
  print("📚 Initializing knowledge base...")
  seed_knowledge_base()
  print("✅ FinanceBot is ready!")
  yield
  print("👋 FinanceBot shutting down...")

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
  title="FinanceBot API",
  description="AI-powered RAG Chatbot for Stock & Crypto Q&A",
  version="1.0.0",
  lifespan=lifespan,
)

# CORS — Frontend se connect karne ke liye
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Production mein specific domain use karo
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# ============================================
# ROUTES
# ============================================

# ---- Health Check ----
@app.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
  """API health check"""
  return HealthResponse(
      status="healthy",
      version="1.0.0",
      services={
          "llm": "OpenRouter (Free)",
          "crypto_data": "CoinGecko (Free)",
          "stock_data": "Alpha Vantage (Free)",
          "news": "Finnhub (Free)",
          "vector_store": "ChromaDB (Local)",
          "embeddings": "HuggingFace (Local)",
          "sentiment": "VADER (Local)",
      }
  )

# ---- MAIN CHAT ENDPOINT ----
@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
  """
  🤖 Main chat endpoint
  
  User question bhejo → AI answer milega with real-time data!
  
  Example questions:
  - "What's the price of Bitcoin?"
  - "Should I buy TSLA?"
  - "What's Tesla's P/E ratio?"
  - "Show me trending crypto"
  - "Latest news for AAPL"
  - "What is DeFi?"
  - "BTC ka price kya hai?"
  """
  try:
      response = await process_chat(request)
      return response
  except Exception as e:
      raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# ---- CRYPTO ENDPOINTS ----
@app.get("/api/crypto/{coin_id}", tags=["Crypto"])
async def get_crypto(coin_id: str):
  """Specific crypto ka real-time price"""
  data = await get_crypto_price(coin_id)
  if not data:
      raise HTTPException(status_code=404, detail=f"Crypto '{coin_id}' not found")
  return data

@app.get("/api/crypto/trending/list", tags=["Crypto"])
async def trending_crypto():
  """Trending cryptocurrencies"""
  return await get_trending_crypto()

@app.get("/api/crypto/market/overview", tags=["Crypto"])
async def market_overview():
  """Top 10 crypto market overview"""
  return await get_crypto_market_overview()

# ---- STOCK ENDPOINTS ----
@app.get("/api/stock/{symbol}", tags=["Stocks"])
async def get_stock(symbol: str):
  """Specific stock ka real-time quote"""
  data = await get_stock_quote(symbol)
  if not data:
      raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found")
  return data

# ---- NEWS ENDPOINTS ----
@app.get("/api/news/{symbol}", tags=["News"])
async def get_news(symbol: str):
  """Company-specific news with sentiment"""
  return await get_company_news(symbol)

@app.get("/api/news", tags=["News"])
async def general_news():
  """General market news"""
  return await get_market_news()

# ---- SESSION MANAGEMENT ----
@app.delete("/api/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str):
  """Chat history clear karo"""
  if session_id in chat_sessions:
      del chat_sessions[session_id]
      return {"message": "Session cleared successfully"}
  raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/session/{session_id}/history", tags=["Session"])
async def get_history(session_id: str):
  """Chat history retrieve karo"""
  if session_id in chat_sessions:
      return {"session_id": session_id, "messages": chat_sessions[session_id]}
  return {"session_id": session_id, "messages": []}

# ---- SERVE FRONTEND ----
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
  @app.get("/chat", tags=["Frontend"])
  async def serve_frontend():
      return FileResponse(os.path.join(frontend_path, "index.html"))

# ============================================
# RUN
# ============================================
if __name__ == "__main__":
  uvicorn.run(
      "main:app",
      host=settings.APP_HOST,
      port=settings.APP_PORT,
      reload=settings.DEBUG,
  )