"""Test 4: place the Notepad shortcut in ONE known corner of the desktop
before running this. The script screenshots, slices, runs Qwen2.5-VL on
each quadrant until it gets a hit, converts to global coords, and moves the
mouse there so you can visually confirm the cursor lands on the icon.

Run: uv run tests/test_4_vision.py
Requires OPENROUTER_API_KEY (or LOCAL_VLM_BASE_URL) to be set.
"""
import sys
sys.path.insert(0, "src")

import pyautogui

from tjm_project import config, screen_utils, vision


def main():
    print("Capturing and slicing screen...")
    screenshot_path = screen_utils.capture_screen()
    quadrant_paths = screen_utils.slice_into_quadrants(screenshot_path)

    for idx, crop_path in enumerate(quadrant_paths):
        name = config.QUADRANT_NAMES[idx]
        print(f"Checking quadrant {idx} ({name})...")
        local = vision.locate_icon_in_crop(crop_path)
        if local is not None:
            gx, gy = screen_utils.local_to_global(idx, *local)
            print(f"  FOUND at local {local} -> global ({gx}, {gy})")
            print("  Moving mouse there now...")
            pyautogui.moveTo(gx, gy, duration=0.5)
            print("  Mouse moved. Visually confirm it's on the Notepad icon.")
            return
        print(f"  Not found in quadrant {idx}.")

    print("Notepad icon was not located in any quadrant. Check icon placement "
          "and VISION_MODEL/OPENROUTER_API_KEY configuration.")


if __name__ == "__main__":
    main()
