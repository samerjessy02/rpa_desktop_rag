"""Screenshot capture + quadrant slicing + local<->global coordinate mapping.
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from tjm_project import config


def capture_screen(save_dir: Path | None = None) -> Path:
    """Take a full-screen screenshot and save it to disk. Returns the path."""
    import pyautogui  # imported lazily

    save_dir = save_dir or config.SCRATCH_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    img = pyautogui.screenshot()
    if img.size != (config.SCREEN_WIDTH, config.SCREEN_HEIGHT):
        # Don't silently proceed on the wrong resolution: quadrant math below
        raise RuntimeError(
            f"Expected {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT} screen, "
            f"got {img.size}. Re-check display scaling/resolution."
        )
    path = save_dir / f"screenshot_{int(time.time() * 1000)}.png"
    img.save(path)
    return path


def slice_into_quadrants(screenshot_path: Path, save_dir: Path | None = None) -> list[Path]:
    """Split a full screenshot into 4 quadrant images, ordered 0..3 as in
    config.QUADRANT_OFFSETS (top_left, top_right, bottom_left, bottom_right).
    """
    save_dir = save_dir or config.SCRATCH_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(screenshot_path)

    paths: list[Path] = []
    stem = screenshot_path.stem
    for idx in range(4):
        ox, oy = config.QUADRANT_OFFSETS[idx]
        box = (ox, oy, ox + config.QUAD_WIDTH, oy + config.QUAD_HEIGHT)
        crop = img.crop(box)
        name = config.QUADRANT_NAMES[idx]
        out_path = save_dir / f"{stem}_{idx}_{name}.png"
        crop.save(out_path)
        paths.append(out_path)
    return paths


def local_to_global(quadrant_index: int, local_x: int, local_y: int) -> tuple[int, int]:
    """Translate a coordinate inside a quadrant crop to full-screen coordinates."""
    if quadrant_index not in config.QUADRANT_OFFSETS:
        raise ValueError(f"quadrant_index must be 0-3, got {quadrant_index}")
    ox, oy = config.QUADRANT_OFFSETS[quadrant_index]
    return ox + local_x, oy + local_y


def bbox_center(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) // 2, (y1 + y2) // 2
