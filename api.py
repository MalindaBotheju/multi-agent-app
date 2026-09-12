"""
FastAPI backend. This is the file Render runs (see render.yaml).

Three endpoints:
  GET  /health                  - simple check that the server is alive
  POST /pipeline/run            - start a new report, runs everything up
                                   to the human review step
  POST /pipeline/review/{id}    - submit an approve/reject decision;
                                   on reject, re-runs the relevant agents
                                   and returns a new report to review
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline import run_until_human_review, resume_after_human_decision
from human.review_store import create_pending_review, get_pending_review, resolve_pending_review

app = FastAPI(title="Multi-Agent Research Pipeline")

# Allows your Vercel-hosted frontend (a different domain) to call this API.
# For tighter security later, replace "*" with your actual Vercel URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    question: str


class ReviewRequest(BaseModel):
    decision: str          # "approve" or "reject"
    reason: str | None = None    # "research" | "writing" | "other" (only needed on reject)
    comment: str | None = None   # what to fix (only needed on reject)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pipeline/run")
def start_pipeline(req: RunRequest):
    state = run_until_human_review(req.question)
    review_id = create_pending_review(state)
    return {"review_id": review_id, "report": state["report"]}


@app.post("/pipeline/review/{review_id}")
def submit_review(review_id: str, req: ReviewRequest):
    state = resolve_pending_review(review_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Review not found or already resolved.")

    if req.decision == "approve":
        return {"status": "APPROVED", "report": state["report"]}

    if req.decision != "reject":
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'.")
    if req.reason not in {"research", "writing", "other"}:
        raise HTTPException(status_code=400, detail="reason must be 'research', 'writing', or 'other'.")

    state = resume_after_human_decision(state, req.reason, req.comment or "")

    if state.get("final_status") == "REJECTED":
        return {"status": "REJECTED", "detail": state["final_reason"]}

    # Still not approved — store it again under a new ID for the next round
    new_review_id = create_pending_review(state)
    return {"review_id": new_review_id, "report": state["report"], "rejections_so_far": state["human_rejections"]}
