# DESIGN_DOC — tjm-project

## 1. Objective

A Windows desktop agent that locates the Notepad icon on a 1920x1080 screen
purely from pixels (no OS window APIs, no fixed coordinates), opens it,
fetches 10 posts from JSONPlaceholder, types each one into Notepad in the
format `Title: {title}\n\n{body}`, and saves each to
`Desktop/tjm-project/post_{id}.txt`.

The interesting engineering problem is the "purely from pixels" part: a
72x72px desktop icon on a 1920x1080 canvas is a needle-in-a-haystack target
for a vision-language model, so the visual search has to be structured
rather than a single "find the icon" call against the full frame.

## 2. The cascaded visual search (ScreenSeekeR-style)

Feeding a full 1920x1080 screenshot to a VLM and asking it to return pixel
coordinates for a small icon is unreliable — the icon occupies a tiny
fraction of the image, well below the effective resolution most VLMs
attend to, so localization accuracy degrades sharply on small UI elements
(this is the failure mode documented for GUI-grounding on high-resolution
screens, e.g. in the ScreenSpot-Pro benchmark and the ScreenSeekeR search
strategy). The fix used here is a **cascaded / coarse-to-fine search**:

1. Split the 1920x1080 screenshot into four 960x540 quadrants.
2. Show the VLM one quadrant at a time (a much smaller effective search
   space per call), asking only "is the Notepad icon in *this* crop, and
   where?"
3. Stop as soon as a quadrant returns a confident hit; translate that
   crop-local coordinate back into full-screen coordinates.
4. If all four quadrants miss (e.g. the icon is temporarily obscured by a
   popup, or the desktop hasn't finished rendering), take a fresh
   screenshot and try again, up to `MAX_RETRIES` times.

This is "cascaded" in the sense that each quadrant is a cheaper, higher-
precision sub-search rather than one expensive full-frame search — the same
principle ScreenSeekeR-style pipelines use, generalized here to a simple
fixed 2x2 grid (a single cascade level) since a 960x540 crop is already
small enough for reliable point/bbox grounding from Qwen2.5-VL. A deeper
implementation could recurse (quadrant of a quadrant) if 960x540 still
proved too coarse, but one level was sufficient for a icon-sized target and
keeps the code easy to explain.

## 3. Why two models (planner vs. grounding)

The assignment calls for "standard agentic design patterns," which in
practice means **separating perception from decision-making**:

- **Grounding node (Qwen2.5-VL)** — a vision-language model whose only job
  is: "given this image crop, is the icon here, and if so, where?" It
  returns structured JSON (`{"found": bool, "bbox": [...]}`) and nothing
  else. No planning, no memory of past attempts.
- **Planner node (Llama-4 Scout, via OpenRouter)** — a text-only reasoning
  step that looks at *state* (which quadrant index we're on, how many
  retries we've used) and decides the next control-flow action:
  `next_quadrant`, `retry`, or `give_up`. It doesn't see pixels at all.

Splitting these matters because they answer different kinds of questions:
grounding is "what's in this image," planning is "given what's happened so
far, what should we do next." Coupling them into one model call would make
the agent harder to test (you couldn't mock one without the other) and
harder to reason about when something goes wrong. In this specific graph
the planner's decision logic is simple enough that a plain conditional
would also work correctly — it's kept as an LLM call to satisfy the
"planner + grounding as separate nodes" requirement and because it's the
natural place to add real judgment later (e.g. "the previous attempt's
screenshot showed a dialog box, wait longer before retrying") without
changing the graph's shape.

## 4. LangGraph state machine

### State schema (`AgentState`, TypedDict)

| Field | Purpose |
|---|---|
| `posts`, `current_post_index`, `current_post` | The 10 fetched posts and a pointer to the one currently being processed |
| `screenshot_path`, `quadrants` | Paths to the latest full screenshot and its 4 quadrant crops |
| `current_quadrant_index` | 0-3 pointer into `quadrants`, driving the cascaded search |
| `target_coords` | Global `(x, y)` once the icon is found; `None` while searching |
| `retry_count`, `max_retries` | Bounds the retry loop so a stuck agent terminates instead of looping forever |
| `completed_paths` | Accumulates output file paths, one per finished post |
| `status` | Human-readable trace string, printed at every transition for debuggability |
| `mock` | Short-circuits real screenshots/VLM calls/pyautogui so the graph can run headless |
| `last_decision` | The planner's most recent routing decision, read by the conditional edge right after it |

### Nodes and edges

```
START -> fetch_posts -> capture_and_slice -> grounding
                                                 |
                                    found? ------+------ not found?
                                       |                     |
                                       v                     v
                                  execution               planner
                                       |               /     |      \
                              more posts?      next_quadrant retry  give_up
                                /      \             |         |        \
                               v        v            v         v         v
                     capture_and_slice  END      grounding  capture_and_slice  END
```

- **`fetch_posts_node`** — one-shot: calls the JSONPlaceholder API and seeds
  `posts`/`current_post`.
- **`capture_and_slice_node`** — takes a screenshot, slices it into 4
  quadrants, resets `current_quadrant_index` to 0 and `target_coords` to
  `None`. Re-entered both for a new post and for a retry after all
  quadrants miss.
- **`grounding_node`** — runs Qwen2.5-VL on `quadrants[current_quadrant_index]`.
  On a hit, sets `target_coords` (converted to global coordinates via
  `local_to_global`). On a miss, increments `current_quadrant_index`.
- **`planner_node`** — only reached on a miss. Decides `next_quadrant`
  (loop back to `grounding` with the incremented index), `retry`
  (increment `retry_count`, loop back to `capture_and_slice` for a fresh
  screenshot), or `give_up` (end the run — this path exists so a stuck
  agent fails loudly rather than looping forever).
- **`execution_node`** — double-clicks `target_coords`, types the
  formatted post, saves it to `Desktop/tjm-project/post_{id}.txt`, closes
  Notepad, and advances to the next post (or ends if all 10 are done).

Conditional edges (`route_after_grounding`, `route_after_planner`,
`route_after_execution`) are plain functions of state, kept outside the
node functions so they're trivial to unit test independently of any model
call.

## 5. Assumptions

- The desktop resolution is fixed at 1920x1080 with no display scaling; the
  quadrant math assumes exact 960x540 crops. `screen_utils.capture_screen`
  hard-fails if the detected resolution doesn't match, rather than silently
  producing wrong coordinates.
- The Notepad icon is visible somewhere on the desktop (not minimized to a
  folder, not covered by a maximized window) at the start of each run.
- Qwen2.5-VL and Llama-4 Scout are both reachable via OpenRouter using an
  OpenAI-compatible chat-completions API; `LOCAL_VLM_BASE_URL` is provided
  as an escape hatch to point the vision call at a local server instead,
  without changing any calling code.
- One retry loop (fresh screenshot + re-slice) is enough to recover from
  transient occlusions (a popup, a not-yet-rendered desktop); genuinely
  missing icons should surface as a `give_up` rather than retry forever.
- "Standard agentic design patterns" was interpreted as: typed state,
  single-responsibility nodes, conditional routing driven by pure
  functions of state, and a mock mode for testing control flow without
  live side effects — deliberately not adding memory/tools abstractions
  beyond what this task needs.

## 6. Testing strategy

Each numbered test in the assignment maps to one script in `tests/`,
building confidence incrementally: environment → API → geometry → vision →
full state machine (mocked) → full state machine (live, 1 post) → full live
run. The mock mode in `graph.py` (`state["mock"]`) means Test 5 exercises
the *exact* production graph and routing logic, not a parallel test-only
copy of it — the only things swapped out are the calls that need a real
display or paid API access.
