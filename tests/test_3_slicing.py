"""Test 3: capture screen, slice into 4 quadrants, save to disk, and verify
coordinate translation with dummy numbers.

Run: uv run tests/test_3_slicing.py
"""
import sys
sys.path.insert(0, "src")

from tjm_project import config, screen_utils


def main():
    print("Capturing screenshot...")
    screenshot_path = screen_utils.capture_screen()
    print(f"  Saved: {screenshot_path}")

    print("Slicing into quadrants...")
    quadrant_paths = screen_utils.slice_into_quadrants(screenshot_path)
    for i, p in enumerate(quadrant_paths):
        print(f"  Quadrant {i} ({config.QUADRANT_NAMES[i]}): {p}")

    print("\nVerifying quadrant image dimensions...")
    from PIL import Image
    for i, p in enumerate(quadrant_paths):
        img = Image.open(p)
        assert img.size == (config.QUAD_WIDTH, config.QUAD_HEIGHT), (
            f"Quadrant {i} has wrong size: {img.size}"
        )
    print(f"  OK: all quadrants are {config.QUAD_WIDTH}x{config.QUAD_HEIGHT}.")

    print("\nVerifying coordinate translation (dummy points)...")
    cases = [
        (0, 0, 0, (0, 0)),
        (1, 0, 0, (config.QUAD_WIDTH, 0)),
        (2, 0, 0, (0, config.QUAD_HEIGHT)),
        (3, 0, 0, (config.QUAD_WIDTH, config.QUAD_HEIGHT)),
        (3, 959, 539, (config.SCREEN_WIDTH - 1, config.SCREEN_HEIGHT - 1)),
    ]
    for quad, lx, ly, expected in cases:
        result = screen_utils.local_to_global(quad, lx, ly)
        assert result == expected, f"quad={quad} local=({lx},{ly}) -> {result}, expected {expected}"
        print(f"  quadrant {quad}, local ({lx},{ly}) -> global {result}  OK")

    print("\nAll quadrant borders match 1920x1080 bounds. Test 3 passed.")


if __name__ == "__main__":
    main()
