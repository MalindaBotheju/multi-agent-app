"""
AGENT: Quality Control
Job: review the final report against basic standards before showing a human.
"""

from core.llm_client import call_llm


def quality_agent(report: str) -> str:
    system_prompt = (
        "You are a Quality Control Agent. Review the report below. Check: "
        "Is it clear? Does it avoid presenting uncertain or invalid claims "
        "as fact? Is the structure logical? Reply with 'APPROVED' if it "
        "passes, or 'NEEDS REVISION:' followed by specific feedback if not."
    )
    return call_llm(system_prompt, report)
