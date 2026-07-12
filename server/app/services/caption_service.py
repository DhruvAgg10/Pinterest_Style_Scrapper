from __future__ import annotations

import os
import random
from typing import Dict, List, Optional

# Instruct model on Hugging Face Inference Providers (free tier). No torch locally.
# Same model as the image analyzer — it is the one reliably served for this account.
CAPTION_MODEL = os.getenv("CAPTION_MODEL", "google/gemma-3-27b-it")

_HF_CLIENT = None

_FALLBACK_NORMAL_TEMPLATES = [
    "Feeling good in this {aesthetic} look today.",
    "A little {aesthetic} moment, just because.",
    "Simple, comfortable, and exactly my vibe right now: {aesthetic}.",
    "New fit, {aesthetic} mood.",
]

_FALLBACK_TRENDY_TEMPLATES = [
    "{aesthetic} core unlocked ✨",
    "main character energy, {aesthetic} edition \U0001F525",
    "not me serving {aesthetic} again \U0001F480",
    "pinterest board come to life \U0001F338",
]


def _hf_client():
    global _HF_CLIENT
    if _HF_CLIENT is None:
        from huggingface_hub import InferenceClient

        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        _HF_CLIENT = InferenceClient(token=token) if token else False
    return _HF_CLIENT


def _generate_with_model(prompt: str) -> str:
    client = _hf_client()
    if not client:
        raise RuntimeError("no HF token configured")
    completion = client.chat_completion(
        model=CAPTION_MODEL,
        max_tokens=40,
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content.strip().strip('"')


def _fallback_caption(aesthetic: str, style: str) -> str:
    templates = _FALLBACK_TRENDY_TEMPLATES if style == "trendy" else _FALLBACK_NORMAL_TEMPLATES
    return random.choice(templates).format(aesthetic=aesthetic)


def build_caption_payload(style_tags: Optional[List[str]] = None, title: Optional[str] = None) -> Dict[str, object]:
    clean_tags = [str(tag) for tag in (style_tags or []) if tag]
    aesthetic = clean_tags[0] if clean_tags else "fashion"
    context = ", ".join(clean_tags[:4]) if clean_tags else "casual fashion"
    reference = f' inspired by "{title}"' if title else ""

    normal_prompt = (
        f"Write one short, genuine Instagram caption (under 20 words, no hashtags) "
        f"for a photo with a {context} aesthetic{reference}. Reply with only the caption."
    )
    trendy_prompt = (
        f"Write one short, trendy Gen Z Instagram caption (under 15 words, playful tone, "
        f"emojis welcome) for a photo with a {context} aesthetic{reference}. Reply with only the caption."
    )

    try:
        normal_caption = _generate_with_model(normal_prompt) or _fallback_caption(aesthetic, "normal")
        trendy_caption = _generate_with_model(trendy_prompt) or _fallback_caption(aesthetic, "trendy")
        caption_source = "text-generation-model"
    except Exception:
        normal_caption = _fallback_caption(aesthetic, "normal")
        trendy_caption = _fallback_caption(aesthetic, "trendy")
        caption_source = "template-fallback"

    return {
        "captions": {"normal": normal_caption, "trendy": trendy_caption},
        "caption_source": caption_source,
        "aesthetic": aesthetic,
    }
