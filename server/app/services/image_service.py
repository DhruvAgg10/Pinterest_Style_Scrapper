from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import requests
from PIL import Image

SUPPORTED_CATEGORIES = {"upper", "lower", "accessories", "tattoo"}

AESTHETIC_LABELS = [
    "streetwear", "old money", "y2k", "grunge", "minimalist", "techwear",
    "cottagecore", "preppy", "gothic", "athleisure", "boho chic", "formal",
    "casual chic", "edgy", "vintage", "monochrome", "pastel", "dark academia",
    "coastal", "military-inspired", "punk", "romantic", "sporty", "business casual",
]

LIFESTYLE_PROMPT = "a lifestyle photo of a person wearing a fashion outfit"
PRODUCT_PROMPT = "a product photo of a single clothing item on a plain background"

_CLIP_MODEL = None
_CLIP_PROCESSOR = None


def _load_clip():
    global _CLIP_MODEL, _CLIP_PROCESSOR
    if _CLIP_MODEL is None:
        from transformers import CLIPModel, CLIPProcessor

        model_name = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
        _CLIP_MODEL = CLIPModel.from_pretrained(model_name)
        _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(model_name)
        _CLIP_MODEL.eval()
    return _CLIP_MODEL, _CLIP_PROCESSOR


def _run_clip_analysis(image: Image.Image, top_k: int = 4) -> Optional[Dict[str, object]]:
    """Classify aesthetic style with CLIP zero-shot and return the image embedding
    from the same forward pass, so tagging and similarity search share one model call.
    """
    try:
        import torch

        model, processor = _load_clip()
        prompts = [f"a photo of {label} fashion style" for label in AESTHETIC_LABELS]
        inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0].tolist()
        ranked = sorted(zip(AESTHETIC_LABELS, probs), key=lambda pair: pair[1], reverse=True)

        embedding = outputs.image_embeds[0]
        embedding = (embedding / embedding.norm()).tolist()

        return {
            "aesthetic_tags": [label for label, _ in ranked[:top_k]],
            "confidence": round(ranked[0][1], 3),
            "embedding": embedding,
        }
    except Exception:
        return None


def _analyze_candidate_image(url: str) -> Optional[Dict[str, object]]:
    """Fetch a candidate image once and run a single CLIP forward pass that yields both
    its embedding (for similarity ranking) and a lifestyle-vs-product classification, so
    plain clothing/flat-lay shots can be filtered out before they reach the user.
    """
    try:
        import torch

        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        model, processor = _load_clip()
        inputs = processor(text=[LIFESTYLE_PROMPT, PRODUCT_PROMPT], images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = model(**inputs)

        lifestyle_score = outputs.logits_per_image.softmax(dim=1)[0].tolist()[0]

        embedding = outputs.image_embeds[0]
        embedding = (embedding / embedding.norm()).tolist()

        return {
            "embedding": embedding,
            "is_lifestyle": lifestyle_score >= 0.5,
            "lifestyle_score": round(lifestyle_score, 3),
        }
    except Exception:
        return None


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _average_embedding(embeddings: List[List[float]]) -> List[float]:
    dimension = len(embeddings[0])
    summed = [0.0] * dimension
    for embedding in embeddings:
        for index, value in enumerate(embedding):
            summed[index] += value
    norm = sum(value * value for value in summed) ** 0.5
    if norm == 0:
        return summed
    return [value / norm for value in summed]


def _analyze_and_filter_candidates(candidates: List[Dict[str, object]]) -> Dict[str, list]:
    """Fetch + classify every candidate once. Returns lifestyle-photo candidates (annotated
    with their embedding), off-topic product-photo candidates, and candidates that failed
    to fetch/analyze at all, so callers can prefer lifestyle shots but still fall back
    rather than return nothing.
    """
    lifestyle: List[Dict[str, object]] = []
    product: List[Dict[str, object]] = []
    unanalyzed: List[Dict[str, object]] = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        analyses = executor.map(
            lambda candidate: _analyze_candidate_image(str(candidate.get("image_url", ""))), candidates
        )

    for candidate, analysis in zip(candidates, analyses):
        if analysis is None:
            unanalyzed.append(candidate)
            continue
        annotated = dict(candidate)
        annotated["_embedding"] = analysis["embedding"]
        annotated["lifestyle_score"] = analysis["lifestyle_score"]
        (lifestyle if analysis["is_lifestyle"] else product).append(annotated)

    return {"lifestyle": lifestyle, "product": product, "unanalyzed": unanalyzed}


def _rank_candidates_by_similarity(
    candidates: List[Dict[str, object]], reference_embedding: List[float], max_results: int
) -> List[Dict[str, object]]:
    scored = []
    for candidate in candidates:
        embedding = candidate.get("_embedding")
        if embedding is None:
            continue
        scored_candidate = {key: value for key, value in candidate.items() if key != "_embedding"}
        scored_candidate["similarity_score"] = round(_cosine_similarity(reference_embedding, embedding), 3)
        scored.append((scored_candidate["similarity_score"], scored_candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [candidate for _, candidate in scored][:max_results]


def _largest_pin_image(media: Dict[str, object]) -> str:
    """Pick the highest-resolution image URL from a v5 Pin's media.images map.

    Pinterest returns keys like "150x150", "400x300", "600x", "1200x". We prefer the
    widest one so downstream CLIP analysis and display get the best available quality.
    """
    images = media.get("images", {}) if isinstance(media, dict) else {}
    if not isinstance(images, dict):
        return ""

    def width_of(key: str) -> int:
        head = str(key).split("x")[0]
        return int(head) if head.isdigit() else 0

    best_url = ""
    best_width = -1
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

    Never scrapes pinterest.com — per Pinterest's Developer Guidelines (no automated
    scraping/data extraction). The public v5 API does not expose a site-wide pin search,
    so we use the user's saved Pins as first-party inspiration material; every candidate
    is still CLIP-filtered and ranked by visual similarity downstream.
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

    pexels_results = _fetch_pexels_inspiration(query, limit)
    if pexels_results:
        return pexels_results

    return []


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
    clip_result = None
    if not Path(image_path).exists():
        width, height = 400, 600
        dominant_color_family = "neutral"
    else:
        with Image.open(image_path) as image:
            width, height = image.size
            dominant_color_family = _classify_color_family(image)
            clip_result = _run_clip_analysis(image.convert("RGB"))

    orientation = "portrait" if height >= width else "landscape"

    if clip_result:
        style_tags = [category] + clip_result["aesthetic_tags"]
        tag_source = "visual-classifier"
        aesthetic_confidence = clip_result["confidence"]
        embedding = clip_result["embedding"]
        top_aesthetic = clip_result["aesthetic_tags"][0]
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
        aesthetic_confidence = None
        embedding = None
        top_aesthetic = None

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
        "aesthetic_confidence": aesthetic_confidence,
        "dominant_colors": [dominant_color_family],
        "analysis_mode": "live_engine",
        "engine_components": ["geometry", "color", "category_tags"],
        "image_summary": {
            "size": orientation,
            "dimensions": {"width": width, "height": height},
            "dominant_color_family": dominant_color_family,
        },
        "fashion_summary": fashion_summary,
        "fit_guidance": fit_guidance,
        "keywords": [
            "fashion reference",
            f"{category} analysis",
            "aesthetic inspiration",
        ],
        "_embedding": embedding,
    }


def build_analysis_payload(image_path: str | Path, category: str) -> Dict[str, object]:
    return _build_rule_based_payload(image_path, category)


def _build_contextual_inspiration_query(query: str, analyses: List[Dict[str, object]] | None = None) -> str:
    if not analyses:
        return query

    category_parts = []
    style_parts = []
    for analysis in analyses:
        category = analysis.get("category")
        if category:
            category_parts.append(str(category))
        for tag in analysis.get("style_tags", []) or []:
            tag_value = str(tag).strip().lower()
            if tag_value and tag_value not in {"casual", "streetwear"}:
                style_parts.append(tag_value)

    context_parts = []
    if category_parts:
        context_parts.extend(category_parts)
    if style_parts:
        context_parts.extend(style_parts[:8])

    if not context_parts:
        return query

    return " ".join([query, " ", " ".join(dict.fromkeys(context_parts))]).strip()


def build_inspiration_payload(
    query: str,
    analyses: List[Dict[str, object]] | None = None,
    reference_embeddings: List[Optional[List[float]]] | None = None,
) -> Dict[str, object]:
    contextual_query = _build_contextual_inspiration_query(query, analyses)
    valid_embeddings = [embedding for embedding in (reference_embeddings or []) if embedding]

    max_results = 6
    candidates = _fetch_inspiration_candidates(contextual_query, limit=24)

    buckets = _analyze_and_filter_candidates(candidates)
    # Prefer genuine lifestyle/outfit photos; only reach for product shots or
    # unanalyzed candidates if there aren't enough lifestyle matches to fill the grid.
    preferred = buckets["lifestyle"] + buckets["unanalyzed"] + buckets["product"]

    if valid_embeddings and buckets["lifestyle"]:
        reference_embedding = _average_embedding(valid_embeddings)
        results = _rank_candidates_by_similarity(buckets["lifestyle"], reference_embedding, max_results=max_results)
        if len(results) < max_results:
            filler = preferred[len(results):max_results]
            results += [{key: value for key, value in candidate.items() if key != "_embedding"} for candidate in filler]
        match_mode = "visual-similarity"
    else:
        results = [
            {key: value for key, value in candidate.items() if key != "_embedding"}
            for candidate in preferred[:max_results]
        ]
        match_mode = "keyword-only"

    data_source = results[0].get("source") if results else "no-results"
    return {"query": contextual_query, "results": results, "data_source": data_source, "match_mode": match_mode}


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
        "results": [
            {
                "title": "Style-ready outfit reference",
                "source": "fashion engine",
                "score": 0.92,
            }
        ],
    }
