from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .services.image_service import build_analysis_payload, build_inspiration_payload, build_recommendation_payload

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

    async def process_group(files: List[UploadFile] | None, category: str) -> None:
        for upload in files or []:
            contents = await upload.read()
            temp_path = f"/tmp/{upload.filename}"
            with open(temp_path, "wb") as handle:
                handle.write(contents)
            analyses.append(build_analysis_payload(temp_path, category, use_model=True))

    await process_group(upper_images, "upper")
    await process_group(lower_images, "lower")
    await process_group(accessories_images, "accessories")
    await process_group(tattoo_images, "tattoo")

    recommendation = build_recommendation_payload(analyses)
    recommendation["inspiration"] = build_inspiration_payload("fashion outfit inspiration")
    return recommendation
