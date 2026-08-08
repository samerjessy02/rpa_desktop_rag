"""LangGraph state machine.

Flow per post:

    capture_and_slice --> grounding --(found)--> execution --(more posts)--> capture_and_slice
                              |                                  |
                          (not found)                        (no more posts)
                              v                                  v
                          planner                               END
                        /    |     \\
             next_quadrant retry  give_up
                  |          |        \\
                  v          v         v
              grounding  capture_and_slice  END

`state["mock"]` short-circuits the vision call and the physical pyautogui
actions so the whole graph can be exercised without a display or API keys
(see tests/test_5_graph_mock.py) — useful for verifying state transitions
in CI or on a machine without a GUI.
"""
from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from tjm_project import config, screen_utils, vision, planner, execution
from tjm_project.api_client import Post, fetch_posts


class AgentState(TypedDict):
    posts: list[Post]
    current_post_index: int
    current_post: Optional[Post]

    screenshot_path: Optional[str]
    quadrants: list[str]
    current_quadrant_index: int
    target_coords: Optional[tuple[int, int]]
    retry_count: int
    max_retries: int

    completed_paths: list[str]
    status: str          # human-readable trace of the last transition
    mock: bool            # if True, skip real VLM calls / pyautogui actions
    last_decision: Optional[str]  # planner's most recent routing decision


# --------------------------------------------------------------------------- 
# Nodes
# ---------------------------------------------------------------------------
def fetch_posts_node(state: AgentState) -> AgentState:
    posts = fetch_posts(config.NUM_POSTS)
    return {
        **state,
        "posts": posts,
        "current_post_index": 0,
        "current_post": posts[0] if posts else None,
        "status": f"fetched {len(posts)} posts",
    }


def capture_and_slice_node(state: AgentState) -> AgentState:
    import pyautogui
    import time
    from datetime import datetime
    
    if state.get("mock"):
        quadrants = [f"mock_quadrant_{i}.png" for i in range(4)]
        return {
            **state,
            "screenshot_path": "mock_screenshot.png",
            "quadrants": quadrants,
            "current_quadrant_index": 0,
            "target_coords": None,
            "status": "captured+sliced (mock)",
        }

    # GUARDRAIL: Minimize all open windows (Win + D) to guarantee a clean desktop view
    pyautogui.hotkey("win", "d")
    time.sleep(0.8)  # wait for animations to clear

    # Create a timestamped folder inside the scratch directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.SCRATCH_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = screen_utils.capture_screen(save_dir=run_dir)
    quadrant_paths = screen_utils.slice_into_quadrants(screenshot_path, save_dir=run_dir)
    
    return {
        **state,
        "screenshot_path": str(screenshot_path),
        "quadrants": [str(p) for p in quadrant_paths],
        "current_quadrant_index": 0,
        "target_coords": None,
        "status": "captured+sliced",
    }
  


def grounding_node(state: AgentState) -> AgentState:
    idx = state["current_quadrant_index"]

    if state.get("mock"):
        # Simulate a hit on the last quadrant of the first attempt so the
        # mock run exercises both the "not found -> planner" edge and the
        # "found -> execution" edge without a real VLM.
        found = idx == 3
        if found:
            global_coords = screen_utils.local_to_global(idx, 100, 100)
            if global_coords is not None:
                gx, gy = global_coords
                return {
                    **state,
                    "target_coords": (gx, gy),
                    "status": f"grounding (mock): found in quadrant {idx}",
                }
        return {
            **state,
            "current_quadrant_index": idx + 1,
            "status": f"grounding (mock): miss in quadrant {idx}",
        }

    crop_path = state["quadrants"][idx]
    local = vision.locate_icon_in_crop(crop_path)
    
    if local is not None:
        global_coords = screen_utils.local_to_global(idx, *local)
        # Reject if guardrails blocked the coordinates (returned None)
        if global_coords is not None:
            gx, gy = global_coords
            return {
                **state,
                "target_coords": (gx, gy),
                "status": f"grounding: found icon in quadrant {idx} -> global ({gx},{gy})",
            }

    return {
        **state,
        "current_quadrant_index": idx + 1,
        "status": f"grounding: miss or invalid coords in quadrant {idx}",
    }


def planner_node(state: AgentState) -> AgentState:
    decision = planner.decide_next_step(
        quadrant_index=state["current_quadrant_index"],
        retry_count=state["retry_count"],
        max_retries=state["max_retries"],
    )
    if decision == "retry":
        return {
            **state,
            "retry_count": state["retry_count"] + 1,
            "status": f"planner: retry #{state['retry_count'] + 1}",
            "last_decision": decision,
        }
    return {**state, "status": f"planner: {decision}", "last_decision": decision}


def execution_node(state: AgentState) -> AgentState:
    import time
    post = state["current_post"]
    target = state["target_coords"]

    if state.get("mock"):
        path = str(config.OUTPUT_DIR / f"post_{post['id']}.txt")
        status = f"execution (mock): wrote {path}"
    else:
        path = execution.run_post_in_notepad(target, post)
        status = f"execution: wrote {path}"

    next_index = state["current_post_index"] + 1
    posts = state["posts"]
    next_post = posts[next_index] if next_index < len(posts) else None

    # TEST PAUSE: Give you time to manually move the Notepad icon on the desktop
    if next_post and not state.get("mock"):
        print("\n" + "=" * 50)
        print(" [TEST PAUSE] Post finished successfully!")
        print(" You have 7 seconds to drag the Notepad icon to a new spot...")
        print("=" * 50)
        for i in range(7, 0, -1):
            print(f" Capturing next screenshot in {i} seconds...", end="\r")
            time.sleep(1.0)
        print("\n Taking screenshot NOW! Hands off the mouse.")

    return {
        **state,
        "completed_paths": [*state["completed_paths"], path],
        "current_post_index": next_index,
        "current_post": next_post,
        "retry_count": 0,
        "status": status,
    }


# --------------------------------------------------------------------------- 
# Conditional routing
# ---------------------------------------------------------------------------
def route_after_grounding(state: AgentState) -> str:
    return "execution" if state.get("target_coords") else "planner"


def route_after_planner(state: AgentState) -> str:
    decision = state.get("last_decision", "give_up")
    if decision == "next_quadrant":
        return "grounding"
    if decision == "retry":
        return "capture_and_slice"
    return "end"


def route_after_execution(state: AgentState) -> str:
    return "capture_and_slice" if state.get("current_post") else "end"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("fetch_posts", fetch_posts_node)
    graph.add_node("capture_and_slice", capture_and_slice_node)
    graph.add_node("grounding", grounding_node)
    graph.add_node("planner", planner_node)
    graph.add_node("execution", execution_node)

    graph.add_edge(START, "fetch_posts")
    graph.add_edge("fetch_posts", "capture_and_slice")
    graph.add_edge("capture_and_slice", "grounding")

    graph.add_conditional_edges(
        "grounding",
        route_after_grounding,
        {"execution": "execution", "planner": "planner"},
    )
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"grounding": "grounding", "capture_and_slice": "capture_and_slice", "end": END},
    )
    graph.add_conditional_edges(
        "execution",
        route_after_execution,
        {"capture_and_slice": "capture_and_slice", "end": END},
    )

    return graph.compile()


def initial_state(mock: bool = False) -> AgentState:
    return {
        "posts": [],
        "current_post_index": 0,
        "current_post": None,
        "screenshot_path": None,
        "quadrants": [],
        "current_quadrant_index": 0,
        "target_coords": None,
        "retry_count": 0,
        "max_retries": config.MAX_RETRIES,
        "completed_paths": [],
        "status": "init",
        "mock": mock,
        "last_decision": None,
    }
