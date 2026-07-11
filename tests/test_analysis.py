from pathlib import Path

from PIL import Image

from server.app.services.image_service import build_analysis_payload, build_inspiration_payload, build_recommendation_payload


def test_build_analysis_payload_returns_expected_structure(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image = Image.new("RGB", (320, 480), color=(255, 120, 80))
    image.save(image_path)

    payload = build_analysis_payload(image_path, "outfit")

    assert payload["category"] == "outfit"
    assert payload["style_tags"]
    assert payload["dominant_colors"]
    assert payload["analysis_mode"] == "live_engine"
    assert payload["image_summary"]["size"] == "portrait"
    assert payload["image_summary"]["dominant_color_family"] in {"warm", "cool", "neutral"}
    assert "fashion" in payload["fashion_summary"].lower()
    assert payload["fit_guidance"]


def test_build_analysis_payload_reports_tag_source(tmp_path: Path) -> None:
    image_path = tmp_path / "sample-model.png"
    image = Image.new("RGB", (400, 300), color=(30, 80, 140))
    image.save(image_path)

    payload = build_analysis_payload(image_path, "upper")

    assert payload["category"] == "upper"
    assert payload["tag_source"] in {"visual-classifier", "fallback-heuristic"}
    if payload["tag_source"] == "visual-classifier":
        assert payload["_embedding"]
        assert payload["aesthetic_confidence"] is not None
    else:
        assert payload["_embedding"] is None


def test_build_inspiration_payload_reports_data_source() -> None:
    payload = build_inspiration_payload("fashion outfit")

    assert payload["query"] == "fashion outfit"
    assert isinstance(payload["results"], list)
    assert payload["data_source"] in {"pinterest-api", "pexels", "no-results"}


def test_build_inspiration_payload_uses_uploaded_context() -> None:
    analyses = [
        {"category": "upper", "style_tags": ["casual", "upper-body", "layered"]},
        {"category": "lower", "style_tags": ["streetwear", "lower-body", "tailored"]},
        {"category": "accessories", "style_tags": ["accessories", "detail"]},
        {"category": "tattoo", "style_tags": ["tattoo", "statement"]},
    ]

    payload = build_inspiration_payload("generic fashion", analyses=analyses)

    assert "upper" in payload["query"]
    assert "lower" in payload["query"]
    assert "accessories" in payload["query"]
    assert "tattoo" in payload["query"]
    assert "layered" in payload["query"] or "streetwear" in payload["query"]


def test_build_recommendation_payload_groups_four_parts() -> None:
    analyses = [
        build_analysis_payload("sample-upper.png", "upper"),
        build_analysis_payload("sample-lower.png", "lower"),
        build_analysis_payload("sample-accessories.png", "accessories"),
        build_analysis_payload("sample-tattoo.png", "tattoo"),
    ]

    payload = build_recommendation_payload(analyses)

    assert payload["grouped_analysis"]["upper"]["category"] == "upper"
    assert payload["grouped_analysis"]["lower"]["category"] == "lower"
    assert payload["grouped_analysis"]["accessories"]["category"] == "accessories"
    assert payload["grouped_analysis"]["tattoo"]["category"] == "tattoo"
    assert payload["style_story"]
    assert payload["fit_focus"]
