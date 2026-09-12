"""
AGENT: Writer
Job: turn validated research into a final report.
"""

import config
from core.llm_client import call_llm


def writer_agent(research_notes: str, validation_issues: str, extra_feedback: str = "") -> str:
    system_prompt = (
        "You are a Writer Agent. Write a clear, well-structured report using "
        "the research notes provided.\n\n"
        "FORMATTING: use standard Markdown only. For any source link, use "
        "normal Markdown link syntax like [source name](https://example.com) "
        "— never wrap URLs in special bracket characters such as 【 】 or any "
        "other non-standard punctuation; those don't render as clickable "
        "links and show up as broken text. Keep tables short enough to "
        "finish completely — an unfinished table is worse than a shorter, "
        "complete one.\n\n"
        "CRITICAL RULE ON NUMBERS: the validation notes may include a "
        "'VERIFIED FINANCIALS' section with real data (revenue, net income, "
        "EPS, margin) from Yahoo Finance. Where a verified figure exists for "
        "a metric, USE THE VERIFIED FIGURE as the headline number in your "
        "report — do not lead with a research-notes figure that conflicts "
        "with it. You may mention the research notes' figure briefly as "
        "'unverified / reported elsewhere as X' if it's notably different, "
        "but the verified number is what goes in the main table or summary. "
        "If no verified figure exists for a metric, say plainly in prose that "
        "the figure could not be verified. NEVER invent placeholder text like "
        "'$XX billion', 'XX%', 'TBD', or similar filler — those look like "
        "broken output, not missing data. If you don't have a real number, "
        "don't put a row with a fake one in a table at all; either omit that "
        "row/metric, or write a short sentence saying it wasn't available in "
        "the sources you had.\n\n"
        "For anything else flagged in the known issues (invalid tickers, "
        "outdated info, missing sources), caveat it clearly rather than "
        "stating it as fact."
    )
    combined_input = (
        f"RESEARCH NOTES:\n{research_notes}\n\n"
        f"KNOWN ISSUES WITH THIS RESEARCH (includes VERIFIED FINANCIALS section):\n{validation_issues}"
    )
    if extra_feedback:
        combined_input += f"\n\nFEEDBACK TO ADDRESS:\n{extra_feedback}"
    return call_llm(system_prompt, combined_input, max_tokens=config.MAX_WRITER_OUTPUT_TOKENS)