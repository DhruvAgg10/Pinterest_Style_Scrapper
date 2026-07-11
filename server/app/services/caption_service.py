from __future__ import annotations

import os
import random
from typing import Dict, List, Optional

_CAPTION_MODEL = None
_CAPTION_TOKENIZER = None

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


def _load_caption_model():
    global _CAPTION_MODEL, _CAPTION_TOKENIZER
    if _CAPTION_MODEL is None:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        model_name = os.getenv("CAPTION_MODEL", "google/flan-t5-base")
        _CAPTION_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        _CAPTION_MODEL = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _CAPTION_MODEL.eval()
    return _CAPTION_MODEL, _CAPTION_TOKENIZER


def _generate_with_model(prompt: str) -> str:
    import torch

    model, tokenizer = _load_caption_model()
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=40,
            do_sample=True,
            temperature=0.9,
            top_p=0.95,
        )
    return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip().strip('"')


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
        f"for a photo with a {context} aesthetic{reference}."
    )
    trendy_prompt = (
        f"Write one short, trendy Gen Z Instagram caption (under 15 words, playful tone, "
        f"emojis welcome) for a photo with a {context} aesthetic{reference}."
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
