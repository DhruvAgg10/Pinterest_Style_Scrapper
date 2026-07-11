import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from .services.caption_service import build_caption_payload
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
    embeddings: List[Optional[List[float]]] = []

    async def process_group(files: Optional[List[UploadFile]], category: str) -> None:
        for upload in files or []:
            try:
                contents = await upload.read()
                temp_dir = Path(tempfile.gettempdir())
                temp_dir.mkdir(parents=True, exist_ok=True)
                safe_name = Path(upload.filename or f"{uuid.uuid4().hex}.bin").name
                temp_path = temp_dir / safe_name
                with open(temp_path, "wb") as handle:
                    handle.write(contents)

                analysis = build_analysis_payload(str(temp_path), category)
                embeddings.append(analysis.pop("_embedding", None))
                analyses.append(analysis)
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
        "fashion outfit inspiration", analyses=analyses, reference_embeddings=embeddings
    )
    return recommendation


@app.post("/api/caption")
def generate_caption(request: CaptionRequest) -> dict[str, object]:
    return build_caption_payload(request.style_tags, request.title)
