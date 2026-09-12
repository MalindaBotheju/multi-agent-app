"""
Real financial data check (Yahoo Finance via yfinance, no API key needed).

This is what makes the Validator agent's ticker/price checks *real* instead
of an LLM just guessing whether something "looks suspicious." We ask the
LLM to spot candidate ticker symbols in the research notes, then check each
one here against actual live data.
"""

import yfinance as yf


def check_ticker(ticker: str) -> str:
    """
    Looks up a ticker on Yahoo Finance and returns a short factual line,
    or a clear 'INVALID TICKER' message if it doesn't exist / has no data.
    """
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.get("last_price")
        currency = info.get("currency", "")
        if price is None:
            return f"{ticker}: INVALID TICKER or no live data available"
        return f"{ticker}: VERIFIED — current price {price} {currency}"
    except Exception as e:
        return f"{ticker}: INVALID TICKER or lookup failed ({e})"


def check_tickers(tickers: list[str]) -> str:
    """Checks a list of tickers and returns one line per ticker."""
    if not tickers:
        return "No tickers were mentioned to check."
    return "\n".join(check_ticker(t) for t in tickers)
