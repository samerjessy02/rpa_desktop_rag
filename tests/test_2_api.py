"""Test 2: fetch post ID 1, print formatted string and target output path.

Run: uv run tests/test_2_api.py
"""
import sys
sys.path.insert(0, "src")

from tjm_project.api_client import fetch_posts, format_post, output_path_for


def main():
    posts = fetch_posts(limit=1)
    assert posts, "No posts returned from API"
    post = posts[0]
    assert post["id"] == 1, f"Expected post id 1, got {post['id']}"

    formatted = format_post(post)
    path = output_path_for(post)

    print("Formatted content:")
    print("-" * 40)
    print(formatted)
    print("-" * 40)
    print(f"Target output path: {path}")

    assert formatted.startswith("Title: ")
    assert "\n\n" in formatted
    print("\nOK: format and path are correct.")


if __name__ == "__main__":
    main()
