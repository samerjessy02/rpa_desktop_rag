"""Central configuration for the tjm-project agent.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Screen geometry -------------------------------------------------------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
QUAD_WIDTH = SCREEN_WIDTH // 2   # 960
QUAD_HEIGHT = SCREEN_HEIGHT // 2  # 540

# Pixel offset of each quadrant's top-left corner in full-screen coordinates.
# Index order matches the iteration order used by the grounding node.
QUADRANT_OFFSETS = {
    0: (0, 0),                        # top_left
    1: (QUAD_WIDTH, 0),                # top_right
    2: (0, QUAD_HEIGHT),               # bottom_left
    3: (QUAD_WIDTH, QUAD_HEIGHT),       # bottom_right
}
QUADRANT_NAMES = {
    0: "top_left",
    1: "top_right",
    2: "bottom_left",
    3: "bottom_right",
}

# --- Output / working paths -------------------------------------------------
DESKTOP_DIR = Path.home() / "Desktop"
OUTPUT_DIR = DESKTOP_DIR / "tjm-project"
SCRATCH_DIR = Path.home() / ".tjm_project_scratch"

# --- External services -------------------------------------------------------
POSTS_API_URL = "https://jsonplaceholder.typicode.com/posts"
NUM_POSTS = 10

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

PLANNER_MODEL = os.getenv("PLANNER_MODEL", "meta-llama/llama-4-scout:free")
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-3.6-flash")
LOCAL_VLM_BASE_URL = os.getenv("LOCAL_VLM_BASE_URL") or None
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- Agent behavior -----------------------------------------------------------
MAX_RETRIES = 3           # full-screen retry loops after all 4 quadrants miss
RETRY_WAIT_SECONDS = 2
NOTEPAD_ICON_PROMPT = (
    "Locate the Notepad desktop icon (a small application shortcut icon, "
    "not an open window) in this image. Respond with strict JSON only, "
    'in the form {"found": true, "bbox": [x1, y1, x2, y2]} using pixel '
    'coordinates relative to THIS image, or {"found": false} if no '
    "Notepad icon is visible in this crop."
)


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
