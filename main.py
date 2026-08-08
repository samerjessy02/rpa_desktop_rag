# """Entry point: `uv run main.py` runs the full 10-post workflow against the
# real desktop. Use `--mock` to dry-run the state machine without touching the
# mouse/keyboard or calling the vision/planner APIs (see Test 5).
# """
# from __future__ import annotations

# import argparse
# import sys

# sys.path.insert(0, "src")

# from tjm_project import config
# from tjm_project.graph import build_graph, initial_state


# def main() -> None:
#     parser = argparse.ArgumentParser(description="tjm-project desktop agent")
#     parser.add_argument(
#         "--mock", action="store_true",
#         help="Dry-run: skip real screenshots/VLM calls/pyautogui actions.",
#     )
#     parser.add_argument(
#         "--limit", type=int, default=config.NUM_POSTS,
#         help="Number of posts to process (default: 10).",
#     )
#     args = parser.parse_args()

#     graph = build_graph()
#     state = initial_state(mock=args.mock)

#     print(f"Starting run (mock={args.mock}, limit={args.limit})...")
#     final_state = None
#     for step in graph.stream(state, {"recursion_limit": 200}):
#         for node_name, node_state in step.items():
#             print(f"[{node_name}] {node_state.get('status')}")
#             final_state = node_state

#     if final_state:
#         print("\nDone.")
#         print(f"Posts written: {len(final_state.get('completed_paths', []))}")
#         for p in final_state.get("completed_paths", []):
#             print(f"  - {p}")


# if __name__ == "__main__":
#     main()

"""Entry point: `uv run main.py` runs the full workflow against the
real desktop. Use `--mock` to dry-run the state machine without touching the
mouse/keyboard or calling the vision/planner APIs (see Test 5).
"""
from __future__ import annotations

import argparse
import sys

sys.path.insert(0, "src")

from tjm_project import config
from tjm_project.graph import build_graph, initial_state


def main() -> None:
    parser = argparse.ArgumentParser(description="rpa-desktop-rag agent")
    parser.add_argument(
        "--mock", action="store_true",
        help="Dry-run: skip real screenshots/VLM calls/pyautogui actions.",
    )
    parser.add_argument(
        "--limit", type=int, default=config.NUM_POSTS,
        help="Number of posts to process (default: 10).",
    )
    args = parser.parse_args()

    # Override config so fetch_posts respects the command-line limit
    config.NUM_POSTS = args.limit

    graph = build_graph()
    state = initial_state(mock=args.mock)

    print(f"Starting run (mock={args.mock}, limit={args.limit})...")
    final_state = None
    for step in graph.stream(state, {"recursion_limit": 200}):
        for node_name, node_state in step.items():
            print(f"[{node_name}] {node_state.get('status')}")
            final_state = node_state

    if final_state:
        print("\nDone.")
        print(f"Posts written: {len(final_state.get('completed_paths', []))}")
        for p in final_state.get("completed_paths", []):
            print(f"  - {p}")


if __name__ == "__main__":
    main()