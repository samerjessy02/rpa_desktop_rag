"""Planner node: a small reasoning step (Llama-4 Scout via OpenRouter) that
decides what to do after a quadrant search misses. This is intentionally a
thin LLM call, not a rules engine, per the assignment's "standard agentic
design patterns" requirement (planner separated from the grounding/vision
step). In practice the decision is simple enough that a plain if/else would
also work — the LLM is kept in the loop so it can reason about edge cases
like an unexpected popup stealing focus.
"""
from __future__ import annotations

from typing import Literal

from langchain_openai import ChatOpenAI

from tjm_project import config

Decision = Literal["next_quadrant", "retry", "give_up"]

_SYSTEM_PROMPT = """You are the planner for a desktop-automation agent \
searching a 1920x1080 screen (split into 4 quadrants, indices 0-3) for a \
Notepad icon. You are called after a quadrant search misses. \
`quadrant_index` is the index of the NEXT quadrant that still needs to be \
checked (it was already incremented past the quadrant that just missed). \
Given quadrant_index and the retry count, decide the next action. Respond \
with exactly one word:
- "next_quadrant" if quadrant_index <= 3 (there is still an unchecked quadrant)
- "retry" if quadrant_index > 3 (all 4 quadrants missed this pass) and \
retry_count < max_retries (take a fresh screenshot in case a popup or icon \
refresh is blocking the icon)
- "give_up" if quadrant_index > 3 and retry_count >= max_retries
"""


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=config.PLANNER_MODEL,
        api_key=config.OPENROUTER_API_KEY or "not-needed",
        base_url=config.OPENROUTER_BASE_URL,
        temperature=0,
    )


def decide_next_step(quadrant_index: int, retry_count: int, max_retries: int) -> Decision:
    """Ask the planner LLM what to do after a quadrant search misses."""
    message = (
        f"quadrant_index={quadrant_index}, retry_count={retry_count}, "
        f"max_retries={max_retries}. What is the next action?"
    )
    try:
        result = _llm().invoke(
            [("system", _SYSTEM_PROMPT), ("human", message)]
        )
        text = (result.content or "").strip().lower()
    except Exception:
        # Fall back to deterministic logic if the LLM call fails (e.g. no
        # API key set during local dev/testing) — the graph should never
        # hang because a free-tier model was rate-limited.
        text = ""

    if "next_quadrant" in text:
        return "next_quadrant"
    if "retry" in text:
        return "retry"
    if "give_up" in text:
        return "give_up"

    # Deterministic fallback mirrors the exact rule the prompt describes.
    if quadrant_index <= 3:
        return "next_quadrant"
    if retry_count < max_retries:
        return "retry"
    return "give_up"
