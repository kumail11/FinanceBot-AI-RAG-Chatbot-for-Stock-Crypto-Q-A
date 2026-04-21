"""
================================================
FinanceBot - Data Service
================================================
CoinGecko + Alpha Vantage + Finnhub data fetch
FREE APIs!
"""

import httpx
import finnhub
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from cachetools import TTLCache
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import settings
from models.schemas import CryptoPrice, StockQuote, NewsArticle

# ============================================
# CACHE: API calls Saves Here(rate limits ke liye)
# TTL = 60 seconds (1 minute cache)
# ============================================

crypto_cache = TTLCache(maxsize=100, ttl=60)
stock_cache = TTLCache(maxsize=100, ttl=60)
news_cache = TTLCache(maxsize=50, ttl=300)

# Sentiment Analyzer (VADER - FREE, Local)
sentiment_analyzer = SentimentIntensityAnalyzer()

# ============================================
# CRYPTO DATA - CoinGecko (FREE, No Key Needed)
# Rate limit: 10-30 calls/minute
# ============================================

# Common cryto name to CoinGecko ID mapping
CRYPTO_ID_MAP = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana",
    "cardano": "cardano", "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "xrp": "ripple", "ripple": "ripple",
    "polkadot": "polkadot", "dot": "polkadot",
    "avalanche": "avalanche-2", "avax": "avalanche-2",
    "chainlink": "chainlink", "link": "chainlink",
    "polygon": "matic-network", "matic": "matic-network",
    "shiba": "shiba-inu", "shib": "shiba-inu",
    "litecoin": "litecoin", "ltc": "litecoin",
    "bnb": "binancecoin", "binance": "binancecoin",
    "tron": "tron", "trx": "tron",
    "pepe": "pepe", "sui": "sui",
}

async def get_crypto_price(crypto_name: str) -> Optional[CryptoPrice]:
    # Fetch data from CoinGecko real time price
    crypto_name = crypto_name.lower().strip()
    coin_id = CRYPTO_ID_MAP.get(crypto_name, crypto_name)

    # Check cache first
    cache_key = f"crypto_{coin_id}"
    if cache_key in crypto_cache:
        return crypto_cache[cache_key]
    
    try:
        url = f"{settings.COINGECKO_BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not data:
            return None
        
        coin = data[0]
        result = CryptoPrice(
            name=coin.get("name", ""),
            symbol=coin.get("symbol", "").upper(),
            current_price_usd=coin.get("current_price", 0),
            market_cap=coin.get("market_cap"),
            price_change_24h=coin.get("price_change_24h"),
            price_change_percentage_24h=coin.get("price_change_percentage_24h"),
            high_24h=coin.get("high_24h"),
            low_24h=coin.get("low_24h"),
            total_volume=coin.get("total_volume")
        )

        # Cache it
        crypto_cache[cache_key] = result
        return result
    
    except Exception as e:
        print(f"CoinGecko Error for {crypto_name}: {e}")
        return None
    

async def get_trending_crypto() -> list[dict]:
    # Fetch trending coins from CoinGecko
    cache_key = "trending_crypto"
    if cache_key in crypto_cache:
        return crypto_cache[cache_key]
    
    try:
        url = f"{settings.COINGECKO_BASE_URL}/search/trending"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        coins = []
        for item in data.get("coins", [])[:10]:
            coin = item.get("item", {})
            coins.append({
                "name": coin.get("name", ""),
                "symbol": coin.get("symbol", ""),
                "market_cap_rank": coin.get("market_cap_rank"),
                "price_btc": coin.get("price_btc", 0),
                "price_usdt": coin.get("price_usdt", 0),
            })

        crypto_cache[cache_key] = coins
        return coins
    
    except Exception as e:
        print(f"Trending Crypto Error: {e}")
        return []


async def get_crypto_market_overview() -> list[dict]:
    # Fetch top 10 coins market overview
    cache_key = "market_overview"
    if cache_key in crypto_cache:
        return crypto_cache[cache_key]
    
    try:
        url = f"{settings.COINGECKO_BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": "false"
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        overview = []
        for coin in data:
            overview.append({
                "name": coin.get("name"),
                "symbol": coin.get("symbol", "").upper(),
                "price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "change_24h": coin.get("price_change_percentage_24h"),
                "volume": coin.get("total_volume"),
            })

        crypto_cache[cache_key] = overview
        return overview
    
    except Exception as e:
        print(f"Market Overview Error: {e}")
        return []
    

# ============================================
# STOCK DATA - Alpha Vantage (FREE Key Required)
# Rate limit: 5 calls/minute, 500/day
# ============================================

async def get_stock_quote(symbol: str) -> Optional[StockQuote]:
    """
    Alpha Vantage se stock ka real-time quote fetch karo
    FREE tier: 25 calls/day
    """
    symbol = symbol.upper().strip()

    cache_key = f"stock_{symbol}"
    if cache_key in stock_cache:
        return stock_cache[cache_key]

    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.ALPHA_VANTAGE_API_KEY
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(settings.ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        # Debug: Print raw response
        print(f"📡 Alpha Vantage Raw Response for {symbol}: {data}")

        quote = data.get("Global Quote", {})

        # Rate limit ya empty response check
        if not quote or "05. price" not in quote:
            print(f"No quote data for {symbol}. Response: {data}")
            return None

        result = StockQuote(
            symbol=quote.get("01. symbol", symbol),
            price=float(quote.get("05. price", 0) or 0),
            change=float(quote.get("09. change", 0) or 0),
            change_percent=quote.get("10. change percent", "0%"),
            volume=int(float(quote.get("06. volume", 0) or 0)),
            high=float(quote.get("03. high", 0) or 0),
            low=float(quote.get("04. low", 0) or 0),
        )

        stock_cache[cache_key] = result
        return result

    except Exception as e:
        print(f"Alpha Vantage Error for {symbol}: {e}")
        return None


async def get_stock_overview(symbol: str) -> Optional[dict]:
    # Company overview from Alpha Vantage (P/E ratio, market cap etc)
    symbol = symbol.upper().strip()
    cache_key = f"overview_{symbol}"
    
    if cache_key in stock_cache:
        return stock_cache[cache_key]
    
    try:
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": settings.ALPHA_VANTAGE_API_KEY
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(settings.ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        if not data or "Symbol" not in data:
            return None
        
        result = {
            "symbol": data.get("Symbol"),
            "name": data.get("Name"),
            "description": data.get("Description", "")[:300],
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "eps": data.get("EPS"),
            "dividend_yield": data.get("DividendYield"),
            "52_week_high": data.get("52WeekHigh"),
            "52_week_low": data.get("52WeekLow"),
            "50_day_avg": data.get("50DayMovingAverage"),
            "200_day_avg": data.get("200DayMovingAverage"),
            "profit_margin": data.get("ProfitMargin"),
            "revenue": data.get("RevenueTTM"),
        }

        stock_cache[cache_key] = result
        return result
    
    except Exception as e:
        print(f"Alpha Vantage Overview Error for {symbol}: {e}")
        return None
    

# ============================================
# NEWS DATA - Finnhub (FREE Key)
# + VADER Sentiment Analysis (FREE, Local)
# ============================================

def analyze_sentiment(text: str) -> tuple[str, float]:
    # Analyze sentiment using VADER and it returns (label, score)
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.15:
      return "bullish 🟢", compound
    elif compound <= -0.15:
        return "bearish 🔴", compound
    else:
        return "neutral 🟡", compound
    

async def get_company_news(symbol: str, days_back: int = 7) -> list[NewsArticle]:
    # Fetch company news from Finnhub + VADER Sentiment
    symbol = symbol.upper().strip()
    cache_key = f"news_{symbol}"
    
    if cache_key in news_cache:
        return news_cache[cache_key]
    
    try:
        finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        date_to = datetime.now().strftime("%Y-%m-%d")
        date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        news_data = finnhub_client.company_news(symbol, _from=date_from, to=date_to)

        articles = []
        for article in news_data[:10]: # Top 10 News
            headline = article.get("headline", "")
            summary = article.get("summary", "")

            # Sentiment Analysis (VADER - Local)
            text_to_analyze = f"{headline}. {summary}"
            sentiment_label, sentiment_score = analyze_sentiment(text_to_analyze)

            articles.append(NewsArticle(
                headline=headline,
                summary=summary[:200],
                source=article.get("source", "Unknown"),
                url=article.get("url", ""),
                datetime=datetime.fromtimestamp(
                    article.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
                sentiment=sentiment_label,
                sentiment_score=round(sentiment_score, 3)
            ))

        news_cache[cache_key] = articles
        return articles
    
    except Exception as e:
        print(f"Finnhub News Error for {symbol}: {e}")
        return []
    

async def get_market_news() -> list[NewsArticle]:
    # Fetch general market news
    cache_key = "market_news"
    
    if cache_key in news_cache:
        return news_cache[cache_key]
    
    try:
        finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        news_data = finnhub_client.general_news("general", min_id=0)

        articles = []
        for article in news_data[:10]:
            headline = article.get("headline", "")
            summary = article.get("summary", "")
            sentiment_label, sentiment_score = analyze_sentiment(f"{headline}. {summary}")

            articles.append(NewsArticle(
                headline=headline,
                summary=summary[:200],
                source=article.get("source", "Unknown"),
                url=article.get("url", ""),
                datetime=datetime.fromtimestamp(
                    article.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
                sentiment=sentiment_label,
                sentiment_score=round(sentiment_score, 3)
            ))

        news_cache[cache_key] = articles
        return articles
    
    except Exception as e:
        print(f"Market News Error: {e}")
        return []