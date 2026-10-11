"""Vision negotiation (Slice 042).

Canonical content-part input (OpenAI shape) is normalized into the
provider's own wire shape per adapter family; providers without vision
support either raise or degrade, by policy.

Input parts:

* ``{"type": "text", "text": "..."}``
* ``{"type": "image_url", "image_url": {"url": ...}}`` — ``url`` is a
  ``data:<mime>;base64,<payload>`` URL, an ``http(s)`` URL, or a bare
  base64 payload (mime must then come from ``mime_type``).
* ``{"type": "image_bytes", "mime_type": "image/png", "data": "<b64>"}``
  — raw-bytes convenience form.

Wire shapes produced by :func:`normalize`:

* OpenAI-family (``openai``, ``openrouter``, ``deepseek``, ``vllm``,
  ``lmstudio``, ``llama.cpp``, ``local-openai``): canonical
  ``image_url`` parts, data URLs re-emitted in canonical
  ``data:<mime>;base64,`` form.
* ``anthropic``: ``{"type": "image", "source": {"type": "base64",
  "media_type": ..., "data": ...}}``. Remote ``http(s)`` URLs raise —
  the Messages API needs base64.
* ``google``: ``{"type": "image", "mime_type": ..., "data": ...}``
  inline-data parts (the shape the Gemini SDK accepts).
* ``ollama``: vision travels at the *message* level — text parts stay
  in ``content`` and base64 payloads go into ``images``.

Downgrade policy (``on_unsupported``):

* ``"raise"`` (default): :class:`ProviderError` naming the provider.
* ``"strip"``: image parts are dropped, text survives; the count is
  reported in :attr:`VisionPayload.dropped` so callers can log it.

No network is touched; all work is on in-memory shapes.
"""


from __future__ import annotations

__all__ = [
    "MAX_IMAGE_BYTES",
    "Provider",
    "ProviderError",
    "VisionPayload",
    "has_images",
    "normalize",
]

import base64
import binascii
from dataclasses import dataclass, field
from typing import Any

from .base import Provider, ProviderError


#: Refuse images larger than this after base64 decoding (boundary guard).
MAX_IMAGE_BYTES = 20 * 1024 * 1024


#: provider.name -> wire family.
_FAMILIES: dict[str, str] = {
    "openai": "openai",
    "openrouter": "openai",
    "deepseek": "openai",
    "vllm": "openai",
    "lmstudio": "openai",
    "llama.cpp": "openai",
    "local-openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "ollama": "ollama",
}

#: MIME types accepted for image parts.
_ALLOWED_MIME = {
    "image/png", "image/jpeg", "image/webp", "image/gif",
}


@dataclass
class VisionPayload:
    """Normalized vision request for one message."""

    #: Content parts in the provider's wire shape.
    content: list[dict[str, Any]] = field(default_factory=list)
    #: Message-level base64 images (Ollama); empty for other families.
    images: list[str] = field(default_factory=list)
    #: Image parts dropped by the "strip" downgrade policy.
    dropped: int = 0


def has_images(parts: list[dict[str, Any]]) -> bool:
    """True when any part is an image part."""
    return any(isinstance(part, dict) and part.get("type") in
               ("image_url", "image_bytes") for part in (parts or []))


def _decode_b64(data: str, where: str) -> str:
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ProviderError(f"{where}: invalid base64 image data.") from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise ProviderError(
            f"{where}: image is {len(raw)} bytes, over the "
            f"{MAX_IMAGE_BYTES}-byte limit.")
    return data


def _split_data_url(url: str, where: str) -> tuple[str, str]:
    """Split ``data:<mime>;base64,<payload>`` into (mime, payload)."""
    if not url.startswith("data:"):
        raise ProviderError(f"{where}: expected a data: URL, got {url[:32]!r}")
    try:
        header, payload = url[5:].split(",", 1)
    except ValueError as exc:
        raise ProviderError(f"{where}: malformed data: URL.") from exc
    if ";base64" not in header:
        raise ProviderError(f"{where}: data: URL must be base64-encoded.")
    mime = header.split(";")[0].strip().lower() or "image/png"
    if mime not in _ALLOWED_MIME:
        raise ProviderError(
            f"{where}: unsupported image MIME type {mime!r}.")
    _decode_b64(payload, where)
    return mime, payload


def _image_source(part: dict[str, Any], index: int) -> tuple[str, str, Any]:
    """Return (mime_type, b64_payload, http_url_or_None) for an image part."""
    where = f"parts[{index}]"
    kind = part.get("type")
    if kind == "image_url":
        image_url = part.get("image_url") or {}
        url = image_url.get("url", "")
        if not isinstance(url, str) or not url:
            raise ProviderError(f"{where}: image_url.url must be a string.")
        if url.startswith("data:"):
            mime, payload = _split_data_url(url, where)
            return mime, payload, None
        if url.startswith(("http://", "https://")):
            return "", "", url
        # Bare base64 payload; MIME from the sibling key or default.
        mime = str(image_url.get("mime_type", "image/png")).lower()
        if mime not in _ALLOWED_MIME:
            raise ProviderError(
                f"{where}: unsupported image MIME type {mime!r}.")
        _decode_b64(url, where)
        return mime, url, None
    if kind == "image_bytes":
        mime = str(part.get("mime_type", "")).lower()
        if mime not in _ALLOWED_MIME:
            raise ProviderError(
                f"{where}: image_bytes needs an allowed 'mime_type'.")
        data = part.get("data", "")
        if not isinstance(data, str) or not data:
            raise ProviderError(f"{where}: image_bytes 'data' must be b64.")
        _decode_b64(data, where)
        return mime, data, None
    raise ProviderError(
        f"{where}: unknown part type {kind!r}; expected 'text', "
        "'image_url' or 'image_bytes'.")


def _check_text(part: dict[str, Any], index: int) -> dict[str, Any]:
    text = part.get("text", "")
    if not isinstance(text, str):
        raise ProviderError(
            f"parts[{index}]: text part 'text' must be a string.")
    return {"type": "text", "text": text}


def normalize(
    provider: Provider,
    parts: list[dict[str, Any]],
    *,
    on_unsupported: str = "raise",
) -> VisionPayload:
    """Normalize ``parts`` into the provider's vision wire shape.

    ``on_unsupported`` is ``"raise"`` (default) or ``"strip"`` — see the
    module docstring. Malformed parts raise :class:`ProviderError`
    regardless of policy.
    """
    if on_unsupported not in ("raise", "strip"):
        raise ValueError(
            f"on_unsupported must be 'raise' or 'strip', "
            f"got {on_unsupported!r}")
    if not isinstance(parts, list):
        raise ProviderError(
            f"parts must be a list, got {type(parts).__name__}")

    if not provider.capabilities().get("vision", False):
        if on_unsupported == "raise":
            raise ProviderError(
                f"Provider {provider.name!r} does not support vision; "
                "strip image parts (on_unsupported='strip') or use a "
                "vision-capable provider.")
        payload = VisionPayload()
        for index, part in enumerate(parts):
            if not isinstance(part, dict):
                raise ProviderError(
                    f"parts[{index}] must be a dict, "
                    f"got {type(part).__name__}")
            if part.get("type") in ("image_url", "image_bytes"):
                payload.dropped += 1
            elif part.get("type") == "text":
                payload.content.append(_check_text(part, index))
            else:
                raise ProviderError(
                    f"parts[{index}]: unknown part type "
                    f"{part.get('type')!r}.")
        return payload

    family = _FAMILIES.get(
        (getattr(provider, "name", "") or "").lower(), "openai")
    payload = VisionPayload()
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            raise ProviderError(
                f"parts[{index}] must be a dict, "
                f"got {type(part).__name__}")
        kind = part.get("type")
        if kind == "text":
            payload.content.append(_check_text(part, index))
            continue
        mime, b64data, http_url = _image_source(part, index)
        if family == "anthropic":
            if http_url:
                raise ProviderError(
                    f"parts[{index}]: Anthropic needs base64 image data, "
                    "not a remote URL.")
            payload.content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime,
                           "data": b64data},
            })
        elif family == "google":
            if http_url:
                raise ProviderError(
                    f"parts[{index}]: Google inline data needs base64 "
                    "image data, not a remote URL.")
            payload.content.append({
                "type": "image",
                "mime_type": mime,
                "data": b64data,
            })
        elif family == "ollama":
            if http_url:
                raise ProviderError(
                    f"parts[{index}]: Ollama needs base64 image data, "
                    "not a remote URL.")
            payload.images.append(b64data)
        else:  # openai family
            url = (f"data:{mime};base64,{b64data}"
                   if not http_url else http_url)
            payload.content.append({
                "type": "image_url",
                "image_url": {"url": url},
            })
    return payload
