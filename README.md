# tjm-project

Windows desktop agent: LangGraph state machine + cascaded visual grounding
(ScreenSeekeR-style) to find the Notepad icon, fetch 10 posts from
JSONPlaceholder, and save them via Notepad to `Desktop/tjm-project/`.

## Setup (uv)

```bash
# 1. Install uv if you don't have it: https://docs.astral.sh/uv/getting-started/installation/

# 2. From the project root, sync dependencies
uv sync

# 3. Copy the env template and fill in your API keys
cp .env.example .env
# edit .env: set OPENROUTER_API_KEY and GOOGLE_API_KEY
```

`OPENROUTER_API_KEY` powers the planner (Llama-4 Scout, via OpenRouter).
`GOOGLE_API_KEY` powers the vision grounding model (Gemini Flash, via
`langchain-google-genai`). Both are required for a real (non-`--mock`)
run.

## Running

```bash
# Full 10-post run against the real desktop
uv run main.py

# Dry run: exercises the full LangGraph state machine without touching
# the mouse/keyboard or calling any model API
uv run main.py --mock
```

## Tests (run in order while building/verifying)

```bash
uv run tests/test_1_env.py          # dependency versions + resolution check
uv run tests/test_2_api.py          # fetch + format post 1
uv run tests/test_3_slicing.py      # screenshot, slice into quadrants, coord math
uv run tests/test_4_vision.py       # real VLM call + mouse-move verification
uv run tests/test_5_graph_mock.py   # full graph, all 10 posts, no side effects
uv run tests/test_6_e2e_single.py   # real end-to-end run for 1 post
```

Before Test 4, 6, and 7 (final verification), place the Notepad shortcut
somewhere visible on the desktop. For Test 7 (final submission
screenshots), re-run with the icon in three different positions
(top-left, bottom-right, center) and capture an annotated screenshot each
time.

## Project layout

```
pyproject.toml
main.py
src/tjm_project/
  config.py       # constants: screen geometry, paths, model ids
  api_client.py   # JSONPlaceholder fetch + formatting
  screen_utils.py # screenshot, quadrant slicing, coordinate mapping
  vision.py        # Gemini Flash grounding calls
  planner.py       # Llama-4 Scout retry/continue decisions
  execution.py      # pyautogui: double-click, type, save, close
  graph.py          # LangGraph state machine wiring it all together
tests/              # Tests 1-6 from the assignment
DESIGN_DOC.md
```