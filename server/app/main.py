from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from .services.caption_service import build_caption_payload
from .services.combo_service import build_combos_payload
from .services.image_service import build_analysis_payload, build_inspiration_payload, build_recommendation_payload


class CaptionRequest(BaseModel):
    style_tags: List[str] = []
    title: Optional[str] = None

app = FastAPI(title="AI Fashion Pose & Style Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/inspiration")
def inspiration(query: str) -> dict[str, object]:
    return build_inspiration_payload(query)


@app.post("/api/analyze")
async def analyze_images(
    upper_images: List[UploadFile] = File(default=None),
    lower_images: List[UploadFile] = File(default=None),
    accessories_images: List[UploadFile] = File(default=None),
    tattoo_images: List[UploadFile] = File(default=None),
) -> dict[str, object]:
    analyses = []

    async def process_group(files: Optional[List[UploadFile]], category: str) -> None:
        # Only the first image per category is sent to the vision model. Each call is a
        # remote LLM round-trip, and the serverless function has a hard time budget.
        for upload in (files or [])[:1]:
            try:
                contents = await upload.read()
                analyses.append(build_analysis_payload(contents, category))
            except Exception as exc:
                analyses.append({
                    "category": category,
                    "style_tags": ["upload-error"],
                    "dominant_colors": ["neutral"],
                    "analysis_mode": "error",
                    "error": str(exc),
                    "image_summary": {"size": "unknown", "dimensions": {"width": 0, "height": 0}},
                })

    await process_group(upper_images, "upper")
    await process_group(lower_images, "lower")
    await process_group(accessories_images, "accessories")
    await process_group(tattoo_images, "tattoo")

    recommendation = build_recommendation_payload(analyses)
    recommendation["inspiration"] = build_inspiration_payload(
        "fashion outfit inspiration", analyses=analyses
    )
    # Internal hints from the analyzer must not leak into the API response.
    for analysis in recommendation.get("grouped_analysis", {}).values():
        if isinstance(analysis, dict):
            analysis.pop("_search_query", None)
    return recommendation


@app.post("/api/combos")
async def build_combos(
    upper_images: List[UploadFile] = File(default=None),
    lower_images: List[UploadFile] = File(default=None),
    shoes_images: List[UploadFile] = File(default=None),
    gender: str = Form(default=""),
    occasion: str = Form(default=""),
) -> dict[str, object]:
    """Take a closet (multiple garments per category), build and rank outfit combos.

    Optional `gender` and `occasion` (e.g. gym, date, movie) sharpen both the
    aesthetic scoring and the inspiration search phrase.
    """

    async def read_group(files: Optional[List[UploadFile]]) -> List[bytes]:
        contents = []
        for upload in files or []:
            try:
                contents.append(await upload.read())
            except Exception:
                continue
        return contents

    closet = {
        "upper": await read_group(upper_images),
        "lower": await read_group(lower_images),
        "shoes": await read_group(shoes_images),
    }
    return build_combos_payload(closet, gender=gender.strip(), occasion=occasion.strip())


@app.get("/api/looks")
def looks(query: str, location: str = "", limit: int = 8) -> dict[str, object]:
    """Reference photos of one outfit worn in a chosen location.

    `query` describes the outfit (e.g. the combo's search phrase); `location`
    (cafe, beach, street, rooftop, ...) is appended so results show a real
    person in that setting wearing a similar look.
    """
    from .services.image_service import _fetch_inspiration_candidates

    phrase = f"{query} {location}".strip() if location else query
    results = _fetch_inspiration_candidates(phrase, limit=limit)
    return {
        "query": phrase,
        "location": location,
        "results": results,
        "data_source": results[0].get("source") if results else "no-results",
    }


@app.post("/api/caption")
def generate_caption(request: CaptionRequest) -> dict[str, object]:
    return build_caption_payload(request.style_tags, request.title)
