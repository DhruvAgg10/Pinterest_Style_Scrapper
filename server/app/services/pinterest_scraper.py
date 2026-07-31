"""Pinterest keyword image search (unofficial).

Pinterest exposes no public keyword-search API. This module calls Pinterest's
own front-end search resource endpoint (the same one the website's search page
uses) and parses the returned JSON. One request returns many high-resolution
pins, so it is cheap enough for the serverless time budget — unlike scraping
individual pin pages.

Note: this is a reverse-engineered front-end endpoint, not an official API. It
can change or rate-limit without notice; every failure degrades to [] so callers
fall through to the next inspiration source.
"""
from __future__ import annotations

import json
from typing import Dict, List

import requests

_ENDPOINT = "https://www.pinterest.com/resource/BaseSearchResource/get/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*, q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "X-APP-VERSION": "a9be7d4",
    "X-Pinterest-PWS-Handler": "www/search/[scope].js",
}


def _best_image(images: Dict) -> str:
    """Prefer the original image, then fall back to the largest sized variant."""
    if not isinstance(images, dict):
        return ""
    orig = images.get("orig")
    if isinstance(orig, dict) and orig.get("url"):
        return orig["url"]
    if isinstance(orig, list) and orig and isinstance(orig[0], dict):
        return orig[0].get("url", "")
    # Sized variants like "736x" — pick the widest.
    best_url, best_width = "", -1
    for key, value in images.items():
        if not isinstance(value, dict) or not value.get("url"):
            continue
        head = str(key).split("x")[0]
        width = int(head) if head.isdigit() else 0
        if width > best_width:
            best_width, best_url = width, value["url"]
    return best_url


def search_pinterest(query: str, limit: int = 6) -> List[Dict[str, object]]:
    """Return up to `limit` inspiration pins for a keyword. Empty list on failure."""
    params = {
        "source_url": f"/search/pins/?q={query}",
        "data": json.dumps(
            {"options": {"query": query, "scope": "pins", "page_size": max(limit * 2, 12)}, "context": {}}
        ),
    }
    headers = {**_HEADERS, "Referer": f"https://www.pinterest.com/search/pins/?q={query}"}
    try:
        response = requests.get(_ENDPOINT, params=params, headers=headers, timeout=15)
        if not response.ok:
            return []
        results = (
            response.json()
            .get("resource_response", {})
            .get("data", {})
            .get("results", [])
        )
    except Exception:
        return []

    pins: List[Dict[str, object]] = []
    for pin in results:
        if not isinstance(pin, dict):
            continue
        image_url = _best_image(pin.get("images", {}))
        if not image_url:
            continue
        pin_id = pin.get("id")
        title = (
            pin.get("grid_title")
            or pin.get("title")
            or (pin.get("description") or "").strip()
            or query
        )
        pins.append(
            {
                "title": title,
                "source": "pinterest",
                "image_url": image_url,
                "url": f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else "https://www.pinterest.com",
            }
        )
        if len(pins) >= limit:
            break
    return pins
