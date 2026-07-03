from pathlib import Path

from PIL import Image

from server.app.services.image_service import build_analysis_payload


def test_build_analysis_payload_returns_expected_structure(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image = Image.new("RGB", (320, 480), color=(255, 120, 80))
    image.save(image_path)

    payload = build_analysis_payload(image_path, "outfit")

    assert payload["category"] == "outfit"
    assert payload["style_tags"]
    assert payload["dominant_colors"]
    assert payload["image_summary"]["size"] == "portrait"
