import asyncio
from services.data_service import(
    get_crypto_price,
    get_trending_crypto,
    get_crypto_market_overview
)

# Delay between API calls (seconds)
DELAY = 5
DELAY_NEW = 12

async def test_all():
    print("=" * 60)
    print("TEST 1: get_crypto_price")
    print("=" * 60)

    coins = ["bitcoin", "eth", "solana", "dogecoin"]

    for coin in coins:
        data = await get_crypto_price(coin)
        if data:
            print(f"""
            ✅ {data.name} ({data.symbol})
            💰 Price:      ${data.current_price_usd:,.2f}
            📈 24h Change: {data.price_change_percentage_24h:.2f}%
            🔺 High:       ${data.high_24h:,.2f}
            🔻 Low:        ${data.low_24h:,.2f}
            📊 Market Cap: ${data.market_cap:,.0f}
            📦 Volume:     ${data.total_volume:,.0f}
            """)
        else:
            print(f"FAILED: {coin} — Data not found!\n")

        await asyncio.sleep(DELAY)

    
    print("=" * 60)
    print("TEST 2: get_trending_crypto")
    print("=" * 60)

    await asyncio.sleep(DELAY)

    trending = await get_trending_crypto()
    if trending:
        for i, coin in enumerate(trending[:5], 1):
            print(f"  🔥 {i}. {coin['name']} ({coin['symbol']}) — Rank #{coin['market_cap_rank']}")
        print()
    else:
        print("FAILED: Trending data not found!\n")

    
    print("=" * 60)
    print("TEST 3: get_crypto_market_overview")
    print("=" * 60)

    await asyncio.sleep(DELAY_NEW)

    overview = await get_crypto_market_overview()
    if overview:
        for coin in overview:
            change = coin['change_24h'] or 0
            emoji = "🟢" if change > 0 else "🔴"
            print(f"  {emoji} {coin['name']} ({coin['symbol']}): ${coin['price']:,.2f} ({change:.2f}%)")
        print()
    else:
        print("FAILED: Market overview not found!\n")

    print("=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)


# RUN
asyncio.run(test_all())