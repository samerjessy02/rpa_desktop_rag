"""Vision grounding node: uses Gemini Flash via LangChain to locate 
the Notepad icon inside a single quadrant crop and returns local (x, y) pixel coordinates.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from tjm_project import config


def _extract_json(text: str) -> Optional[dict]:
    """VLMs often wrap JSON in prose or markdown fences; pull the object out."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def locate_icon_in_crop(image_path: Path) -> Optional[tuple[int, int]]:
    """Call Gemini Flash on a single quadrant crop.

    Returns the (local_x, local_y) center of the Notepad icon if found,
    else None. Coordinates are local to `image_path` (i.e. 0-960 x 0-540).
    """
    llm = ChatGoogleGenerativeAI(
        model=config.VISION_MODEL,
        temperature=0,
        google_api_key=config.GOOGLE_API_KEY,
    )

    image_bytes = Path(image_path).read_bytes()
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        f"{config.NOTEPAD_ICON_PROMPT}\n\n"
        "Analyze this quadrant image crop carefully. If the Notepad desktop icon is present, "
        "respond with a valid JSON object in this exact format: "
        '{"found": true, "bbox": [ymin, xmin, ymax, xmax]}. '
        "Crucially, the bounding box coordinates MUST be normalized values between 0 and 1000. "
        'If the Notepad icon is not in this crop, respond with {"found": false}.'
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            },
        ]
    )

    response = llm.invoke([message])
    
    # Handle both string and list content blocks returned by Gemini models
    raw_content = response.content
    if isinstance(raw_content, list):
        raw = "".join(
            item.get("text", "") for item in raw_content if isinstance(item, dict)
        )
    else:
        raw = str(raw_content or "")

    parsed = _extract_json(raw)
    if not parsed or not parsed.get("found"):
        return None

    bbox = parsed.get("bbox")
    if not bbox or len(bbox) != 4:
        return None

    ymin, xmin, ymax, xmax = bbox
    
    # Calculate center in the normalized [0, 1000] scale
    norm_x = (xmin + xmax) / 2.0
    
    # We still keep a slight upper-bias (0.3) to account for the text label ("Notepad")
    norm_y = ymin + ((ymax - ymin) * 0.3)
    
    # Map the 0-1000 scale to absolute pixel dimensions of the crop
    target_x = int((norm_x / 1000.0) * config.QUAD_WIDTH)
    target_y = int((norm_y / 1000.0) * config.QUAD_HEIGHT)
    
    return target_x, target_y
    # # Temporary override for testing
    # return 9999, 9999