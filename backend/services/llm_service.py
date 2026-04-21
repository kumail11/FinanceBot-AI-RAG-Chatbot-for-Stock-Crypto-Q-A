"""
================================================
FinanceBot - LLM Service
================================================
LangChain
"""

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import Optional

from config import settings

# ============================================
# SYSTEM PROMPT — BOT personality rules
# ============================================

FINANCE_SYSTEM_PROMPT = """
    You are FinanceBot — an AI-powered financial assistant that provides 
    real-time data and intelligent analysis for stocks and cryptocurrencies.

    ## YOUR CAPABILITIES:
    - Real-time crypto prices (CoinGecko)
    - Stock quotes & company fundamentals (Alpha Vantage)
    - Financial news with sentiment analysis (Finnhub + VADER)
    - Market trends and analysis
    - Educational explanations of financial concepts

    ## YOUR RULES:
    1. ALWAYS use the real-time data provided in the context to answer questions
    2. NEVER make up prices or financial data — only use what's provided
    3. If data is not available, clearly say "I don't have real-time data for this"
    4. Add relevant emojis for better readability
    5. Provide balanced analysis — mention both risks and opportunities
    6. Include a disclaimer: "This is not financial advice" when giving opinions
    7. Format responses with headers, bullet points for clarity
    8. Keep responses concise but informative (200-400 words ideal)
    9. If user asks in Urdu/Roman Urdu, respond in the same language

    ## RESPONSE FORMAT:
    - Start with a direct answer to the question
    - Include relevant data points
    - Provide brief analysis
    - End with disclaimer if opinion-based
"""

def get_llm(provider: str = "groq") -> ChatOpenAI:
    if provider == "groq" and settings.GROQ_API_KEY:
        return ChatOpenAI(
            model=settings.GROQ_MODEL,
            openai_api_key=settings.GROQ_API_KEY,
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0.3,
            max_tokens=1024,
        )
    else:
        # Default: OpenRouter (FREE)
        return ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=0.3,
            max_tokens=1024,
            default_headers={
                "HTTP-Referer": "https://financebot.app",
                "X-Title": "FinanceBot"
            }
        )
    

async def generate_response(
    query: str,
    context: str,
    chat_history: list[dict] = None,
    provider: str = "groq"
    ) -> str:
    """
    LLM se response generate karo with context (RAG style)

    Args:
        query: User ka question
        context: Real-time data + knowledge base context
        chat_history: Previous messages
        provider: "openrouter" ya "groq"
    """
    llm = get_llm(provider)

    messages = [
        SystemMessage(content=FINANCE_SYSTEM_PROMPT),
    ]

    # Chat history add karo (last 10 messages)
    if chat_history:
        for msg in chat_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Current query with context
    augmented_query = f"""
    ## REAL-TIME DATA CONTEXT:
    {context}

    ## USER'S QUESTION:
    {query}

    Please answer the user's question using the real-time data provided above.
    If the data doesn't contain relevant information, say so clearly.
    """

    messages.append(HumanMessage(content=augmented_query))

    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return f"Sorry, I encountered an error generating a response. Please try again. Error: {str(e)[:100]}"
  