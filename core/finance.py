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
            print(f"[finance] {ticker}: fast_info returned no last_price — {dict(info)!r}")
            return f"{ticker}: INVALID TICKER or no live data available"
        return f"{ticker}: VERIFIED — current price {price} {currency}"
    except Exception as e:
        print(f"[finance] {ticker}: check_ticker EXCEPTION: {type(e).__name__}: {e}")
        return f"{ticker}: INVALID TICKER or lookup failed ({e})"


def check_tickers(tickers: list[str]) -> str:
    """Checks a list of tickers and returns one line per ticker."""
    if not tickers:
        return "No tickers were mentioned to check."
    return "\n".join(check_ticker(t) for t in tickers)


def get_key_financials(ticker: str) -> str:
    """
    Pulls real trailing-twelve-month financials (revenue, net income, EPS,
    profit margin) straight from Yahoo Finance — not from web search
    snippets. This is what the Researcher's numbers should be checked
    against, and what the Writer should actually put in the report instead
    of unverified figures pulled from search results.
    """
    try:
        info = yf.Ticker(ticker).info
        revenue = info.get("totalRevenue")
        net_income = info.get("netIncomeToCommon")
        eps = info.get("trailingEps")
        margin = info.get("profitMargins")
        currency = info.get("currency", "")

        if revenue is None and eps is None:
            print(f"[finance] {ticker}: .info returned {len(info)} keys but no revenue/eps found")
            return f"{ticker}: no verified financial data available from Yahoo Finance."

        lines = [f"{ticker} — VERIFIED financial data (Yahoo Finance, trailing twelve months):"]
        if revenue is not None:
            lines.append(f"  Revenue (TTM): {revenue:,} {currency}")
        if net_income is not None:
            lines.append(f"  Net income (TTM): {net_income:,} {currency}")
        if eps is not None:
            lines.append(f"  EPS (trailing): {eps}")
        if margin is not None:
            lines.append(f"  Profit margin: {margin:.1%}")
        return "\n".join(lines)
    except Exception as e:
        print(f"[finance] {ticker}: get_key_financials EXCEPTION: {type(e).__name__}: {e}")
        return f"{ticker}: financial data lookup failed ({e})"


def get_key_financials_for_tickers(tickers: list[str]) -> str:
    """Runs get_key_financials for a list of tickers."""
    if not tickers:
        return "No tickers were mentioned, so no financial data was verified."
    return "\n\n".join(get_key_financials(t) for t in tickers)