"""
AGENT: Writer
Job: turn validated research into a final report.
"""

from core.llm_client import call_llm


def writer_agent(research_notes: str, validation_issues: str, extra_feedback: str = "") -> str:
    system_prompt = (
        "You are a Writer Agent. Write a clear, well-structured report using "
        "the research notes provided.\n\n"
        "CRITICAL RULE ON NUMBERS: the validation notes may include a "
        "'VERIFIED FINANCIALS' section with real data (revenue, net income, "
        "EPS, margin) from Yahoo Finance. Where a verified figure exists for "
        "a metric, USE THE VERIFIED FIGURE as the headline number in your "
        "report — do not lead with a research-notes figure that conflicts "
        "with it. You may mention the research notes' figure briefly as "
        "'unverified / reported elsewhere as X' if it's notably different, "
        "but the verified number is what goes in the main table or summary. "
        "If no verified figure exists for a metric, say the figure could not "
        "be verified rather than presenting a research-notes number as fact.\n\n"
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
    return call_llm(system_prompt, combined_input)