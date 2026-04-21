"""
Finnhub News + VADER Sentiment — Quick Test
Run: python test_news.py
"""

import asyncio
from services.data_service import (
  get_company_news,
  get_market_news,
  analyze_sentiment,
)

DELAY = 3  # Finnhub: 60 calls/minute — fast!

async def test_all():

  # ==========================================
  # TEST 1: VADER Sentiment Analysis (Local)
  # ==========================================
  print("=" * 60)
  print("TEST 1: analyze_sentiment (VADER — Local, No API)")
  print("=" * 60)

  test_headlines = [
      "Bitcoin surges to all-time high as institutional investors pile in",
      "Tesla stock crashes 15% after disappointing earnings report",
      "Apple announces new product line at annual event",
      "Market fears grow as inflation data exceeds expectations",
      "Ethereum upgrade successfully completed, network stable",
      "Federal Reserve signals aggressive rate hikes ahead",
      "Google reports record-breaking quarterly revenue",
      "Crypto market faces major sell-off amid regulatory concerns",
  ]

  for headline in test_headlines:
      sentiment, score = analyze_sentiment(headline)
      print(f"  {sentiment}  ({score:+.3f})  →  {headline}")

  print()
  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 2: Company News (AAPL)
  # ==========================================
  print("=" * 60)
  print("TEST 2: get_company_news (AAPL)")
  print("=" * 60)

  news = await get_company_news("AAPL")
  if news:
      print(f"  📰 Found {len(news)} articles for AAPL:\n")
      for i, article in enumerate(news[:5], 1):
          print(f"""  {i}. {article.sentiment} ({article.sentiment_score:+.3f})
   📰 {article.headline}
   📝 {article.summary[:120]}...
   🔗 {article.source} | {article.datetime}
          """)
  else:
      print("  FAILED: AAPL news not found!\n")

  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 3: Company News (TSLA)
  # ==========================================
  print("=" * 60)
  print("TEST 3: get_company_news (TSLA)")
  print("=" * 60)

  news = await get_company_news("TSLA")
  if news:
      print(f"  📰 Found {len(news)} articles for TSLA:\n")
      for i, article in enumerate(news[:5], 1):
          print(f"""  {i}. {article.sentiment} ({article.sentiment_score:+.3f})
   📰 {article.headline}
   📝 {article.summary[:120]}...
   🔗 {article.source} | {article.datetime}
          """)
  else:
      print("  FAILED: TSLA news not found!\n")

  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 4: Company News (NVDA)
  # ==========================================
  print("=" * 60)
  print("TEST 4: get_company_news (NVDA)")
  print("=" * 60)

  news = await get_company_news("NVDA")
  if news:
      print(f"  📰 Found {len(news)} articles for NVDA:\n")
      for i, article in enumerate(news[:5], 1):
          print(f"""  {i}. {article.sentiment} ({article.sentiment_score:+.3f})
   📰 {article.headline}
   🔗 {article.source} | {article.datetime}
          """)
  else:
      print("  FAILED: NVDA news not found!\n")

  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 5: General Market News
  # ==========================================
  print("=" * 60)
  print("TEST 5: get_market_news (General)")
  print("=" * 60)

  news = await get_market_news()
  if news:
      print(f"  📰 Found {len(news)} general market articles:\n")

      bullish_count = sum(1 for a in news if "bullish" in (a.sentiment or ""))
      bearish_count = sum(1 for a in news if "bearish" in (a.sentiment or ""))
      neutral_count = sum(1 for a in news if "neutral" in (a.sentiment or ""))

      print(f"  📊 Sentiment Summary: 🟢 Bullish: {bullish_count} | 🔴 Bearish: {bearish_count} | 🟡 Neutral: {neutral_count}\n")

      for i, article in enumerate(news[:5], 1):
          print(f"""  {i}. {article.sentiment} ({article.sentiment_score:+.3f})
   📰 {article.headline}
   🔗 {article.source} | {article.datetime}
          """)
  else:
      print("  FAILED: Market news not found!\n")

  print("=" * 60)
  print("ALL NEWS TESTS COMPLETE!")
  print("=" * 60)

asyncio.run(test_all())