from pathlib import Path

from PIL import Image

from server.app.services.image_service import (
    _build_contextual_inspiration_query,
    _extract_json,
    _largest_pin_image,
    build_analysis_payload,
    build_inspiration_payload,
    build_recommendation_payload,
)


def test_build_analysis_payload_returns_expected_structure(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (320, 480), color=(255, 120, 80)).save(image_path)

    payload = build_analysis_payload(image_path, "outfit")

    assert payload["category"] == "outfit"
    assert payload["style_tags"]
    assert payload["dominant_colors"]
    assert payload["analysis_mode"] == "live_engine"
    assert payload["image_summary"]["size"] == "portrait"
    assert payload["image_summary"]["dominant_color_family"] in {"warm", "cool", "neutral"}
    assert "fashion" in payload["fashion_summary"].lower()
    assert payload["fit_guidance"]


def test_build_analysis_payload_accepts_raw_bytes(tmp_path: Path) -> None:
    image_path = tmp_path / "sample-bytes.png"
    Image.new("RGB", (400, 300), color=(30, 80, 140)).save(image_path)

    payload = build_analysis_payload(image_path.read_bytes(), "upper")

    assert payload["category"] == "upper"
    assert payload["tag_source"] in {"vision-model", "fallback-heuristic"}
    assert payload["image_summary"]["dimensions"] == {"width": 400, "height": 300}
    assert payload["image_summary"]["size"] == "landscape"


def test_build_analysis_payload_falls_back_on_unreadable_input() -> None:
    payload = build_analysis_payload("does-not-exist.png", "tattoo")

    assert payload["tag_source"] == "fallback-heuristic"
    assert "tattoo" in payload["style_tags"]


def test_largest_pin_image_prefers_widest_variant() -> None:
    media = {"images": {"150x150": {"url": "small"}, "600x": {"url": "big"}, "400x300": {"url": "mid"}}}

    assert _largest_pin_image(media) == "big"
    assert _largest_pin_image({}) == ""


def test_extract_json_unwraps_fenced_model_output() -> None:
    raw = '```json\n{"aesthetic_tags": ["y2k"], "colors": ["pink"]}\n```'

    assert _extract_json(raw) == {"aesthetic_tags": ["y2k"], "colors": ["pink"]}
    assert _extract_json("no json here") is None


def test_contextual_query_prefers_vision_model_search_phrase() -> None:
    analyses = [
        {"category": "upper", "style_tags": ["upper", "y2k"], "_search_query": "y2k baby tee outfit"},
    ]

    assert _build_contextual_inspiration_query("fashion", analyses) == "y2k baby tee outfit"


def test_contextual_query_falls_back_to_tags() -> None:
    analyses = [
        {"category": "upper", "style_tags": ["casual", "layered"], "_search_query": ""},
        {"category": "tattoo", "style_tags": ["tattoo", "statement"], "_search_query": ""},
    ]

    query = _build_contextual_inspiration_query("generic fashion", analyses)

    assert "upper" in query
    assert "tattoo" in query
    assert "layered" in query


def test_build_inspiration_payload_reports_data_source() -> None:
    payload = build_inspiration_payload("fashion outfit")

    assert payload["query"] == "fashion outfit"
    assert isinstance(payload["results"], list)
    assert payload["data_source"] in {"pinterest-api", "pexels", "no-results"}
    assert all(not key.startswith("_") for item in payload["results"] for key in item)


def test_build_recommendation_payload_groups_four_parts() -> None:
    analyses = [
        build_analysis_payload("missing-upper.png", "upper"),
        build_analysis_payload("missing-lower.png", "lower"),
        build_analysis_payload("missing-accessories.png", "accessories"),
        build_analysis_payload("missing-tattoo.png", "tattoo"),
    ]

    payload = build_recommendation_payload(analyses)

    assert payload["grouped_analysis"]["upper"]["category"] == "upper"
    assert payload["grouped_analysis"]["lower"]["category"] == "lower"
    assert payload["grouped_analysis"]["accessories"]["category"] == "accessories"
    assert payload["grouped_analysis"]["tattoo"]["category"] == "tattoo"
    assert payload["style_story"]
    assert payload["fit_focus"]
