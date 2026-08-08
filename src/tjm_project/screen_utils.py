"""Screenshot capture + quadrant slicing + local<->global coordinate mapping.

This is the mechanical half of the ScreenSeekeR-style cascaded search: instead
of feeding a full 1920x1080 frame to the VLM (which the paper shows fails on
small targets like desktop icons), we slice the frame into four quadrants and
search them one at a time, only ever showing the model a 960x540 crop.
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from tjm_project import config

def capture_screen(save_dir: Path | None = None) -> Path:
    """Take a full-screen screenshot and save it to disk. Returns the path."""
    import pyautogui

    save_dir = save_dir or config.SCRATCH_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    img = pyautogui.screenshot()
    
    if img.size != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        raise RuntimeError(
            f"Expected {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT} screen, "
            f"got {img.size}. Re-check display scaling/resolution."
        )
        
    path = save_dir / "full.png"
    img.save(path)
    return path


def slice_into_quadrants(screenshot_path: Path, save_dir: Path | None = None) -> list[Path]:
    """Split a full screenshot into 4 quadrant images."""
    save_dir = save_dir or screenshot_path.parent
    save_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(screenshot_path)

    paths: list[Path] = []
    for idx in range(4):
        ox, oy = config.QUADRANT_OFFSETS[idx]
        box = (ox, oy, ox + config.QUAD_WIDTH, oy + config.QUAD_HEIGHT)
        crop = img.crop(box)
        
        name = config.QUADRANT_NAMES[idx]
        out_path = save_dir / f"{name}.png"
        crop.save(out_path)
        paths.append(out_path)
        
    return paths


def bbox_center(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) // 2, (y1 + y2) // 2


def local_to_global(quadrant_index: int, local_x: int, local_y: int) -> tuple[int, int] | None:
    """Translate a coordinate inside a quadrant crop to full-screen coordinates.
    Returns None if the coordinates fall outside the logical screen boundaries.
    """
    if quadrant_index not in config.QUADRANT_OFFSETS:
        raise ValueError(f"quadrant_index must be 0-3, got {quadrant_index}")
        
    # Guardrail: Check if local coordinates exceed the quadrant size
    if not (0 <= local_x <= config.QUAD_WIDTH) or not (0 <= local_y <= config.QUAD_HEIGHT):
        return None
        
    ox, oy = config.QUADRANT_OFFSETS[quadrant_index]
    gx, gy = ox + local_x, oy + local_y
    
    # Guardrail: Check if global coordinates exceed the full screen size
    if not (0 <= gx <= config.SCREEN_WIDTH) or not (0 <= gy <= config.SCREEN_HEIGHT):
        return None
        
    return gx, gy