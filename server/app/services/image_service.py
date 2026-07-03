from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from PIL import Image


def build_analysis_payload(image_path: str | Path, category: str) -> Dict[str, object]:
    image = Image.open(image_path)
    width, height = image.size
    orientation = "portrait" if height >= width else "landscape"

    dominant_colors = ["warm", "neutral"]
    style_tags = ["casual", "streetwear"]
    if category == "tattoo":
        style_tags.append("tattoo")

    return {
        "category": category,
        "style_tags": style_tags,
        "dominant_colors": dominant_colors,
        "image_summary": {
            "size": orientation,
            "dimensions": {"width": width, "height": height},
        },
        "keywords": [
            "fashion reference",
            f"{category} analysis",
            "aesthetic inspiration",
        ],
    }


def build_recommendation_payload(analyses: List[Dict[str, object]]) -> Dict[str, object]:
    tags = set()
    for analysis in analyses:
        tags.update(analysis.get("style_tags", []))

    return {
        "recommended_tags": sorted(tags),
        "results": [
            {
                "title": "Sample style reference",
                "source": "demo provider",
                "score": 0.92,
            }
        ],
    }
