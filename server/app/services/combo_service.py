"""Closet combo engine.

Takes a user's closet (multiple garments per category), builds outfit
combinations (upper x lower x shoes), and scores each with the vision-language
model already used elsewhere — no torch, no CLIP, fits Vercel serverless.

The VLM reads the garment images of one combo and returns an aesthetic score,
vibe tags, and a Pinterest-style search phrase used to fetch location photos the
user can recreate.
"""
from __future__ import annotations

import json
import re
from io import BytesIO
from itertools import product
from typing import Dict, List, Optional

from PIL import Image

from .hf_client import get_hf_client
from .image_service import (
    VLM_MODEL,
    _fetch_inspiration_candidates,
    _image_to_data_uri,
)

# Categories that form a wearable outfit. Accessories/tattoo are optional extras.
COMBO_CATEGORIES = ("upper", "lower", "shoes")

# Cap how many combos we send to the VLM per request — each is a remote round-trip
# and the serverless function has a hard time budget.
MAX_SCORED_COMBOS = 6

_COMBO_PROMPT = (
    "You are a fashion stylist rating one outfit{who}{occasion}. The images are, "
    "in order: {order}. First identify each garment precisely (type, colour, "
    "material). Then judge how well they work together as a viral, aesthetic "
    "outfit{occasion_clause}. Reply with ONLY compact JSON, no markdown, in this "
    "exact shape: "
    '{{"aesthetic_score": <integer 1-10>, '
    '"vibe_tags": ["3-4 concise style tags"], '
    '"why": "one short sentence on why it works or does not", '
    '"search_query": "a specific Pinterest search phrase describing this exact '
    'look on a real person{who_query}{occasion_query}"}}'
)


def _load_image(image_source) -> Optional[Image.Image]:
    """Accept a PIL image, raw bytes, or a filesystem path. Return RGB or None."""
    try:
        if isinstance(image_source, Image.Image):
            return image_source.convert("RGB")
        if isinstance(image_source, (bytes, bytearray)):
            return Image.open(BytesIO(bytes(image_source))).convert("RGB")
        from pathlib import Path

        if Path(image_source).exists():
            return Image.open(image_source).convert("RGB")
    except Exception:
        return None
    return None


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _build_prompt(order: str, gender: str, occasion: str) -> str:
    """Fill the combo prompt with optional gender + occasion context."""
    who = f" for a {gender} person" if gender else ""
    who_query = f" {gender}" if gender else ""
    occ = f" for a {occasion}" if occasion else ""
    occ_clause = f" suitable for {occasion}" if occasion else ""
    occ_query = f" {occasion} outfit" if occasion else ""
    return _COMBO_PROMPT.format(
        who=who,
        occasion=occ,
        order=order,
        occasion_clause=occ_clause,
        who_query=who_query,
        occasion_query=occ_query,
    )


def _score_combo(
    items: List[Dict[str, object]], gender: str = "", occasion: str = ""
) -> Optional[Dict[str, object]]:
    """Send one combo's garment images to the VLM and parse its rating.

    ``items`` is a list of {category, image} dicts. Returns None on any failure
    so the caller can skip this combo rather than hard-fail the whole request.
    """
    client = get_hf_client()
    if not client:
        return None
    order = ", ".join(item["category"] for item in items)
    content: List[Dict[str, object]] = [
        {"type": "text", "text": _build_prompt(order, gender, occasion)}
    ]
    for item in items:
        content.append(
            {"type": "image_url", "image_url": {"url": _image_to_data_uri(item["image"])}}
        )
    try:
        completion = client.chat_completion(
            model=VLM_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": content}],
        )
        data = _extract_json(completion.choices[0].message.content)
    except Exception:
        return None
    if not data:
        return None

    try:
        score = int(data.get("aesthetic_score", 0))
    except (TypeError, ValueError):
        score = 0
    tags = [str(t).strip().lower() for t in data.get("vibe_tags", []) if str(t).strip()]
    return {
        "aesthetic_score": max(0, min(10, score)),
        "vibe_tags": tags[:4],
        "why": str(data.get("why", "")).strip(),
        "search_query": str(data.get("search_query", "")).strip(),
    }


def build_combos_payload(
    closet: Dict[str, List],
    max_scored: int = MAX_SCORED_COMBOS,
    inspiration_per_combo: int = 4,
    gender: str = "",
    occasion: str = "",
) -> Dict[str, object]:
    """Build and rank outfit combos from a closet.

    ``closet`` maps category -> list of image sources (bytes/path/PIL). Only the
    combo categories (upper/lower/shoes) drive combinations. Returns combos
    ranked by aesthetic score, each with inspiration photos to recreate.
    """
    # Resolve images per category, dropping ones that fail to load.
    loaded: Dict[str, List[Dict[str, object]]] = {}
    for category in COMBO_CATEGORIES:
        images = []
        for index, source in enumerate(closet.get(category, []) or []):
            image = _load_image(source)
            if image is not None:
                images.append({"category": category, "image": image, "index": index})
        if images:
            loaded[category] = images

    present = [c for c in COMBO_CATEGORIES if c in loaded]
    if len(present) < 2:
        return {
            "combos": [],
            "message": "Upload at least two categories (e.g. upper + lower) to build combos.",
            "categories_present": present,
        }

    # Cartesian product over whatever categories the user provided.
    all_combos = list(product(*(loaded[c] for c in present)))
    scored: List[Dict[str, object]] = []
    for combo_items in all_combos[:max_scored]:
        items = list(combo_items)
        rating = _score_combo(items, gender=gender, occasion=occasion)
        if rating is None:
            continue
        query = rating["search_query"] or " ".join(rating["vibe_tags"]) or "aesthetic outfit"
        inspiration = _fetch_inspiration_candidates(query, limit=inspiration_per_combo)
        scored.append(
            {
                "items": [{"category": it["category"], "index": it["index"]} for it in items],
                "aesthetic_score": rating["aesthetic_score"],
                "vibe_tags": rating["vibe_tags"],
                "why": rating["why"],
                "search_query": query,
                "inspiration": inspiration,
            }
        )

    scored.sort(key=lambda c: c["aesthetic_score"], reverse=True)
    return {
        "combos": scored,
        "total_possible": len(all_combos),
        "scored": len(scored),
        "categories_present": present,
        "score_source": "vision-model" if scored else "unavailable",
    }
