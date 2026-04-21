"""
================================================
FinanceBot - RAG Service
================================================
Retrieval Augmented Generation Pipeline:
1. Financial knowledge ChromaDB mein store hota hai
2. User query aati hai → relevant docs retrieve hoti hain
3. Real-time data + retrieved docs = context
4. LLM se answer generate hota hai
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import Optional

from config import settings

# ============================================
# EMBEDDINGS — Local, Free
# Model: all-MiniLM-L6-v2 (fast + accurate)
# ============================================

_embeddings = None

def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Free local embeddings — sentence-transformers
    Pehli baar load hoga, phir cache mein rahega
    """
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings


# ============================================
# VECTOR STORE — ChromaDB (Local, Free)
# ============================================

_vector_store = None

def get_vector_store() -> Chroma:
    """ChromaDB vector store initialize karo"""
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
    return _vector_store


# ============================================
# FINANCIAL KNOWLEDGE BASE
# Yeh knowledge seed karo ChromaDB mein
# ============================================

FINANCE_KNOWLEDGE = [
  # --- Crypto Fundamentals ---
  {
      "content": "Bitcoin (BTC) is a decentralized digital currency created in 2009 by Satoshi Nakamoto. It uses proof-of-work consensus. Bitcoin has a maximum supply of 21 million coins. The Bitcoin halving occurs approximately every 4 years, reducing mining rewards by 50%. Key metrics: hash rate, difficulty, mempool size. Bitcoin is often called 'digital gold' and is considered a store of value.",
      "metadata": {"category": "crypto", "topic": "bitcoin", "type": "fundamental"}
  },
  {
      "content": "Ethereum (ETH) is a decentralized platform for smart contracts and dApps. It transitioned from Proof of Work to Proof of Stake (The Merge, Sep 2022). Key metrics: gas fees, TVL (Total Value Locked), staking APR. Ethereum's EIP-1559 introduced base fee burning, making ETH potentially deflationary. Major use cases: DeFi, NFTs, Layer 2 solutions.",
      "metadata": {"category": "crypto", "topic": "ethereum", "type": "fundamental"}
  },
  {
      "content": "DeFi (Decentralized Finance) allows financial services without intermediaries. Key concepts: TVL, yield farming, liquidity pools, AMMs (Automated Market Makers), lending/borrowing protocols. Major DeFi protocols: Aave, Uniswap, Compound, MakerDAO. Risks: smart contract bugs, impermanent loss, rug pulls, regulatory uncertainty.",
      "metadata": {"category": "crypto", "topic": "defi", "type": "educational"}
  },
  {
      "content": "Crypto market indicators: Fear & Greed Index (0-100), Bitcoin Dominance (BTC.D), Total Market Cap, Trading Volume, RSI (Relative Strength Index), MACD. Bull market signals: increasing volume, higher lows, positive sentiment. Bear market signals: declining volume, lower highs, negative sentiment, increasing fear index.",
      "metadata": {"category": "crypto", "topic": "indicators", "type": "technical"}
  },

  # --- Stock Market Fundamentals ---
  {
      "content": "P/E Ratio (Price-to-Earnings): Share price / EPS. Low P/E may indicate undervaluation; high P/E may indicate growth expectations. Average S&P 500 P/E is ~20-25. Forward P/E uses estimated future earnings. Trailing P/E uses last 12 months. Compare P/E within same sector for accuracy.",
      "metadata": {"category": "stocks", "topic": "pe_ratio", "type": "fundamental"}
  },
  {
      "content": "Key stock metrics: EPS (Earnings Per Share), P/E Ratio, Market Cap, Revenue, Profit Margin, ROE (Return on Equity), Debt-to-Equity, Dividend Yield, Free Cash Flow. For growth stocks: revenue growth rate, TAM (Total Addressable Market). For value stocks: P/B ratio, dividend history.",
      "metadata": {"category": "stocks", "topic": "metrics", "type": "fundamental"}
  },
  {
      "content": "Technical Analysis basics: Support and Resistance levels, Moving Averages (50-day, 200-day), RSI (oversold <30, overbought >70), MACD (signal crossovers), Bollinger Bands, Volume analysis. Golden Cross: 50-day MA crosses above 200-day MA (bullish). Death Cross: opposite (bearish).",
      "metadata": {"category": "stocks", "topic": "technical_analysis", "type": "technical"}
  },
  {
      "content": "Major stock market indices: S&P 500 (top 500 US companies), NASDAQ (tech-heavy), Dow Jones (30 large-cap), Russell 2000 (small-cap). Sectors: Technology, Healthcare, Finance, Energy, Consumer, Industrial, Real Estate, Utilities, Materials, Communication.",
      "metadata": {"category": "stocks", "topic": "indices", "type": "educational"}
  },

  # --- Trading Strategies ---
  {
      "content": "Dollar Cost Averaging (DCA): Invest a fixed amount at regular intervals regardless of price. Reduces impact of volatility. Best for long-term investors. Example: invest $100 in BTC every week. Studies show DCA often outperforms lump-sum investing in volatile markets.",
      "metadata": {"category": "general", "topic": "dca", "type": "strategy"}
  },
  {
      "content": "Risk Management: Never invest more than you can afford to lose. Diversification across assets and sectors. Stop-loss orders to limit downside. Position sizing: risk only 1-2% of portfolio per trade. The 60/40 portfolio: 60% stocks, 40% bonds (traditional). For crypto: consider 5-10% of total portfolio allocation.",
      "metadata": {"category": "general", "topic": "risk_management", "type": "strategy"}
  },

  # --- Macro Economics ---
  {
      "content": "Federal Reserve interest rates affect all markets. Rate hikes = stronger dollar, lower stock/crypto prices typically. Rate cuts = weaker dollar, higher risk asset prices. CPI (Consumer Price Index) measures inflation. Key events: FOMC meetings, Non-Farm Payrolls, GDP reports. 'Don't fight the Fed' is a common investing adage.",
      "metadata": {"category": "general", "topic": "macro", "type": "educational"}
  },
  {
      "content": "Crypto regulation landscape: US SEC classifies most tokens as securities. EU's MiCA regulation provides framework. UAE and Singapore are crypto-friendly jurisdictions. Key risks: regulatory crackdowns, exchange bans, stablecoin regulations. Bitcoin ETFs approved in US (Jan 2024) were a major milestone.",
      "metadata": {"category": "crypto", "topic": "regulation", "type": "educational"}
  }
]


def seed_knowledge_base():
    """
    Financial knowledge base ko ChromaDB mein seed karo
    Yeh sirf ek baar run hoga (startup pe)
    """
    vector_store = get_vector_store()

    # Check if already seeded
    existing = vector_store._collection.count()
    if existing > 0:
        print(f"✅ Knowledge base already has {existing} documents. Skipping seed.")
        return

    print("📚 Seeding financial knowledge base...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " "]
    )

    documents = []
    for item in FINANCE_KNOWLEDGE:
        chunks = text_splitter.split_text(item["content"])
        for chunk in chunks:
            documents.append(Document(
                page_content=chunk,
                metadata=item["metadata"]
            ))

    vector_store.add_documents(documents)
    print(f"✅ Seeded {len(documents)} documents into ChromaDB!")

def retrieve_relevant_knowledge(query: str, top_k: int = 3) -> list[str]:
    """
    User query ke liye relevant knowledge retrieve karo
    ChromaDB se similarity search
    """
    vector_store = get_vector_store()

    try:
        results = vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"❌ Retrieval Error: {e}")
        return []

def add_knowledge(content: str, metadata: dict = None):
    """
    Naya knowledge add karo ChromaDB mein
    (Future use: dynamic knowledge updates)
    """
    vector_store = get_vector_store()
    metadata = metadata or {"category": "general", "type": "dynamic"}

    doc = Document(page_content=content, metadata=metadata)
    vector_store.add_documents([doc])
    print(f"✅ Added new knowledge: {content[:50]}...")