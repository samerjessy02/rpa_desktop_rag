# """Physical execution: double-click the located icon, type the post into
# Notepad, save it with Ctrl+S, and close the window.

# Kept separate from graph.py so it can be monkeypatched/mocked in tests
# (Test 5 runs the graph without touching the real mouse/keyboard).
# """
# from __future__ import annotations

# import time

# from tjm_project import config
# from tjm_project.api_client import Post, format_post, output_path_for


# def run_post_in_notepad(target_coords: tuple[int, int], post: Post) -> str:
#     """Double-click Notepad at target_coords, type the post, save it to
#     Desktop/tjm-project/post_{id}.txt, and close Notepad. Returns the path
#     written as a string.
#     """
#     import pyautogui  # lazy import: only needed for the real (non-mock) path

#     pyautogui.PAUSE = 0.3
#     config.ensure_dirs()
#     out_path = output_path_for(post)

#     pyautogui.doubleClick(*target_coords)
#     time.sleep(1.0)  # let Notepad open and grab focus

#     content = format_post(post)
#     pyautogui.typewrite(content, interval=0.005)

# #     # Save As -> type full path -> Enter
# #     pyautogui.hotkey("ctrl", "shift", "s")
# #     time.sleep(0.5)
# #     pyautogui.typewrite(str(out_path), interval=0.01)
# #     pyautogui.press("enter")
# #     time.sleep(0.5)
# #     # Notepad may pop a "replace file?" dialog if the file already exists
# #     pyautogui.press("enter")

# #     # Close the window
# #     pyautogui.hotkey("alt", "f4")
# #     time.sleep(0.3)

# #     return str(out_path)


# """Physical execution: double-click the located icon, type the post into
# Notepad, save it with Ctrl+S, and close the window.

# Kept separate from graph.py so it can be monkeypatched/mocked in tests
# (Test 5 runs the graph without touching the real mouse/keyboard).
# """
# from __future__ import annotations

# import time

# from tjm_project import config
# from tjm_project.api_client import Post, format_post, output_path_for


# def run_post_in_notepad(target_coords: tuple[int, int], post: Post) -> str:
#     """Double-click Notepad at target_coords, type the post, save it to
#     Desktop/tjm-project/post_{id}.txt, and close Notepad. Returns the path
#     written as a string.
#     """
#     import pyautogui  # lazy import: only needed for the real (non-mock) path

#     pyautogui.PAUSE = 0.4
#     config.ensure_dirs()
#     out_path = output_path_for(post)

#     # 1. Open Notepad
#     pyautogui.doubleClick(*target_coords)
#     time.sleep(1.5)  # allow window to fully load and focus

#     # 2. Type post content
#     content = format_post(post)
#     pyautogui.typewrite(content, interval=0.005)
#     time.sleep(0.5)

#     # 3. Trigger Save (Ctrl+S opens Save As for a new/unsaved file)
#     pyautogui.hotkey("ctrl", "s")
#     time.sleep(1.0)  # wait for the Save As dialog box to appear and take focus

#     # 4. Select all in the filename field to clear placeholder text, then type absolute path
#     pyautogui.hotkey("ctrl", "a")
#     pyautogui.typewrite(str(out_path), interval=0.01)
#     time.sleep(0.3)
    
#     # 5. Press Enter to save
#     pyautogui.press("enter")
#     time.sleep(1.0)  # wait for file write / potential overwrite dialog

#     # 6. Handle potential "Confirm Save As" (file already exists) dialog
#     pyautogui.press("enter")
#     time.sleep(0.5)

#     # 7. Press Enter again to accept any final save/close confirmation prompt (clicks "Save")
#     pyautogui.press("enter")
#     time.sleep(0.5)

#     # 8. Close the window cleanly
#     pyautogui.hotkey("alt", "f4")
#     time.sleep(0.5)

#     return str(out_path)


"""Physical execution: double-click the located icon, type the post into
Notepad, save it via Save As menu, and close the window.

Kept separate from graph.py so it can be monkeypatched/mocked in tests
(Test 5 runs the graph without touching the real mouse/keyboard).
"""
from __future__ import annotations

import time

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
    out_path = output_path_for(post)

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
    
    # 5. Press Enter to save
    pyautogui.press("enter")
    time.sleep(1.0)  # wait for file write / potential overwrite dialog

    # 6. Handle potential "Confirm Save As" (file already exists) prompt
    pyautogui.press("enter")
    time.sleep(0.5)

    # 7. Close Notepad cleanly
    pyautogui.hotkey("alt", "f4")
    time.sleep(0.5)

    return str(out_path)