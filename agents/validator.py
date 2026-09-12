"""
AGENT: Validator
Job: check the research notes for problems before they get used.

Three layers, not just one:
  1. Real ticker check: is the ticker even valid, and its current price
     (core/finance.py) — not an LLM guess.
  2. Real financials check: actual revenue/net income/EPS/margin from
     Yahoo Finance (core/finance.py) — used to catch fabricated or
     mismatched numbers in the research notes, not just flag them.
  3. LLM judgment check: everything else (outdated info, missing sources,
     internal inconsistency) still goes through the LLM, since there's no
     simple API for "does this sound made up."
"""

from core.llm_client import call_llm
from core.finance import check_tickers, get_key_financials_for_tickers
from agents.researcher import extract_tickers, resolve_ticker_from_request


def validator_agent(research_notes: str, user_request: str = "") -> str:
    # Combine tickers found two ways: mentioned in the research notes, AND
    # resolved directly from the user's question. The second one matters
    # because if web search fails or comes back empty, notes-based
    # extraction finds nothing — even for a company as well-known as
    # Tesla — and real financials never get fetched at all.
    tickers_from_notes = extract_tickers(research_notes)
    tickers_from_request = resolve_ticker_from_request(user_request) if user_request else []
    tickers = list(dict.fromkeys(tickers_from_notes + tickers_from_request))  # dedupe, keep order
    print(f"[Validator] tickers from notes: {tickers_from_notes}, from request: {tickers_from_request}, combined: {tickers}")

    # Real checks first
    ticker_check_results = check_tickers(tickers)
    financials_check_results = get_key_financials_for_tickers(tickers)
    print(f"[Validator] ticker check result: {ticker_check_results!r}")
    print(f"[Validator] financials check result: {financials_check_results!r}")

    # LLM judgment check second
    system_prompt = (
        "You are a Validator Agent. Review the research notes below, plus "
        "the REAL TICKER CHECK and REAL FINANCIAL DATA (both come from a "
        "live financial data source, not your own judgment — always trust "
        "these over the research notes if they conflict). Your job: "
        "1) Point out any figure in the research notes that CONTRADICTS the "
        "real financial data — name the specific number and what the "
        "verified figure actually is. "
        "2) Flag anything else that looks outdated, missing a source, "
        "marked NOT FOUND, or internally inconsistent. "
        "Output a short list of issues found, or 'NO ISSUES FOUND' if it "
        "looks fine."
    )
    combined_input = (
        f"RESEARCH NOTES:\n{research_notes}\n\n"
        f"REAL TICKER CHECK:\n{ticker_check_results}\n\n"
        f"REAL FINANCIAL DATA:\n{financials_check_results}"
    )
    llm_issues = call_llm(system_prompt, combined_input)

    return (
        f"TICKER CHECK (real data):\n{ticker_check_results}\n\n"
        f"VERIFIED FINANCIALS (real data — use these numbers, not the research notes' figures):\n{financials_check_results}\n\n"
        f"OTHER ISSUES (LLM review):\n{llm_issues}"
    )