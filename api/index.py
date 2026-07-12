"""Vercel serverless entrypoint.

The FastAPI app now calls Hugging Face Inference Providers over HTTPS instead of running
torch locally, so the whole backend fits inside Vercel's Python function size limit.
"""
import sys
from pathlib import Path

# Vercel executes this file from the /api directory; make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.app.main import app  # noqa: E402

__all__ = ["app"]
