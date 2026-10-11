"""TIER: unit

Unit tests for slice 042 (vision negotiation).

No network, no sockets, no real keys: normalization operates on
in-memory content parts only.
"""

import base64

import pytest

from mythic_agent.providers import vision
from mythic_agent.providers.base import Provider, ProviderError


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

def _make_provider(name, vision_capable):
    flags = {"streaming": True, "tool_calling": False,
             "vision": vision_capable, "json_mode": False}

    def capabilities(self):
        return dict(flags)

    def chat(self, messages, **kwargs):
        raise ProviderError("fake: chat not implemented")

    return type(f"_Provider_{name}", (Provider,), {
        "name": name,
        "capabilities": capabilities,
        "chat": chat,
    })


_TINY_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64).decode()
_DATA_URL = f"data:image/png;base64,{_TINY_B64}"


def _image_part(url=_DATA_URL):
    return {"type": "image_url", "image_url": {"url": url}}


def _parts():
    return [{"type": "text", "text": "Describe this."}, _image_part()]


# ----------------------------------------------------------------------
# has_images()
# ----------------------------------------------------------------------

def test_has_images():
    assert vision.has_images(_parts()) is True
    assert vision.has_images([{"type": "text", "text": "x"}]) is False
    assert vision.has_images([]) is False
    assert vision.has_images(None) is False


# ----------------------------------------------------------------------
# normalize(): per-family wire shapes
# ----------------------------------------------------------------------

def test_normalize_openai_family_passthrough():
    provider = _make_provider("openai", True)()
    payload = vision.normalize(provider, _parts())
    assert payload.dropped == 0
    assert payload.images == []
    assert payload.content[0] == {"type": "text", "text": "Describe this."}
    image = payload.content[1]
    assert image["type"] == "image_url"
    assert image["image_url"]["url"] == _DATA_URL


def test_normalize_anthropic_shape():
    provider = _make_provider("anthropic", True)()
    payload = vision.normalize(provider, _parts())
    image = payload.content[1]
    assert image == {"type": "image",
                     "source": {"type": "base64",
                                "media_type": "image/png",
                                "data": _TINY_B64}}


def test_normalize_google_shape():
    provider = _make_provider("google", True)()
    payload = vision.normalize(provider, _parts())
    image = payload.content[1]
    assert image == {"type": "image", "mime_type": "image/png",
                     "data": _TINY_B64}


def test_normalize_ollama_message_level_images():
    provider = _make_provider("ollama", True)()
    payload = vision.normalize(provider, _parts())
    assert payload.images == [_TINY_B64]
    assert payload.content == [{"type": "text", "text": "Describe this."}]


def test_normalize_image_bytes_form():
    provider = _make_provider("anthropic", True)()
    parts = [{"type": "image_bytes", "mime_type": "image/jpeg",
              "data": _TINY_B64}]
    payload = vision.normalize(provider, parts)
    assert payload.content[0]["source"]["media_type"] == "image/jpeg"


def test_normalize_remote_url_openai_ok():
    provider = _make_provider("openai", True)()
    payload = vision.normalize(
        provider, [_image_part("https://example.com/pic.png")])
    assert payload.content[0]["image_url"]["url"] == \
        "https://example.com/pic.png"


def test_normalize_remote_url_rejected_where_base64_required():
    for name in ("anthropic", "google", "ollama"):
        provider = _make_provider(name, True)()
        with pytest.raises(ProviderError):
            vision.normalize(
                provider, [_image_part("https://example.com/pic.png")])


# ----------------------------------------------------------------------
# Downgrade policy
# ----------------------------------------------------------------------

def test_unsupported_vision_raise_by_default():
    provider = _make_provider("novision", False)()
    with pytest.raises(ProviderError) as excinfo:
        vision.normalize(provider, _parts())
    assert "novision" in str(excinfo.value)


def test_unsupported_vision_strip_drops_images():
    provider = _make_provider("novision", False)()
    payload = vision.normalize(provider, _parts(), on_unsupported="strip")
    assert payload.dropped == 1
    assert payload.content == [{"type": "text", "text": "Describe this."}]


def test_unsupported_vision_strip_all_images():
    provider = _make_provider("novision", False)()
    payload = vision.normalize(
        provider, [_image_part(), _image_part()], on_unsupported="strip")
    assert payload.dropped == 2
    assert payload.content == []


def test_invalid_policy_rejected():
    provider = _make_provider("novision", False)()
    with pytest.raises(ValueError):
        vision.normalize(provider, _parts(), on_unsupported="explode")


# ----------------------------------------------------------------------
# Failure and boundary behavior
# ----------------------------------------------------------------------

def test_malformed_parts_rejected():
    provider = _make_provider("openai", True)()
    for bad in ("nope", [{"type": "video", "url": "x"}],
                [{"type": "image_url", "image_url": {"url": "data:xx"}}],
                [{"type": "image_url",
                  "image_url": {"url": "data:image/png;base64,!!!notb64"}}],
                [{"type": "image_bytes", "mime_type": "image/png",
                  "data": ""}],
                [{"type": "text", "text": 42}],
                ["not-a-dict"]):
        with pytest.raises(ProviderError):
            vision.normalize(provider, bad)


def test_parts_must_be_list():
    provider = _make_provider("openai", True)()
    with pytest.raises(ProviderError):
        vision.normalize(provider, "nope")


def test_unsupported_mime_rejected():
    provider = _make_provider("openai", True)()
    part = {"type": "image_url",
            "image_url": {"url": f"data:image/tiff;base64,{_TINY_B64}"}}
    with pytest.raises(ProviderError):
        vision.normalize(provider, [part])


def test_oversize_image_rejected(monkeypatch):
    provider = _make_provider("openai", True)()
    monkeypatch.setattr(vision, "MAX_IMAGE_BYTES", 10)
    with pytest.raises(ProviderError):
        vision.normalize(provider, [_image_part()])


def test_empty_parts_ok():
    provider = _make_provider("openai", True)()
    payload = vision.normalize(provider, [])
    assert payload.content == [] and payload.dropped == 0
