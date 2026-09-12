"""
Real web search (DuckDuckGo, no API key needed) — used by the Researcher
agent so it works with actual current information instead of the LLM
guessing from memory.
"""

import time
from ddgs import DDGS


def web_search(query: str, max_results: int = 3) -> str:
    """Runs a real DuckDuckGo search and returns titles + snippets + links."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        # DuckDuckGo rate-limits aggressively if hit with several queries
        # in quick succession — this is the most common cause of a
        # "search failed" line, especially right after a prior research pass.
        print(f"[search] FAILED for '{query}': {e}")
        return f"[search failed for '{query}': {e}]"

    if not results:
        print(f"[search] NO RESULTS for '{query}'")
        return f"[no results for '{query}']"

    print(f"[search] OK for '{query}' — {len(results)} result(s)")
    formatted = []
    for r in results:
        # Truncate snippets — untrimmed search result bodies can be long
        # enough to burn through a rate-limited token budget in one call.
        body = r["body"][:250]
        formatted.append(f"- {r['title']}: {body} (Source: {r['href']})")
    return "\n".join(formatted)


def web_search_all(queries: list[str], delay_seconds: float = 1.0) -> str:
    """
    Runs web_search for each query with a small delay between calls, to
    reduce the chance of DuckDuckGo rate-limiting a burst of queries —
    which is what silently produced near-empty research notes before.
    """
    results = []
    for i, q in enumerate(queries):
        if i > 0:
            time.sleep(delay_seconds)
        results.append(f"QUERY: {q}\n{web_search(q)}")
    return "\n\n".join(results)