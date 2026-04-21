"""
================================================
FinanceBot - Chat Service (MAIN ORCHESTRATOR)
================================================
Yeh sab kuch connect karta hai:
1. User question analyze karo
2. Detect karo: Crypto? Stock? News? General?
3. Relevant APIs se data fetch karo
4. ChromaDB se knowledge retrieve karo
5. Sab combine karke LLM ko bhejo
6. Answer return karo

YEH FILE SABSE IMPORTANT HAI! 💪
"""

import re
import uuid
from typing import Optional
from datetime import datetime

from services.data_service import (
  get_crypto_price,
  get_stock_quote,
  get_stock_overview,
  get_company_news,
  get_market_news,
  get_trending_crypto,
  get_crypto_market_overview,
)
from services.rag_service import retrieve_relevant_knowledge
from services.llm_service import generate_response
from models.schemas import ChatRequest, ChatResponse

# ============================================
# CHAT HISTORY — In-memory (per session)
# Production mein Redis ya DB use karo
# ============================================
chat_sessions: dict[str, list[dict]] = {}

# ============================================
# INTENT DETECTION — User kya pooch raha hai?
# ============================================

# Common crypto names/symbols
CRYPTO_KEYWORDS = {
  "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "cardano", "ada",
  "dogecoin", "doge", "xrp", "ripple", "polkadot", "dot", "avalanche",
  "avax", "chainlink", "link", "polygon", "matic", "shiba", "shib",
  "litecoin", "ltc", "bnb", "binance", "tron", "trx", "pepe", "sui",
  "crypto", "coin", "token", "blockchain", "defi", "nft", "web3",
  "mining", "staking", "halving", "wallet"
}

# Common stock symbols/keywords
STOCK_KEYWORDS = {
  "stock", "share", "equity", "nasdaq", "s&p", "dow", "nyse",
  "dividend", "earnings", "revenue", "p/e", "pe ratio", "eps",
  "market cap", "ipo", "bull", "bear", "index", "etf",
  "fundamental", "technical analysis", "moving average"
}

# Common stock tickers (detect AAPL, TSLA, etc.)
STOCK_TICKER_PATTERN = r'\b([A-Z]{1,5})\b'

POPULAR_TICKERS = {
  "AAPL", "TSLA", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA",
  "AMD", "NFLX", "DIS", "JPM", "BAC", "V", "MA", "WMT", "KO",
  "PEP", "NKE", "INTC", "CRM", "PYPL", "SQ", "UBER", "ABNB",
  "COIN", "PLTR", "SNAP", "ROKU", "ZM", "SHOP", "SE", "BABA",
  "TSM", "SONY", "ORCL", "IBM", "CSCO", "QCOM", "TXN", "AVGO"
}

NEWS_KEYWORDS = {
  "news", "headline", "update", "latest", "today", "sentiment",
  "article", "report", "announcement", "khabar", "aaj"
}

TRENDING_KEYWORDS = {
  "trending", "hot", "popular", "top", "best", "worst",
  "gainers", "losers", "movers"
}

def detect_intent(query: str) -> dict:
  """
  User ka question analyze karke intent detect karo
  Returns: {
      "type": "crypto" | "stock" | "news" | "trending" | "general",
      "entities": ["BTC", "AAPL", etc.],
      "needs_price": True/False,
      "needs_news": True/False,
      "needs_overview": True/False,
  }
  """
  query_lower = query.lower()
  words = set(query_lower.split())

  intent = {
      "type": "general",
      "entities": [],
      "needs_price": False,
      "needs_news": False,
      "needs_overview": False,
      "needs_trending": False,
      "needs_market": False,
  }

  # Detect crypto entities
  crypto_found = []
  for keyword in CRYPTO_KEYWORDS:
      if keyword in query_lower:
          if keyword not in {"crypto", "coin", "token", "blockchain", "defi",
                           "nft", "web3", "mining", "staking", "halving", "wallet"}:
              crypto_found.append(keyword)
          intent["type"] = "crypto"

  # Detect stock entities
  stock_found = []
  # Check for explicit tickers
  potential_tickers = re.findall(STOCK_TICKER_PATTERN, query)
  for ticker in potential_tickers:
      if ticker in POPULAR_TICKERS:
          stock_found.append(ticker)
          intent["type"] = "stock"

  # Check for stock keywords
  for keyword in STOCK_KEYWORDS:
      if keyword in query_lower:
          intent["type"] = "stock"

  # Detect news intent
  for keyword in NEWS_KEYWORDS:
      if keyword in query_lower:
          intent["needs_news"] = True

  # Detect trending intent
  for keyword in TRENDING_KEYWORDS:
      if keyword in query_lower:
          intent["needs_trending"] = True

  # Detect price-related queries
  price_words = {"price", "cost", "worth", "value", "rate", "kitna", "kitnay", "kya hai"}
  if any(w in query_lower for w in price_words):
      intent["needs_price"] = True

  # Detect overview/fundamental queries
  overview_words = {"p/e", "pe ratio", "eps", "market cap", "revenue", "overview",
                   "fundamental", "company", "about", "detail", "info"}
  if any(w in query_lower for w in overview_words):
      intent["needs_overview"] = True

  # Detect market overview
  market_words = {"market", "overview", "overall", "global", "top coins", "top 10"}
  if any(w in query_lower for w in market_words):
      intent["needs_market"] = True

  intent["entities"] = crypto_found + stock_found
  return intent

# ============================================
# CONTEXT BUILDER — Data fetch + knowledge combine
# ============================================

async def build_context(query: str, intent: dict) -> tuple[str, list[str], dict]:
  """
  Intent ke basis pe relevant data fetch karo aur context banao
  
  Returns: (context_string, sources_list, data_dict)
  """
  context_parts = []
  sources = []
  data_used = {}

  # ---- 1. CRYPTO DATA ----
  if intent["type"] == "crypto":
      for entity in intent["entities"]:
          if intent["needs_price"] or True:  # Always fetch price for crypto
              price_data = await get_crypto_price(entity)
              if price_data:
                  context_parts.append(f"""
📊 {price_data.name} ({price_data.symbol}) — Real-Time Data:
• Current Price: ${price_data.current_price_usd:,.2f}
• 24h Change: {price_data.price_change_percentage_24h:.2f}% (${price_data.price_change_24h:,.2f})
• 24h High: ${price_data.high_24h:,.2f}
• 24h Low: ${price_data.low_24h:,.2f}
• Market Cap: ${price_data.market_cap:,.0f}
• 24h Volume: ${price_data.total_volume:,.0f}
""")
                  sources.append("CoinGecko (Real-time)")
                  data_used[f"crypto_{entity}"] = price_data.model_dump()

      # Trending crypto
      if intent["needs_trending"]:
          trending = await get_trending_crypto()
          if trending:
              trending_text = "\n🔥 Trending Cryptocurrencies:\n"
              for i, coin in enumerate(trending[:5], 1):
                  trending_text += f"  {i}. {coin['name']} ({coin['symbol']}) — Rank #{coin['market_cap_rank']}\n"
              context_parts.append(trending_text)
              sources.append("CoinGecko (Trending)")

      # Market overview
      if intent["needs_market"]:
          overview = await get_crypto_market_overview()
          if overview:
              market_text = "\n📈 Crypto Market Overview (Top 10):\n"
              for coin in overview:
                  change = coin['change_24h'] or 0
                  emoji = "🟢" if change > 0 else "🔴"
                  market_text += f"  {emoji} {coin['name']} ({coin['symbol']}): ${coin['price']:,.2f} ({change:.2f}%)\n"
              context_parts.append(market_text)
              sources.append("CoinGecko (Market Overview)")

  # ---- 2. STOCK DATA ----
  if intent["type"] == "stock":
      for entity in intent["entities"]:
          # Stock Quote
          if intent["needs_price"] or True:
              quote = await get_stock_quote(entity)
              if quote:
                  context_parts.append(f"""
📊 {entity} — Stock Quote:
• Price: ${quote.price:.2f}
• Change: ${quote.change:.2f} ({quote.change_percent})
• High: ${quote.high:.2f}
• Low: ${quote.low:.2f}
• Volume: {quote.volume:,}
""")
                  sources.append("Alpha Vantage (Real-time)")
                  data_used[f"stock_{entity}"] = quote.model_dump()

          # Company Overview (P/E, EPS, etc.)
          if intent["needs_overview"]:
              overview = await get_stock_overview(entity)
              if overview:
                  context_parts.append(f"""
🏢 {overview.get('name', entity)} — Company Overview:
• Sector: {overview.get('sector', 'N/A')}
• Industry: {overview.get('industry', 'N/A')}
• Market Cap: ${int(overview.get('market_cap', 0)):,}
• P/E Ratio: {overview.get('pe_ratio', 'N/A')}
• EPS: {overview.get('eps', 'N/A')}
• Dividend Yield: {overview.get('dividend_yield', 'N/A')}
• 52-Week High: ${overview.get('52_week_high', 'N/A')}
• 52-Week Low: ${overview.get('52_week_low', 'N/A')}
• Profit Margin: {overview.get('profit_margin', 'N/A')}
• Description: {overview.get('description', 'N/A')}
""")
                  sources.append("Alpha Vantage (Company Overview)")
                  data_used[f"overview_{entity}"] = overview

  # ---- 3. NEWS DATA ----
  if intent["needs_news"]:
      # Entity-specific news
      for entity in intent["entities"]:
          # For stocks, use ticker directly. For crypto, map to relevant ticker
          ticker = entity.upper() if entity.upper() in POPULAR_TICKERS else None
          if ticker:
              news = await get_company_news(ticker)
              if news:
                  news_text = f"\n📰 Latest News for {ticker}:\n"
                  for i, article in enumerate(news[:5], 1):
                      news_text += f"""
{i}. [{article.sentiment}] {article.headline}
   Source: {article.source} | {article.datetime}
   Summary: {article.summary}
"""
                  context_parts.append(news_text)
                  sources.append("Finnhub (News + VADER Sentiment)")

      # General market news if no specific entity
      if not intent["entities"]:
          news = await get_market_news()
          if news:
              news_text = "\n📰 Latest Market News:\n"
              for i, article in enumerate(news[:5], 1):
                  news_text += f"""
{i}. [{article.sentiment}] {article.headline}
   Source: {article.source} | {article.datetime}
"""
              context_parts.append(news_text)
              sources.append("Finnhub (Market News)")

  # ---- 4. KNOWLEDGE BASE (ChromaDB RAG) ----
  knowledge_docs = retrieve_relevant_knowledge(query, top_k=3)
  if knowledge_docs:
      knowledge_text = "\n📚 Knowledge Base:\n"
      for doc in knowledge_docs:
          knowledge_text += f"• {doc}\n"
      context_parts.append(knowledge_text)
      sources.append("Knowledge Base (ChromaDB)")

  # Combine all context
  full_context = "\n".join(context_parts) if context_parts else "No specific data available for this query."

  return full_context, sources, data_used

# ============================================
# MAIN CHAT FUNCTION
# ============================================

async def process_chat(request: ChatRequest) -> ChatResponse:
  """
  MAIN FUNCTION — User ka message process karo aur response do
  
  Flow:
  1. Session manage karo
  2. Intent detect karo
  3. Context build karo (data + knowledge)
  4. LLM se response generate karo
  5. History update karo
  6. Response return karo
  """

  # 1. Session Management
  session_id = request.session_id or str(uuid.uuid4())
  if session_id not in chat_sessions:
      chat_sessions[session_id] = []

  # 2. Intent Detection
  intent = detect_intent(request.message)
  print(f"🎯 Detected Intent: {intent}")

  # 3. Build Context (Real-time data + Knowledge)
  context, sources, data_used = await build_context(request.message, intent)
  print(f"📦 Context built with {len(sources)} sources")

  # 4. Generate Response via LLM
  answer = await generate_response(
      query=request.message,
      context=context,
      chat_history=chat_sessions[session_id],
      provider="groq"  # Change to "groq" for faster responses
  )

  # 5. Update Chat History
  chat_sessions[session_id].append({
      "role": "user",
      "content": request.message,
      "timestamp": datetime.now().isoformat()
  })
  chat_sessions[session_id].append({
      "role": "assistant",
      "content": answer,
      "timestamp": datetime.now().isoformat()
  })

  # Keep only last 20 messages per session
  if len(chat_sessions[session_id]) > 20:
      chat_sessions[session_id] = chat_sessions[session_id][-20:]

  # 6. Return Response
  return ChatResponse(
      answer=answer,
      sources=sources,
      data_used=data_used,
      session_id=session_id,
  )