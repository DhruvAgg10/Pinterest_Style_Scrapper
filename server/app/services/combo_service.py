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

_GARMENT_PROMPT = (
    "You are a fashion cataloguer. Look at this single {category} garment. "
    "Identify it precisely. Reply with ONLY compact JSON, no markdown: "
    '{{"item_type": "specific name e.g. white oxford shirt, black skinny jeans, '
    'grey tank top, tan chelsea boots", '
    '"primary_color": "main colour", '
    '"secondary_color": "accent colour or empty", '
    '"pattern": "solid/striped/plaid/graphic/etc", '
    '"material": "cotton/denim/leather/knit/etc or empty", '
    '"style": "1-2 style tags e.g. casual, formal, streetwear"}}'
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


def analyze_garment(image: Image.Image, category: str) -> Dict[str, object]:
    """Stage 1: classify ONE garment image on its own (type, colour, pattern...).

    Returns structured attributes plus a short `descriptor` string. Falls back to
    a minimal descriptor if the vision model is unavailable, so combos still work.
    """
    client = get_hf_client()
    fallback = {
        "item_type": category,
        "primary_color": "",
        "secondary_color": "",
        "pattern": "",
        "material": "",
        "style": "",
        "descriptor": category,
    }
    if not client:
        return fallback
    try:
        completion = client.chat_completion(
            model=VLM_MODEL,
            max_tokens=160,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _GARMENT_PROMPT.format(category=category)},
                    {"type": "image_url", "image_url": {"url": _image_to_data_uri(image)}},
                ],
            }],
        )
        data = _extract_json(completion.choices[0].message.content)
    except Exception:
        return fallback
    if not data:
        return fallback

    attrs = {k: str(data.get(k, "")).strip() for k in
             ("item_type", "primary_color", "secondary_color", "pattern", "material", "style")}
    descriptor = " ".join(
        p for p in [attrs["primary_color"], attrs["pattern"], attrs["item_type"]] if p
    ) or attrs["item_type"] or category
    attrs["descriptor"] = descriptor.strip()
    return attrs


def _score_combo_text(
    descriptors: List[str], gender: str = "", occasion: str = ""
) -> Optional[Dict[str, object]]:
    """Stage 2: score a combo from its per-garment descriptors (text only, cheap).

    Because each garment was already identified in stage 1, the model reasons
    over accurate item descriptions instead of guessing from stacked images.
    """
    client = get_hf_client()
    if not client:
        return None
    outfit = " + ".join(descriptors)
    who = f" for a {gender}" if gender else ""
    occ_rule = (
        f' Also judge if this outfit is actually appropriate to WEAR for {occasion} '
        f'(e.g. a dress shirt is not gym-appropriate). Set "suitable" false if not.'
        if occasion else ""
    )
    suitable_field = '"suitable": <true or false>, ' if occasion else ""
    prompt = (
        f"You are a fashion stylist. Rate this outfit{who}: {outfit}."
        f"{occ_rule} Judge how well the pieces work together as a viral, aesthetic "
        "look. Reply with ONLY compact JSON, no markdown: "
        "{" + suitable_field +
        '"aesthetic_score": <integer 1-10>, '
        '"vibe_tags": ["3-4 concise style tags"], '
        '"why": "one short sentence on why it works or not", '
        '"search_query": "a specific Pinterest search phrase for a real person '
        f'wearing this exact outfit{who}{(" " + occasion) if occasion else ""}"}}'
    )
    try:
        completion = client.chat_completion(
            model=VLM_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
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
    query = str(data.get("search_query", "")).strip() or outfit
    # Default suitable True when the model omits it (no occasion given).
    suitable = data.get("suitable", True)
    return {
        "aesthetic_score": max(0, min(10, score)),
        "vibe_tags": tags[:4],
        "why": str(data.get("why", "")).strip(),
        "search_query": query,
        "suitable": bool(suitable) if isinstance(suitable, bool) else True,
    }



def build_look_keyword(outfit: str, location: str = "", want: str = "") -> str:
    """Turn an outfit + optional location + free-text intent into a tight Pinterest
    search keyword. Uses the model when available; otherwise concatenates.

    `want` is the user's own words for the kind of photo they want, e.g.
    "candid full body shots", "moody film grain", "mirror selfie".
    """
    parts = [p for p in [outfit, location, want] if p]
    fallback = " ".join(parts).strip() or outfit
    client = get_hf_client()
    if not client or not (location or want):
        return fallback
    prompt = (
        "Write ONE short Pinterest search phrase (max 8 words, no quotes, no "
        "punctuation) that would surface aesthetic photos of a real person wearing "
        f"this outfit: {outfit}."
        + (f" Setting/location: {location}." if location else "")
        + (f" The user wants: {want}." if want else "")
        + " Reply with only the phrase."
    )
    try:
        completion = client.chat_completion(
            model=VLM_MODEL,
            max_tokens=30,
            messages=[{"role": "user", "content": prompt}],
        )
        phrase = completion.choices[0].message.content.strip().strip('"').replace("\n", " ")
        return phrase or fallback
    except Exception:
        return fallback


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
    # Stage 1: load each image and classify the garment ONCE (type/colour/etc).
    # Analysing every image individually is the "understanding layer" — the model
    # sees one garment at a time instead of guessing from a stack.
    loaded: Dict[str, List[Dict[str, object]]] = {}
    for category in COMBO_CATEGORIES:
        items = []
        for index, source in enumerate(closet.get(category, []) or []):
            image = _load_image(source)
            if image is None:
                continue
            attrs = analyze_garment(image, category)
            items.append(
                {"category": category, "index": index, "attrs": attrs,
                 "descriptor": attrs["descriptor"]}
            )
        if items:
            loaded[category] = items

    present = [c for c in COMBO_CATEGORIES if c in loaded]
    if len(present) < 2:
        return {
            "combos": [],
            "message": "Upload at least two categories (e.g. upper + lower) to build combos.",
            "categories_present": present,
        }

    # Stage 2: combine and score from the accurate descriptors (text scoring).
    # Keep scoring until we have `max_scored` suitable combos, but never make more
    # than `call_budget` model calls, to protect the serverless time budget.
    all_combos = list(product(*(loaded[c] for c in present)))
    call_budget = max_scored * 3 if occasion else max_scored
    scored: List[Dict[str, object]] = []
    calls = 0
    for combo_items in all_combos:
        if len(scored) >= max_scored or calls >= call_budget:
            break
        calls += 1
        items = list(combo_items)
        descriptors = [it["descriptor"] for it in items]
        rating = _score_combo_text(descriptors, gender=gender, occasion=occasion)
        if rating is None:
            continue
        # When an occasion is chosen, drop combos the stylist deems inappropriate
        # to wear there (e.g. a dress shirt for "gym").
        if occasion and not rating.get("suitable", True):
            continue
        query = rating["search_query"] or " ".join(descriptors) or "aesthetic outfit"
        inspiration = _fetch_inspiration_candidates(query, limit=inspiration_per_combo)
        scored.append(
            {
                "items": [
                    {"category": it["category"], "index": it["index"],
                     "item_type": it["attrs"]["item_type"],
                     "color": it["attrs"]["primary_color"]}
                    for it in items
                ],
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
