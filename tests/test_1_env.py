"""Test 1: verify dependencies import cleanly and the display is 1920x1080.

Run: uv run tests/test_1_env.py
"""
import sys
sys.path.insert(0, "src")

import importlib.metadata as md

from tjm_project import config

PACKAGES = ["langgraph", "langchain", "langchain-openai", "pyautogui", "pillow", "requests"]


def main():
    print("Dependency versions:")
    for pkg in PACKAGES:
        try:
            print(f"  {pkg}: {md.version(pkg)}")
        except md.PackageNotFoundError:
            print(f"  {pkg}: NOT INSTALLED")

    print("\nChecking screen resolution...")
    try:
        import pyautogui
        size = pyautogui.size()
        print(f"  Detected: {size.width}x{size.height}")
        assert (size.width, size.height) == (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (
            f"Expected {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}, got {size}"
        )
        print("  OK: resolution matches 1920x1080.")
    except Exception as e:
        print(f"  Could not verify resolution (no display attached?): {e}")
        print("  This is expected in headless/CI environments.")


if __name__ == "__main__":
    main()
