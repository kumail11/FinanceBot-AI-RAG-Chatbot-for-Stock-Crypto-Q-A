"""
Alpha Vantage Stock Functions — Quick Test
Run: python test_stocks.py
"""

import asyncio
from services.data_service import (
  get_stock_quote,
  get_stock_overview,
)

DELAY = 15  # Alpha Vantage: 5 calls/minute — safe delay

async def test_all():

  # ==========================================
  # TEST 1: Stock Quote (Single)
  # ==========================================
  print("=" * 60)
  print("TEST 1: get_stock_quote (Single — AAPL)")
  print("=" * 60)

  data = await get_stock_quote("AAPL")
  if data:
      print(f"""
✅ {data.symbol}
   💰 Price:          ${data.price:.2f}
   📈 Change:         ${data.change:.2f} ({data.change_percent})
   🔺 High:           ${data.high:.2f}
   🔻 Low:            ${data.low:.2f}
   📦 Volume:         {data.volume:,}
      """)
  else:
      print("  FAILED: AAPL data not found!\n")

  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 2: Multiple Stock Quotes
  # ==========================================
  print("=" * 60)
  print("TEST 2: get_stock_quote (Multiple Stocks)")
  print("=" * 60)

  stocks = ["TSLA", "MSFT", "GOOGL"]

  for symbol in stocks:
      data = await get_stock_quote(symbol)
      if data:
          change = data.change or 0
          emoji = "🟢" if change > 0 else "🔴"
          print(f"  {emoji} {data.symbol}: ${data.price:.2f} ({data.change_percent})")
      else:
          print(f"  FAILED: {symbol} — Data not found!")

      await asyncio.sleep(DELAY)

  print()

  # ==========================================
  # TEST 3: Stock Overview (Company Fundamentals)
  # ==========================================
  print("=" * 60)
  print("TEST 3: get_stock_overview (TSLA Fundamentals)")
  print("=" * 60)

  await asyncio.sleep(DELAY)

  overview = await get_stock_overview("TSLA")
  if overview:
      print(f"""
✅ {overview.get('name', 'N/A')} ({overview.get('symbol', 'N/A')})
   🏢 Sector:         {overview.get('sector', 'N/A')}
   🏭 Industry:       {overview.get('industry', 'N/A')}
   📊 Market Cap:     ${int(overview.get('market_cap', 0)):,}
   📈 P/E Ratio:      {overview.get('pe_ratio', 'N/A')}
   💵 EPS:            {overview.get('eps', 'N/A')}
   💰 Dividend Yield: {overview.get('dividend_yield', 'N/A')}
   🔺 52W High:       ${overview.get('52_week_high', 'N/A')}
   🔻 52W Low:        ${overview.get('52_week_low', 'N/A')}
   📊 Profit Margin:  {overview.get('profit_margin', 'N/A')}
   📝 Description:    {overview.get('description', 'N/A')}
      """)
  else:
      print("  FAILED: TSLA overview not found!\n")

  await asyncio.sleep(DELAY)

  # ==========================================
  # TEST 4: Stock Overview (AAPL)
  # ==========================================
  print("=" * 60)
  print("TEST 4: get_stock_overview (AAPL Fundamentals)")
  print("=" * 60)

  overview = await get_stock_overview("AAPL")
  if overview:
      print(f"""
✅ {overview.get('name', 'N/A')} ({overview.get('symbol', 'N/A')})
   🏢 Sector:         {overview.get('sector', 'N/A')}
   🏭 Industry:       {overview.get('industry', 'N/A')}
   📊 Market Cap:     ${int(overview.get('market_cap', 0)):,}
   📈 P/E Ratio:      {overview.get('pe_ratio', 'N/A')}
   💵 EPS:            {overview.get('eps', 'N/A')}
   🔺 52W High:       ${overview.get('52_week_high', 'N/A')}
   🔻 52W Low:        ${overview.get('52_week_low', 'N/A')}
      """)
  else:
      print("  FAILED: AAPL overview not found!\n")

  print("=" * 60)
  print("ALL STOCK TESTS COMPLETE!")
  print("=" * 60)

asyncio.run(test_all())