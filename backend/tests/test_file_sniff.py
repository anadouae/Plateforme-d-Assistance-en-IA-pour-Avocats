"""Tests magic-bytes upload validation."""

from app.services.file_sniff import sniff_allowed_upload


def test_pdf_ok():
    assert sniff_allowed_upload(b"%PDF-1.4 fake", ".pdf") is None


def test_pdf_reject_text():
    assert sniff_allowed_upload(b"not a pdf", ".pdf") is not None


def test_png_ok():
    content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    assert sniff_allowed_upload(content, ".png") is None


def test_jpeg_ok():
    content = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert sniff_allowed_upload(content, ".jpg") is None


def test_docx_requires_zip():
    assert sniff_allowed_upload(b"plain text file here", ".docx") is not None


def test_empty_rejected():
    assert sniff_allowed_upload(b"", ".pdf") is not None
