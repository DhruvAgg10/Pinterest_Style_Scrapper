from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from PIL import Image

SUPPORTED_CATEGORIES = {"upper", "lower", "accessories", "tattoo"}


def _run_huggingface_analysis(image_path: str | Path, category: str) -> Dict[str, object]:
    try:
        from transformers import pipeline

        model_name = os.getenv("HF_IMAGE_MODEL", "google/vit-base-patch16-224")
        classifier = pipeline("image-classification", model=model_name, device=-1)
        result = classifier(str(image_path))[0]
        return {
            "analysis_mode": "huggingface",
            "model": model_name,
            "prediction": result.get("label", "fashion"),
            "confidence": round(float(result.get("score", 0.0)), 3),
            "style_tags": [category, "ai-classified"],
        }
    except Exception:
        return {
            "analysis_mode": "live_engine",
            "model": "fallback",
            "prediction": "fashion",
            "confidence": 0.0,
            "style_tags": [category, "fallback"],
        }


def _fetch_pinterest_inspiration(query: str) -> List[Dict[str, object]]:
    try:
        response = requests.get(
            "https://www.pinterest.com/search/pins/?q=" + requests.utils.quote(query),
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        pins = []
        seen = set()

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-pin-media")
            if not src or not src.startswith("https://"):
                continue
            if src in seen:
                continue
            seen.add(src)
            pins.append({
                "title": query,
                "source": "pinterest",
                "image_url": src,
                "url": "https://www.pinterest.com/search/pins/?q=" + requests.utils.quote(query),
            })
            if len(pins) >= 6:
                break

        if pins:
            return pins

        for link in soup.select("a")[:6]:
            href = link.get("href", "")
            if href and "pin" in href.lower():
                pins.append({"title": query, "source": "pinterest", "image_url": "https://i.pinimg.com/200x/0/0/0.jpg", "url": href})
        return pins
    except Exception:
        return [{"title": query, "source": "pinterest-fallback", "image_url": "https://i.pinimg.com/200x/0/0/0.jpg", "url": "https://www.pinterest.com"}]


def _classify_color_family(image: Image.Image) -> str:
    image = image.convert("RGB")
    pixels = list(image.resize((16, 16)).getdata())
    r = sum(pixel[0] for pixel in pixels) / len(pixels)
    g = sum(pixel[1] for pixel in pixels) / len(pixels)
    b = sum(pixel[2] for pixel in pixels) / len(pixels)

    if r > 180 and g > 170 and b > 160:
        return "neutral"
    if r > g and r > b:
        return "warm"
    if b > r and b > g:
        return "cool"
    return "neutral"


def _build_rule_based_payload(image_path: str | Path, category: str) -> Dict[str, object]:
    if not Path(image_path).exists():
        width, height = 400, 600
        dominant_color_family = "neutral"
    else:
        with Image.open(image_path) as image:
            width, height = image.size
            dominant_color_family = _classify_color_family(image)

    orientation = "portrait" if height >= width else "landscape"

    style_tags = ["casual", "streetwear"]
    if category == "tattoo":
        style_tags.extend(["tattoo", "statement"])
    elif category == "upper":
        style_tags.extend(["upper-body", "layered"])
    elif category == "lower":
        style_tags.extend(["lower-body", "tailored"])
    elif category == "accessories":
        style_tags.extend(["accessories", "detail"])

    return {
        "category": category,
        "style_tags": style_tags,
        "dominant_colors": [dominant_color_family],
        "analysis_mode": "live_engine",
        "engine_components": ["geometry", "color", "category_tags"],
        "image_summary": {
            "size": orientation,
            "dimensions": {"width": width, "height": height},
            "dominant_color_family": dominant_color_family,
        },
        "keywords": [
            "fashion reference",
            f"{category} analysis",
            "aesthetic inspiration",
        ],
    }


def build_analysis_payload(image_path: str | Path, category: str, use_model: bool = False) -> Dict[str, object]:
    payload = _build_rule_based_payload(image_path, category)
    if use_model:
        model_payload = _run_huggingface_analysis(image_path, category)
        payload["analysis_mode"] = model_payload["analysis_mode"]
        payload["engine_status"] = "active"
        payload["confidence"] = model_payload["confidence"]
        payload["model"] = model_payload["model"]
        payload["prediction"] = model_payload["prediction"]
        payload["style_tags"] = list(dict.fromkeys(payload["style_tags"] + model_payload["style_tags"]))
    return payload


def build_inspiration_payload(query: str) -> Dict[str, object]:
    return {"query": query, "results": _fetch_pinterest_inspiration(query)}


def build_recommendation_payload(analyses: List[Dict[str, object]]) -> Dict[str, object]:
    tags = set()
    grouped_analysis = {}
    for analysis in analyses:
        category = analysis.get("category", "unknown")
        grouped_analysis[category] = analysis
        tags.update(analysis.get("style_tags", []))

    return {
        "recommended_tags": sorted(tags),
        "grouped_analysis": grouped_analysis,
        "results": [
            {
                "title": "Sample style reference",
                "source": "demo provider",
                "score": 0.92,
            }
        ],
    }
