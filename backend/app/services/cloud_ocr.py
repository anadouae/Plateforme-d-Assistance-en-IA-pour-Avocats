"""OCR cloud haute qualité (Mistral OCR → Gemini).

Les scans / PDF image ne passent plus par Tesseract CPU (lent et fragile).
Les clés API restent dans settings — jamais loguées.
"""

from __future__ import annotations

import base64
import logging
import re

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_MD_IMG = re.compile(r"!\[[^\]]*\]\([^)]+\)")


def _strip_markdown_noise(text: str) -> str:
    text = _MD_IMG.sub("", text or "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pages_to_text(pages: list) -> str:
    parts: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            markdown = getattr(page, "markdown", "") or getattr(page, "text", "") or ""
        else:
            markdown = page.get("markdown") or page.get("text") or ""
        markdown = (markdown or "").strip()
        if markdown:
            parts.append(markdown)
    return _strip_markdown_noise("\n\n".join(parts))


def _mistral_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.MISTRAL_API_KEY}"}


def _mistral_base() -> str:
    return (settings.MISTRAL_BASE_URL or "https://api.mistral.ai/v1").rstrip("/")


def _mistral_ocr_model() -> str:
    return getattr(settings, "MISTRAL_OCR_MODEL", None) or "mistral-ocr-latest"


def _mistral_delete_file(client: httpx.Client, file_id: str) -> None:
    try:
        client.delete(f"{_mistral_base()}/files/{file_id}", headers=_mistral_headers())
    except Exception:
        pass


def _mistral_ocr_via_upload(content: bytes, filename: str, mime: str) -> str:
    timeout = float(getattr(settings, "OCR_CLOUD_TIMEOUT_SEC", 90) or 90)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        up = client.post(
            f"{_mistral_base()}/files",
            headers=_mistral_headers(),
            files={"file": (filename or "document.pdf", content, mime)},
            data={"purpose": "ocr"},
        )
        if up.status_code >= 400:
            logger.warning("Mistral OCR upload failed: HTTP %s", up.status_code)
            return ""
        file_id = (up.json() or {}).get("id")
        if not file_id:
            return ""
        try:
            payload_file = {
                "model": _mistral_ocr_model(),
                "document": {"type": "file", "file_id": file_id},
            }
            ocr = client.post(
                f"{_mistral_base()}/ocr",
                headers={**_mistral_headers(), "Content-Type": "application/json"},
                json=payload_file,
            )
            if ocr.status_code >= 400:
                signed = client.get(
                    f"{_mistral_base()}/files/{file_id}/url",
                    headers=_mistral_headers(),
                    params={"expiry": 24},
                )
                url = ""
                if signed.status_code < 400:
                    url = (signed.json() or {}).get("url") or ""
                if not url:
                    return ""
                ocr = client.post(
                    f"{_mistral_base()}/ocr",
                    headers={**_mistral_headers(), "Content-Type": "application/json"},
                    json={
                        "model": _mistral_ocr_model(),
                        "document": {"type": "document_url", "document_url": url},
                    },
                )
            if ocr.status_code >= 400:
                logger.warning("Mistral OCR process failed: HTTP %s", ocr.status_code)
                return ""
            data = ocr.json() or {}
            return _pages_to_text(data.get("pages") or [])
        finally:
            _mistral_delete_file(client, file_id)


def _mistral_ocr_document(content: bytes, filename: str, mime: str) -> str:
    if not (settings.MISTRAL_API_KEY or "").strip():
        return ""
    if not content:
        return ""
    try:
        text = _mistral_ocr_via_upload(content, filename, mime)
        if text:
            return text
    except Exception as exc:
        logger.warning("Mistral OCR error: %s", type(exc).__name__)
    return ""


def _gemini_ocr_document(content: bytes, mime: str) -> str:
    key = (settings.GEMINI_API_KEY or "").strip()
    if not key or not content:
        return ""
    # Gemini inline PDF ~20 Mo
    if len(content) > 20 * 1024 * 1024:
        return ""
    model = settings.GEMINI_MODEL or "gemini-2.5-flash"
    timeout = float(getattr(settings, "OCR_CLOUD_TIMEOUT_SEC", 90) or 90)
    prompt = (
        "Extract ALL text from this document, faithfully and completely. "
        "Keep original language (Arabic, French, or mixed). "
        "Preserve reading order, headings, tables as plain text, names, dates, amounts. "
        "Do not summarize. Do not translate. Output only the extracted text."
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": mime,
                                        "data": base64.b64encode(content).decode("ascii"),
                                    }
                                },
                                {"text": prompt},
                            ]
                        }
                    ],
                    "generationConfig": {"maxOutputTokens": 65536, "temperature": 0},
                },
            )
        if r.status_code >= 400:
            logger.warning("Gemini OCR failed: HTTP %s", r.status_code)
            return ""
        data = r.json() or {}
        parts = (
            (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts"))
            or []
        )
        text = "".join(p.get("text") or "" for p in parts if isinstance(p, dict))
        return _strip_markdown_noise(text)
    except Exception as exc:
        logger.warning("Gemini OCR error: %s", type(exc).__name__)
        return ""


def cloud_ocr_available() -> bool:
    if not getattr(settings, "OCR_CLOUD_ENABLED", True):
        return False
    return bool(
        (settings.MISTRAL_API_KEY or "").strip()
        or (settings.GEMINI_API_KEY or "").strip()
    )


def ocr_document_cloud(
    content: bytes,
    *,
    filename: str = "document.pdf",
    mime: str = "application/pdf",
) -> tuple[str, int | None]:
    """OCR haute qualité via cloud. Retourne (texte, score) ou ('', 0)."""
    if not cloud_ocr_available() or not content:
        return "", 0

    text = _mistral_ocr_document(content, filename, mime)
    if text and len(text) >= 40:
        logger.info("Cloud OCR Mistral ok (%d chars)", len(text))
        return text, 96

    text = _gemini_ocr_document(content, mime)
    if text and len(text) >= 40:
        logger.info("Cloud OCR Gemini ok (%d chars)", len(text))
        return text, 92

    return "", 0
