from server.app.services.caption_service import build_caption_payload


def test_build_caption_payload_returns_normal_and_trendy_captions() -> None:
    payload = build_caption_payload(["streetwear", "y2k"], title="Layered denim look")

    assert payload["captions"]["normal"]
    assert payload["captions"]["trendy"]
    assert payload["caption_source"] in {"text-generation-model", "template-fallback"}
    assert payload["aesthetic"] == "streetwear"


def test_build_caption_payload_handles_missing_tags() -> None:
    payload = build_caption_payload([], title=None)

    assert payload["aesthetic"] == "fashion"
    assert payload["captions"]["normal"]
    assert payload["captions"]["trendy"]
