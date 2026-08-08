"""Planner node: a small reasoning step (Llama-4 Scout via OpenRouter) that
does two jobs:

1. `decide_quadrant_order` — ScreenSeekeR-style position inference. Given a
   downscaled, grid-annotated full screenshot and the target description,
   the planner uses its GUI/layout knowledge to rank the 4 quadrants by how
   likely each is to contain the target, BEFORE any grounding call happens.
   This replaces a blind fixed 0-1-2-3 scan with an image-informed search
   order.
2. `decide_next_step` — after a quadrant search misses, decides whether to
   check the next quadrant in the planned order, retry with a fresh
   screenshot, or give up. Unchanged from before.

Both are intentionally thin LLM calls, not a rules engine. The LLM is kept
in the loop so it can reason about edge cases like an unexpected popup
stealing focus, or GUI conventions (e.g. "shortcuts are usually along the
left edge") that a fixed scan order can't capture.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Literal, Optional

from langchain_core.messages import HumanMessage
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

_ORDER_SYSTEM_PROMPT = """You are the planner for a desktop-automation agent. \
You are shown a downscaled screenshot of a 1920x1080 desktop. A red grid has \
been drawn DIRECTLY ON the image, dividing it into 4 quadrants. Each \
quadrant's index is labeled in a red box positioned next to the center \
crosshair, tucked into that quadrant:
  0 = top_left, 1 = top_right, 2 = bottom_left, 3 = bottom_right
Use those red index numbers exactly as drawn on the image — do not mentally \
re-derive your own split, and do not second-guess the grid lines shown.

Given a description of a target UI element, examine EVERY quadrant \
individually and carefully before ranking — small icons are easy to miss at \
this resolution. Do not assume the target is near other visible icons: a \
single desktop shortcut icon dropped alone on an empty part of the \
wallpaper, with no other icons nearby, is completely normal and just as \
likely as icons appearing in a cluster. Read any small text labels under \
icons if you can make them out; a label matching the target's name is \
strong evidence, even if that icon is isolated.

Important distinction: a "desktop icon" or "desktop shortcut" sits on the \
open desktop background (the empty area of the screen, possibly overlaid on \
a photo/wallpaper) — it is NOT the same as an icon pinned to the taskbar at \
the bottom of the screen. Only treat the taskbar as the likely location if \
the target description explicitly mentions the taskbar.

Rank ALL FOUR quadrant indices from most likely to least likely to contain \
the target.

Respond with strict JSON only, in the form {"order": [a, b, c, d]} where \
a, b, c, d is a permutation of 0, 1, 2, 3 — most likely quadrant first, \
least likely last. No prose, no markdown fences.
"""


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=config.PLANNER_MODEL,
        api_key=config.OPENROUTER_API_KEY or "not-needed",
        base_url=config.OPENROUTER_BASE_URL,
        temperature=0,
    )


def _extract_json(text: str) -> Optional[dict]:
    """Planner responses may be wrapped in prose or markdown fences; pull the
    JSON object out."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def decide_quadrant_order(screenshot_path: Path, target_description: str) -> list[int]:
    """Ask the planner LLM, given a downscaled, grid-annotated full
    screenshot, to rank the four quadrants by likelihood of containing
    `target_description`.

    Returns a list that is a permutation of [0, 1, 2, 3], most-likely-first.
    Falls back to the natural [0, 1, 2, 3] order if the call fails or the
    response can't be parsed into a valid permutation — the search still
    works, it just degrades to the old blind scan for that pass.
    """
    fallback = [0, 1, 2, 3]

    try:
        image_bytes = Path(screenshot_path).read_bytes()
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"Target: {target_description}\n\n{_ORDER_SYSTEM_PROMPT}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
            ]
        )
        result = _llm().invoke([message])
        raw_content = result.content
        if isinstance(raw_content, list):
            text = "".join(
                item.get("text", "") for item in raw_content if isinstance(item, dict)
            )
        else:
            text = str(raw_content or "")

        parsed = _extract_json(text)
        order = parsed.get("order") if parsed else None
        if isinstance(order, list) and sorted(order) == [0, 1, 2, 3]:
            return [int(i) for i in order]
    except Exception:
        # Fall back to the natural scan order if the LLM call fails (e.g. no
        # API key set during local dev/testing, or a non-vision-capable
        # model) — the graph should never hang on this.
        pass

    return fallback


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

    # Deterministic fallback
    if quadrant_index <= 3:
        return "next_quadrant"
    if retry_count < max_retries:
        return "retry"
    return "give_up"
