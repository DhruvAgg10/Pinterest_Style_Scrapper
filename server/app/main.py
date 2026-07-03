from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .services.image_service import build_analysis_payload, build_recommendation_payload

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


@app.post("/api/analyze")
async def analyze_images(
    outfit_images: List[UploadFile] = File(default=None),
    tattoo_images: List[UploadFile] = File(default=None),
) -> dict[str, object]:
    analyses = []

    for upload in outfit_images or []:
        contents = await upload.read()
        temp_path = f"/tmp/{upload.filename}"
        with open(temp_path, "wb") as handle:
            handle.write(contents)
        analyses.append(build_analysis_payload(temp_path, "outfit"))

    for upload in tattoo_images or []:
        contents = await upload.read()
        temp_path = f"/tmp/{upload.filename}"
        with open(temp_path, "wb") as handle:
            handle.write(contents)
        analyses.append(build_analysis_payload(temp_path, "tattoo"))

    return build_recommendation_payload(analyses)
