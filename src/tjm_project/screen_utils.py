"""Screenshot capture + quadrant slicing + local<->global coordinate mapping.
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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


def annotate_quadrant_grid(img: Image.Image) -> Image.Image:
    """Draw the quadrant grid directly onto a copy of the image, with each
    quadrant's index labeled (matching config.QUADRANT_OFFSETS/
    QUADRANT_NAMES exactly: 0=top_left, 1=top_right, 2=bottom_left,
    3=bottom_right).

    Labels sit right next to the center crosshair, NOT in the screen
    corners. Windows' default icon auto-arrange grid starts filling from
    the top-left corner of the screen (and would start similarly in each
    quadrant's own top-left corner), so a corner-placed label risks
    occluding exactly the icon it's meant to help identify. The dead center
    of the screen is essentially never covered by desktop icons, so that's
    where the labels go instead.
    """
    annotated = img.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size
    mid_x, mid_y = w // 2, h // 2

    line_color = (255, 0, 0)
    draw.line([(mid_x, 0), (mid_x, h)], fill=line_color, width=2)
    draw.line([(0, mid_y), (w, mid_y)], fill=line_color, width=2)

    label_size = max(16, h // 24)
    try:
        font = ImageFont.truetype("arial.ttf", size=label_size)
    except Exception:
        font = ImageFont.load_default()

    box = label_size + 10   # box side length
    gap = 6                 # gap from the crosshair lines

    # Each label sits just off the crosshair, tucked into its own quadrant.
    label_positions = {
        0: (mid_x - gap - box, mid_y - gap - box),   # top_left: up-and-left of center
        1: (mid_x + gap, mid_y - gap - box),          # top_right: up-and-right of center
        2: (mid_x - gap - box, mid_y + gap),          # bottom_left: down-and-left of center
        3: (mid_x + gap, mid_y + gap),                # bottom_right: down-and-right of center
    }
    for idx, (x, y) in label_positions.items():
        draw.rectangle([x, y, x + box, y + box], fill=line_color)
        # Roughly center the digit inside the box
        draw.text((x + box * 0.28, y + box * 0.12), str(idx), fill=(255, 255, 255), font=font)

    return annotated


def downscale_for_planner(
    screenshot_path: Path,
    max_dim: int = None,
    save_dir: Path | None = None,
    annotate: bool = True,
) -> Path:
    """Create a downscaled, quadrant-grid-annotated copy of the full
    screenshot for the planner's quadrant-ordering call (ScreenSeekeR-style
    position inference). Keeps the image reasonably sized (token/latency
    friendly) while preserving legibility of small icon labels, and draws
    the fixed quadrant grid + index labels (near the center crosshair, not
    the corners) directly on it so the planner's answer is grounded in our
    exact coordinate scheme rather than its own guess at where a 2x2 split
    would fall.
    """
    max_dim = max_dim or config.PLANNER_IMAGE_MAX_DIM
    save_dir = save_dir or config.SCRATCH_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(screenshot_path)
    w, h = img.size
    scale = max_dim / max(w, h)
    if scale < 1:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))

    if annotate:
        img = annotate_quadrant_grid(img)

    out_path = save_dir / f"{screenshot_path.stem}_planner_view.png"
    img.save(out_path)
    return out_path


def local_to_global(quadrant_index: int, local_x: int, local_y: int) -> tuple[int, int]:
    """Translate a coordinate inside a quadrant crop to full-screen coordinates."""
    if quadrant_index not in config.QUADRANT_OFFSETS:
        raise ValueError(f"quadrant_index must be 0-3, got {quadrant_index}")
    ox, oy = config.QUADRANT_OFFSETS[quadrant_index]
    return ox + local_x, oy + local_y


def bbox_center(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) // 2, (y1 + y2) // 2
