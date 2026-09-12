"""
All the tunable constants for the pipeline live here, in one place.

Secrets (like GROQ_API_KEY) come from environment variables, loaded from
a local .env file via python-dotenv. On Render, you won't have a .env
file at all — you set the same variable in Render's dashboard instead,
and os.environ.get() picks it up exactly the same way.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into os.environ if the file exists (local dev only)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# llama-3.3-70b-versatile was deprecated by Groq on Aug 16, 2026 — using it
# now returns an error, which is what was causing the "Internal Server
# Error" you hit. gpt-oss-120b is Groq's recommended replacement.
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

MAX_QUALITY_REVISIONS = 3   # how many times Writer retries after Quality rejects
MAX_HUMAN_REJECTIONS = 2    # how many times the pipeline retries after a human rejects

# Rate-limit handling: a single pipeline run makes 6+ LLM calls, which can
# exceed Groq's free-tier tokens-per-minute limit. These control how the
# retry-with-backoff in core/llm_client.py behaves.
MAX_LLM_RETRIES = 3                # how many times to retry a single call after a 429
LLM_RETRY_BASE_DELAY_SECONDS = 5   # fallback wait if Groq doesn't tell us how long
MAX_LLM_OUTPUT_TOKENS = 800        # caps each response's length, reducing token usage per call
MAX_WRITER_OUTPUT_TOKENS = 2000    # the Writer's full report needs more room than other agents —
                                    # 800 was cutting reports off mid-table (broken markdown)

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Locally: copy .env.example to .env and fill "
        "it in. On Render: set it under the service's Environment tab."
    )