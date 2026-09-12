"""
The one function every agent uses to 'think'. Every agent is really just:
a different system_prompt + this same function.

Includes retry-with-backoff for Groq's rate limit errors (HTTP 429). The
free/on-demand Groq tier caps you at a fixed number of tokens per minute —
a single pipeline run makes 6+ LLM calls, so it's easy to hit that limit
mid-run. Rather than crashing the whole request, we wait and retry.
"""

import re
import time

from groq import Groq, RateLimitError
import config

client = Groq(api_key=config.GROQ_API_KEY)


def _seconds_to_wait(error: RateLimitError, attempt: int) -> float:
    """
    Figures out how long to wait before retrying. Prefers the exact time
    Groq tells us in its error message/headers; falls back to a growing
    default (5s, 10s, 15s...) if that's not available.
    """
    try:
        header_val = error.response.headers.get("retry-after")
        if header_val:
            return float(header_val) + 1  # small buffer
    except Exception:
        pass

    match = re.search(r"try again in ([\d.]+)s", str(error))
    if match:
        return float(match.group(1)) + 1

    return config.LLM_RETRY_BASE_DELAY_SECONDS * (attempt + 1)


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = None) -> str:
    """
    max_tokens defaults to config.MAX_LLM_OUTPUT_TOKENS. Pass a higher value
    for calls that genuinely need more room (e.g. the Writer's full report)
    without raising the cap — and therefore the token cost — for every
    other, shorter agent call.
    """
    if max_tokens is None:
        max_tokens = config.MAX_LLM_OUTPUT_TOKENS

    last_error = None

    for attempt in range(config.MAX_LLM_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=config.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except RateLimitError as e:
            last_error = e
            if attempt == config.MAX_LLM_RETRIES:
                break
            wait_seconds = _seconds_to_wait(e, attempt)
            time.sleep(wait_seconds)

    # Ran out of retries — raise a clear error instead of Groq's raw one
    raise RuntimeError(
        f"Groq rate limit hit {config.MAX_LLM_RETRIES + 1} times in a row and gave up. "
        f"Your account's tokens-per-minute limit is likely too low for this pipeline's "
        f"token usage. Consider upgrading your Groq tier, or wait a minute and retry. "
        f"Original error: {last_error}"
    )