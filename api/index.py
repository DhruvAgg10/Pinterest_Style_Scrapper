from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.main import app as fastapi_app

app = fastapi_app

@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
