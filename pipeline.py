"""
THE PIPELINE — web version.

Same agent order and same two feedback loops as before, but restructured
into two entry points so a web server can pause in the middle:

  run_until_human_review(user_request)
      -> runs Supervisor -> Researcher -> Validator -> Writer -> Quality
         (including the Quality retry loop), then STOPS and hands back a
         report + everything needed to resume later.

  resume_after_human_decision(state, reason, comment)
      -> called when the human rejects. Routes back to Researcher or
         Writer depending on `reason`, runs the relevant stages again,
         and STOPS again with a new report — up to MAX_HUMAN_REJECTIONS.

api.py calls these two functions and stores state in human/review_store.py
between calls — that's what makes this work over HTTP instead of input().
"""

import config
from agents.supervisor import supervisor_agent
from agents.researcher import researcher_agent
from agents.validator import validator_agent
from agents.writer import writer_agent
from agents.quality import quality_agent


def _run_quality_loop(research_notes: str, issues: str) -> str:
    """Writer drafts, Quality checks, Writer revises — up to a limit."""
    report = writer_agent(research_notes, issues)
    quality_result = quality_agent(report)

    rounds = 0
    while quality_result.strip().upper().startswith("NEEDS REVISION") and rounds < config.MAX_QUALITY_REVISIONS:
        rounds += 1
        report = writer_agent(research_notes, issues, extra_feedback=quality_result)
        quality_result = quality_agent(report)

    if quality_result.strip().upper().startswith("NEEDS REVISION"):
        report = f"[WARNING: Quality Agent did not approve after {config.MAX_QUALITY_REVISIONS} revisions]\n\n{report}"

    return report


def run_until_human_review(user_request: str) -> dict:
    """Runs the full automated part of the pipeline. Returns state for the API to store."""
    print(f"\n=== NEW REQUEST: {user_request!r} ===")

    plan = supervisor_agent(user_request)
    print(f"[Supervisor] plan: {plan[:200]!r}")

    research_notes = researcher_agent(plan)

    issues = validator_agent(research_notes, user_request)
    print(f"[Validator] issues: {issues[:200]!r}")

    report = _run_quality_loop(research_notes, issues)
    print(f"[Quality] final report ready, length: {len(report)} chars")

    return {
        "user_request": user_request,
        "plan": plan,
        "research_notes": research_notes,
        "issues": issues,
        "report": report,
        "human_rejections": 0,
    }


def resume_after_human_decision(state: dict, reason: str, comment: str) -> dict:
    """
    Called after a human rejects. Mutates and returns the same state dict
    with an updated report, ready to be shown for review again — unless
    MAX_HUMAN_REJECTIONS has been hit, in which case it's marked final.
    """
    state["human_rejections"] += 1
    print(f"\n=== HUMAN REJECTED (reason={reason!r}, attempt {state['human_rejections']}) ===")
    print(f"Comment: {comment!r}")

    if state["human_rejections"] > config.MAX_HUMAN_REJECTIONS:
        state["final_status"] = "REJECTED"
        state["final_reason"] = f"Gave up after {config.MAX_HUMAN_REJECTIONS} rejections."
        return state

    if reason == "research":
        # Bad research -> go all the way back to the Researcher
        state["research_notes"] = researcher_agent(state["plan"], extra_instructions=comment)
        state["issues"] = validator_agent(state["research_notes"], state["user_request"])
        print(f"[Validator] issues: {state['issues'][:200]!r}")
        state["report"] = _run_quality_loop(state["research_notes"], state["issues"])
    else:
        # "writing" or "other" -> research was fine, just rewrite
        report = writer_agent(
            state["research_notes"],
            state["issues"],
            extra_feedback=f"Human feedback: {comment}",
        )
        quality_result = quality_agent(report)
        if quality_result.strip().upper().startswith("NEEDS REVISION"):
            report = writer_agent(state["research_notes"], state["issues"], extra_feedback=quality_result)
        state["report"] = report

    return state