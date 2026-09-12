"""
AGENT: Writer
Job: turn validated research into a final report.
"""

from core.llm_client import call_llm


def writer_agent(research_notes: str, validation_issues: str, extra_feedback: str = "") -> str:
    system_prompt = (
        "You are a Writer Agent. Write a clear, well-structured report using "
        "the research notes provided. If there are known issues with the "
        "research (including any INVALID TICKER results), explicitly caveat "
        "those parts in the report rather than stating them as fact."
    )
    combined_input = (
        f"RESEARCH NOTES:\n{research_notes}\n\n"
        f"KNOWN ISSUES WITH THIS RESEARCH:\n{validation_issues}"
    )
    if extra_feedback:
        combined_input += f"\n\nFEEDBACK TO ADDRESS:\n{extra_feedback}"
    return call_llm(system_prompt, combined_input)
