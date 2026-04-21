"""
================================================
FinanceBot - Helper Utilities
================================================
"""

import re
from datetime import datetime

def format_large_number(num: float) -> str:
  """Large numbers ko readable format mein convert karo"""
  if num >= 1_000_000_000_000:
      return f"${num / 1_000_000_000_000:.2f}T"
  elif num >= 1_000_000_000:
      return f"${num / 1_000_000_000:.2f}B"
  elif num >= 1_000_000:
      return f"${num / 1_000_000:.2f}M"
  elif num >= 1_000:
      return f"${num / 1_000:.2f}K"
  else:
      return f"${num:.2f}"

def extract_tickers(text: str) -> list[str]:
  """Text se stock tickers extract karo"""
  pattern = r'\$([A-Z]{1,5})\b'
  return re.findall(pattern, text)

def get_greeting() -> str:
  """Time-based greeting"""
  hour = datetime.now().hour
  if hour < 12:
      return "Good Morning! ☀️"
  elif hour < 17:
      return "Good Afternoon! 🌤️"
  elif hour < 21:
      return "Good Evening! 🌆"
  else:
      return "Good Night! 🌙"