from pathlib import Path

from PIL import Image

from server.app.services.image_service import build_analysis_payload, build_recommendation_payload


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


def test_build_analysis_payload_supports_model_backed_mode(tmp_path: Path) -> None:
    image_path = tmp_path / "sample-model.png"
    image = Image.new("RGB", (400, 300), color=(30, 80, 140))
    image.save(image_path)

    payload = build_analysis_payload(image_path, "upper", use_model=True)

    assert payload["analysis_mode"] in {"huggingface", "live_engine"}
    assert payload["category"] == "upper"


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
