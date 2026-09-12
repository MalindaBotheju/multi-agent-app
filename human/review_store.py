"""
HUMAN-IN-THE-LOOP, web version.

The old CLI version used input() to block and wait for a person to type
y/n. A web server can't do that — each HTTP request must return quickly.
So instead: when a report is ready for review, we store it here with a
unique ID and return that ID to the frontend. The person reviews it on
the web page and calls back a separate endpoint with their decision.

This is an in-memory dict, not a database — it's just tracking "what's
currently awaiting a decision" while the server process is running. If
the server restarts, any pending review is lost. That's a deliberate
simplification (no database was requested), not persistent storage.
"""

import uuid

# review_id -> {"state": dict of everything the pipeline needs to resume}
_pending_reviews: dict[str, dict] = {}


def create_pending_review(pipeline_state: dict) -> str:
    """Stores a pipeline state awaiting human decision. Returns its ID."""
    review_id = str(uuid.uuid4())
    _pending_reviews[review_id] = pipeline_state
    return review_id


def get_pending_review(review_id: str) -> dict | None:
    return _pending_reviews.get(review_id)


def resolve_pending_review(review_id: str) -> dict | None:
    """Removes and returns the pipeline state once a decision has been made."""
    return _pending_reviews.pop(review_id, None)
