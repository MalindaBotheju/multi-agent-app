"""
AGENT: Researcher
Job: turn the research plan into real search queries, run them against the
web, and summarize the actual results into notes.

Accepts optional `extra_instructions` so the pipeline can send it back here
after a human rejection (e.g. "the previous research missed X, dig deeper").
"""

from core.llm_client import call_llm
from core.search import web_search_all


def researcher_agent(research_plan: str, extra_instructions: str = "") -> str:
    # Step A: ask the LLM to turn the plan into concrete search queries
    query_prompt = (
        "You are a Researcher Agent. Given the research plan below, output "
        "3-5 short web search queries (one per line, no numbering) that "
        "would find the needed information. Queries only, nothing else."
    )
    plan_input = research_plan
    if extra_instructions:
        plan_input += f"\n\nADDITIONAL INSTRUCTIONS:\n{extra_instructions}"

    raw_queries = call_llm(query_prompt, plan_input)
    queries = [q.strip("- ").strip() for q in raw_queries.splitlines() if q.strip()]
    print(f"[Researcher] generated {len(queries)} queries: {queries}")

    # Step B: actually run those searches (with a small delay between them —
    # see core/search.py for why)
    combined_results = web_search_all(queries)
    print(f"[Researcher] combined search results length: {len(combined_results)} chars")

    # Step C: ask the LLM to turn raw search results into clean research notes
    notes_prompt = (
        "You are a Researcher Agent. Below are real web search results. "
        "Summarize them into factual notes organized by topic. Cite the "
        "source link next to each fact. If the search results don't answer "
        "something from the plan, say 'NOT FOUND' rather than guessing. "
        "Also list any stock ticker symbols mentioned, on a final line "
        "starting with 'TICKERS:' (comma-separated, or 'TICKERS: none')."
    )
    notes = call_llm(notes_prompt, f"RESEARCH PLAN:\n{plan_input}\n\nSEARCH RESULTS:\n{combined_results}")
    print(f"[Researcher] notes preview: {notes[:200]!r}")
    return notes


def extract_tickers(research_notes: str) -> list[str]:
    """Pulls the 'TICKERS: ...' line out of the research notes."""
    for line in research_notes.splitlines():
        if line.strip().upper().startswith("TICKERS:"):
            raw = line.split(":", 1)[1].strip()
            if raw.lower() == "none" or not raw:
                return []
            return [t.strip().upper() for t in raw.split(",") if t.strip()]
    return []


def resolve_ticker_from_request(user_request: str) -> list[str]:
    """
    Identifies the primary stock ticker directly from the user's original
    question (e.g. "Tesla" -> "TSLA"), independent of whether web search
    found anything. This matters because extract_tickers() only sees
    tickers that happen to show up in the research notes — if search fails
    or comes back empty, notes-based extraction finds nothing even for a
    company as well-known as Tesla, and the pipeline never fetches real
    verified financials at all. This is a separate, cheap LLM call that
    doesn't depend on search succeeding.
    """
    system_prompt = (
        "You identify stock ticker symbols. Given a user's request, reply "
        "with ONLY the single most relevant public company's ticker symbol "
        "in capital letters (e.g. 'TSLA' for Tesla, 'NVDA' for NVIDIA) if "
        "the request is clearly about one specific publicly traded company. "
        "Reply with exactly 'NONE' if no specific public company is "
        "identifiable, or if multiple unrelated companies are mentioned. "
        "No explanation, no punctuation, no extra words."
    )
    result = call_llm(system_prompt, user_request, max_tokens=10).strip().upper()

    # Basic sanity check: real tickers are short, alphabetic (maybe a dot)
    cleaned = result.replace(".", "")
    if result == "NONE" or not result or len(result) > 6 or not cleaned.isalpha():
        return []
    return [result]