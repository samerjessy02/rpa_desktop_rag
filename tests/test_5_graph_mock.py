"""Test 5: run the complete graph in mock mode (no real screenshots, VLM
calls, or pyautogui actions) and verify state flows correctly through all
10 post iterations, printing every transition.

Run: uv run tests/test_5_graph_mock.py
"""
import sys
from unittest.mock import patch
sys.path.insert(0, "src")

from tjm_project.graph import build_graph, initial_state
from tjm_project import config


def mock_fetch_posts(*args, **kwargs):
    """Returns dummy posts instantly instead of hitting the real internet."""
    return [
        {"id": i, "title": f"Mock Title {i}", "body": f"Mock body {i}"} 
        for i in range(1, config.NUM_POSTS + 1)
    ]


def main():
    graph = build_graph()
    state = initial_state(mock=True)

    transitions = []
    final_state = None
    
    # Temporarily replace the real fetch_posts with our mock version 
    # while the graph runs, completely bypassing the network.
    with patch("tjm_project.graph.fetch_posts", side_effect=mock_fetch_posts):
        for step in graph.stream(state, {"recursion_limit": 500}):
            for node_name, node_state in step.items():
                transitions.append(node_name)
                print(f"[{node_name}] {node_state.get('status')}")
                final_state = node_state

    print(f"\nTotal transitions: {len(transitions)}")

    expected_post_count = config.NUM_POSTS
    completed = final_state.get("completed_paths", [])
    print(f"Posts 'completed' (mock writes): {len(completed)} / {expected_post_count}")

    assert len(completed) == expected_post_count, (
        f"Expected {expected_post_count} completed posts, got {len(completed)}"
    )
    assert final_state.get("current_post") is None, "Graph ended with posts still pending"
    assert "execution" in transitions and "grounding" in transitions and "planner" in transitions

    print("\nOK: state machine visited capture/grounding/planner/execution nodes "
          "and processed all posts to completion.")


if __name__ == "__main__":
    main()