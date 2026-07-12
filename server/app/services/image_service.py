from __future__ import annotations

import base64
import json
import os
import re
from io import BytesIO
from typing import Dict, List, Optional

import requests
from PIL import Image

SUPPORTED_CATEGORIES = {"upper", "lower", "accessories", "tattoo"}

# Kept as the fallback vocabulary when the vision model is unavailable.
AESTHETIC_LABELS = [
    "streetwear", "old money", "y2k", "grunge", "minimalist", "techwear",
    "cottagecore", "preppy", "gothic", "athleisure", "boho chic", "formal",
    "casual chic", "edgy", "vintage", "monochrome", "pastel", "dark academia",
    "coastal", "military-inspired", "punk", "romantic", "sporty", "business casual",
]

# Vision-language model that "reads" the outfit image and returns structured style data.
# Runs remotely on Hugging Face Inference Providers (free tier) — no torch in the bundle.
VLM_MODEL = os.getenv("VLM_MODEL", "google/gemma-3-27b-it")

_HF_CLIENT = None


def _hf_client():
    global _HF_CLIENT
    if _HF_CLIENT is None:
        from huggingface_hub import InferenceClient

        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        _HF_CLIENT = InferenceClient(token=token) if token else False
    return _HF_CLIENT


_VLM_PROMPT = (
    "You are a fashion stylist. Analyze the {category} in this photo. "
    "Reply with ONLY compact JSON, no markdown, in this exact shape: "
    '{{"aesthetic_tags": ["3-5 concise fashion style tags"], '
    '"colors": ["2-3 dominant colors"], '
    '"search_query": "a short Pinterest-style search phrase for similar looks"}}'
)


def _image_to_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _extract_json(text: str) -> Optional[dict]:
    """VLMs sometimes wrap JSON in ```json fences or prose. Pull the first JSON object out."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _vlm_analyze(image: Image.Image, category: str) -> Optional[Dict[str, object]]:
    """Ask the vision model to classify the outfit. Returns None on any failure so the
    caller can fall back to lightweight local heuristics — the app never hard-fails.
    """
    client = _hf_client()
    if not client:
        return None
    try:
        completion = client.chat_completion(
            model=VLM_MODEL,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _VLM_PROMPT.format(category=category)},
                    {"type": "image_url", "image_url": {"url": _image_to_data_uri(image)}},
                ],
            }],
        )
        data = _extract_json(completion.choices[0].message.content)
        if not data:
            return None
        tags = [str(t).strip().lower() for t in data.get("aesthetic_tags", []) if str(t).strip()]
        colors = [str(c).strip().lower() for c in data.get("colors", []) if str(c).strip()]
        query = str(data.get("search_query", "")).strip()
        if not tags:
            return None
        return {"aesthetic_tags": tags[:5], "colors": colors[:3] or ["neutral"], "search_query": query}
    except Exception:
        return None


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


# ---------------------------------------------------------------------------
# Inspiration sourcing (Pinterest official API + Pexels, never scraping)
# ---------------------------------------------------------------------------

def _largest_pin_image(media: Dict[str, object]) -> str:
    """Pick the highest-resolution image URL from a v5 Pin's media.images map."""
    images = media.get("images", {}) if isinstance(media, dict) else {}
    if not isinstance(images, dict):
        return ""

    def width_of(key: str) -> int:
        head = str(key).split("x")[0]
        return int(head) if head.isdigit() else 0

    best_url, best_width = "", -1
    for key, value in images.items():
        url = value.get("url") if isinstance(value, dict) else None
        if not url:
            continue
        width = width_of(key)
        if width > best_width:
            best_width, best_url = width, url
    return best_url


def _fetch_pinterest_api_inspiration(query: str, limit: int) -> List[Dict[str, object]]:
    """Reads the authenticated user's own Pins through Pinterest's official v5 API.

    Never scrapes pinterest.com — per Pinterest's Developer Guidelines. The public v5 API
    has no site-wide pin search, so the user's saved Pins are used as first-party
    inspiration material.
    """
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    if not token:
        return []
    try:
        response = requests.get(
            "https://api.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": min(max(limit, 1), 100)},
            timeout=15,
        )
        if not response.ok:
            return []
        payload = response.json()
        items = payload.get("items", []) if isinstance(payload, dict) else []

        results: List[Dict[str, object]] = []
        for item in items:
            image_url = _largest_pin_image(item.get("media", {}))
            if not image_url:
                continue
            pin_id = item.get("id")
            results.append({
                "title": item.get("title") or item.get("description") or query,
                "source": "pinterest-api",
                "image_url": image_url,
                "url": f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else "https://www.pinterest.com",
            })
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []


def _fetch_pexels_inspiration(query: str, limit: int) -> List[Dict[str, object]]:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        return []
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": min(limit, 80), "orientation": "portrait"},
            timeout=15,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        return [
            {
                "title": photo.get("alt") or query,
                "source": "pexels",
                "image_url": photo.get("src", {}).get("medium") or photo.get("src", {}).get("large", ""),
                "url": photo.get("url", "https://www.pexels.com"),
                "photographer": photo.get("photographer"),
            }
            for photo in photos[:limit]
            if photo.get("src", {}).get("medium") or photo.get("src", {}).get("large")
        ]
    except Exception:
        return []


def _fetch_inspiration_candidates(query: str, limit: int = 6) -> List[Dict[str, object]]:
    pinterest_results = _fetch_pinterest_api_inspiration(query, limit)
    if pinterest_results:
        return pinterest_results
    return _fetch_pexels_inspiration(query, limit)


# ---------------------------------------------------------------------------
# Analysis payload
# ---------------------------------------------------------------------------

def _build_rule_based_payload(image: Optional[Image.Image], category: str) -> Dict[str, object]:
    if image is None:
        width, height = 400, 600
        dominant_color_family = "neutral"
    else:
        width, height = image.size
        dominant_color_family = _classify_color_family(image)

    vlm = _vlm_analyze(image, category) if image is not None else None
    orientation = "portrait" if height >= width else "landscape"

    if vlm:
        style_tags = [category] + vlm["aesthetic_tags"]
        tag_source = "vision-model"
        top_aesthetic = vlm["aesthetic_tags"][0]
        colors = vlm["colors"]
        search_query = vlm["search_query"]
    else:
        style_tags = ["casual", "streetwear"]
        if category == "tattoo":
            style_tags.extend(["tattoo", "statement"])
        elif category == "upper":
            style_tags.extend(["upper-body", "layered"])
        elif category == "lower":
            style_tags.extend(["lower-body", "tailored"])
        elif category == "accessories":
            style_tags.extend(["accessories", "detail"])
        tag_source = "fallback-heuristic"
        top_aesthetic = None
        colors = [dominant_color_family]
        search_query = ""

    if dominant_color_family == "warm":
        fashion_summary = f"This {category} look reads warm and expressive, with strong fashion energy for contemporary styling."
        fit_guidance = "Aim for balance by pairing structured layers with relaxed silhouettes."
    elif dominant_color_family == "cool":
        fashion_summary = f"This {category} look has a cool-toned palette that feels polished and modern in fashion terms."
        fit_guidance = "Keep the overall shape clean and intentional to preserve a refined fit."
    else:
        fashion_summary = f"This {category} look is balanced and versatile, making it suitable for everyday fashion storytelling."
        fit_guidance = "Use proportion and texture to create a confident, wearable outfit."

    if top_aesthetic:
        fashion_summary = f"{fashion_summary} The strongest aesthetic match is {top_aesthetic}."

    return {
        "category": category,
        "style_tags": style_tags,
        "tag_source": tag_source,
        "dominant_colors": colors,
        "analysis_mode": "live_engine",
        "engine_components": ["vision-model" if vlm else "heuristic", "color", "category_tags"],
        "image_summary": {
            "size": orientation,
            "dimensions": {"width": width, "height": height},
            "dominant_color_family": dominant_color_family,
        },
        "fashion_summary": fashion_summary,
        "fit_guidance": fit_guidance,
        "keywords": [k for k in [search_query, "fashion reference", f"{category} analysis"] if k],
        "_search_query": search_query,
    }


def build_analysis_payload(image_source, category: str) -> Dict[str, object]:
    """Accepts a filesystem path, raw bytes, or a PIL Image; returns the analysis payload."""
    image: Optional[Image.Image] = None
    try:
        if isinstance(image_source, Image.Image):
            image = image_source
        elif isinstance(image_source, (bytes, bytearray)):
            image = Image.open(BytesIO(bytes(image_source)))
        else:
            from pathlib import Path

            if Path(image_source).exists():
                image = Image.open(image_source)
    except Exception:
        image = None

    if image is not None:
        image = image.convert("RGB")
    return _build_rule_based_payload(image, category)


def _build_contextual_inspiration_query(query: str, analyses: List[Dict[str, object]] | None = None) -> str:
    if not analyses:
        return query

    # Prefer a vision-model search phrase if one was produced.
    for analysis in analyses:
        phrase = analysis.get("_search_query")
        if phrase:
            return phrase

    category_parts, style_parts = [], []
    for analysis in analyses:
        category = analysis.get("category")
        if category:
            category_parts.append(str(category))
        for tag in analysis.get("style_tags", []) or []:
            tag_value = str(tag).strip().lower()
            if tag_value and tag_value not in {"casual", "streetwear"}:
                style_parts.append(tag_value)

    context_parts = category_parts + style_parts[:8]
    if not context_parts:
        return query
    return " ".join([query, " ", " ".join(dict.fromkeys(context_parts))]).strip()


def build_inspiration_payload(
    query: str,
    analyses: List[Dict[str, object]] | None = None,
    reference_embeddings=None,  # kept for signature compatibility; unused without CLIP
) -> Dict[str, object]:
    contextual_query = _build_contextual_inspiration_query(query, analyses)
    max_results = 6
    candidates = _fetch_inspiration_candidates(contextual_query, limit=max_results)

    results = [
        {key: value for key, value in candidate.items() if not key.startswith("_")}
        for candidate in candidates[:max_results]
    ]
    data_source = results[0].get("source") if results else "no-results"
    return {
        "query": contextual_query,
        "results": results,
        "data_source": data_source,
        "match_mode": "keyword-semantic",
    }


def build_recommendation_payload(analyses: List[Dict[str, object]]) -> Dict[str, object]:
    tags = set()
    grouped_analysis = {}
    for analysis in analyses:
        category = analysis.get("category", "unknown")
        grouped_analysis[category] = analysis
        tags.update(analysis.get("style_tags", []))

    style_story_parts = []
    for category, analysis in grouped_analysis.items():
        style_story_parts.append(f"{category}: {', '.join(analysis.get('style_tags', [])[:3])}")

    return {
        "recommended_tags": sorted(tags),
        "grouped_analysis": grouped_analysis,
        "style_story": " | ".join(style_story_parts) if style_story_parts else "A focused fashion look is emerging from your uploads.",
        "fit_focus": "Use the outfit pieces together to balance silhouette, proportion, and confidence for a polished finish.",
    }
