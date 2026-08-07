"""Test 6: real end-to-end run for exactly ONE post (post_1). Place the
Notepad icon somewhere on the desktop before running. Verifies that
Desktop/tjm-project/post_1.txt is created with valid content.

Run: uv run tests/test_6_e2e_single.py
Requires a real Windows desktop session, OPENROUTER_API_KEY, and the
Notepad shortcut visible somewhere on screen.
"""
import sys
from unittest.mock import patch
sys.path.insert(0, "src")

from tjm_project import config
import tjm_project.graph as graph_module
from tjm_project.api_client import fetch_posts


def main():
    graph = graph_module.build_graph()
    state = graph_module.initial_state(mock=False)

    # Limit the run to exactly one post so this test is fast and isolated.
    one_post = fetch_posts(limit=1)
    with patch.object(graph_module, "fetch_posts", return_value=one_post):
        final_state = None
        for step in graph.stream(state, {"recursion_limit": 200}):
            for node_name, node_state in step.items():
                print(f"[{node_name}] {node_state.get('status')}")
                final_state = node_state

    out_path = config.OUTPUT_DIR / "post_1.txt"
    assert out_path.exists(), f"{out_path} was not created"

    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("Title: "), "File content missing 'Title: ' prefix"
    assert len(content.strip()) > 0, "File is empty"

    print(f"\nOK: {out_path} exists with valid content:")
    print("-" * 40)
    print(content)
    print("-" * 40)


if __name__ == "__main__":
    main()
