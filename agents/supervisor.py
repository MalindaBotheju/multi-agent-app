"""
AGENT: Supervisor
Job: take the user's request and break it into a clear research plan.
"""

from core.llm_client import call_llm


def supervisor_agent(user_request: str) -> str:
    system_prompt = (
        "You are a Supervisor Agent. Your only job is to take a user's request "
        "and break it down into a short, clear list of what information needs "
        "to be researched to answer it well. Output a numbered list only."
    )
    return call_llm(system_prompt, user_request)
