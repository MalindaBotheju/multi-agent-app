"""
AGENT: Validator
Job: check the research notes for problems before they get used.

Two layers, not just one:
  1. Real check: any stock tickers mentioned are verified against live
     Yahoo Finance data (core/finance.py) — not an LLM guess.
  2. LLM judgment check: everything else (outdated info, missing sources,
     internal inconsistency) still goes through the LLM, since there's no
     simple API for "does this sound made up."
"""

from core.llm_client import call_llm
from core.finance import check_tickers
from agents.researcher import extract_tickers


def validator_agent(research_notes: str) -> str:
    # Real check first
    tickers = extract_tickers(research_notes)
    ticker_check_results = check_tickers(tickers)

    # LLM judgment check second
    system_prompt = (
        "You are a Validator Agent. Review the research notes below, plus "
        "the REAL TICKER CHECK RESULTS (which come from a live financial "
        "data source, not your own judgment — trust these over the notes "
        "if they conflict). Flag anything that looks: outdated, missing a "
        "source, marked NOT FOUND, internally inconsistent, or contradicted "
        "by the ticker check. Output a short list of issues found, or "
        "'NO ISSUES FOUND' if it looks fine."
    )
    combined_input = (
        f"RESEARCH NOTES:\n{research_notes}\n\n"
        f"REAL TICKER CHECK RESULTS:\n{ticker_check_results}"
    )
    llm_issues = call_llm(system_prompt, combined_input)

    return f"TICKER CHECK (real data):\n{ticker_check_results}\n\nOTHER ISSUES (LLM review):\n{llm_issues}"
