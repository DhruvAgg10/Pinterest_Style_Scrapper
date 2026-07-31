"""Shared Hugging Face Inference Providers client.

Both the image analyzer and the caption generator call the same free-tier
HF Inference Providers endpoint, so the client construction lives here once.

Returns a cached ``InferenceClient`` when a token is set, or ``None`` when no
token is configured — callers treat ``None`` as "degrade to local fallbacks".
"""
from __future__ import annotations

import os
from typing import Optional

_HF_CLIENT = None  # None = not yet resolved; False = resolved-but-no-token


def get_hf_client():
    """Return a cached HF InferenceClient, or None if no token is configured."""
    global _HF_CLIENT
    if _HF_CLIENT is None:
        from huggingface_hub import InferenceClient

        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        _HF_CLIENT = InferenceClient(token=token) if token else False
    return _HF_CLIENT or None
