"""Physical execution: double-click the located icon, type the post into
Notepad, save it via Save As menu, and close the window.

Kept separate from graph.py so it can be monkeypatched/mocked in tests
(Test 5 runs the graph without touching the real mouse/keyboard).
"""
from __future__ import annotations

import time
from pathlib import Path

from tjm_project import config
from tjm_project.api_client import Post, format_post, output_path_for


def run_post_in_notepad(target_coords: tuple[int, int], post: Post) -> str:
    """Double-click Notepad at target_coords, type the post, save it via
    Save As to Desktop/tjm-project/post_{id}.txt, and close Notepad. 
    Returns the path written as a string.
    """
    import pyautogui  # lazy import: only needed for the real (non-mock) path

    pyautogui.PAUSE = 0.4
    config.ensure_dirs()
    
    # Ensure out_path is a Path object
    out_path = Path(output_path_for(post))

    # GUARDRAIL: Delete the file via Python if it already exists. 
    # This guarantees Notepad will never show a "Confirm Save As" (overwrite) dialog,
    # meaning we only ever need to press Enter exactly once.
    if out_path.exists():
        out_path.unlink()

    # 1. Open Notepad
    pyautogui.doubleClick(*target_coords)
    time.sleep(1.5)  # allow window to fully load and focus

    # 2. Type post content
    content = format_post(post)
    pyautogui.typewrite(content, interval=0.005)
    time.sleep(0.5)

    # 3. Open "Save As" dialog reliably via menu: Alt + F, then A
    pyautogui.hotkey("alt", "f")
    time.sleep(0.4)
    pyautogui.press("a")
    time.sleep(1.2)  # wait for Save As dialog box to open and focus filename field

    # 4. Type the full absolute file path directly into the dialog box
    pyautogui.typewrite(str(out_path), interval=0.01)
    time.sleep(0.5)
    
    # 5. Press Enter to save (Closes the Save As dialog)
    pyautogui.press("enter")
    time.sleep(1.0)  # wait for file to write

    # 6. Close Notepad cleanly
    pyautogui.hotkey("alt", "f4")
    time.sleep(0.5)

    return str(out_path)