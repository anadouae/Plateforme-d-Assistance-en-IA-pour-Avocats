# -*- coding: utf-8 -*-
"""Generate fidelity compose preview for Cursor validation."""
from __future__ import annotations

from pathlib import Path

from app.services.dictation import compose_official_document
from app.services.docx_export import build_plaidoirie_docx

ROOT = Path(__file__).resolve().parents[1]
_logo_candidates = [
    ROOT / "frontend" / "public" / "logo-sanad-final.png",
    ROOT / "frontend" / "public" / "logofinale.png",
    ROOT / "frontend" / "public" / "logo-sanad.png",
]
_logo = next((p.read_bytes() for p in _logo_candidates if p.is_file()), None)

SRC = Path("/tmp/_amrani_src.txt").read_text(encoding="utf-8") if Path("/tmp/_amrani_src.txt").exists() else ""

title, body, provider, checks = compose_official_document(
    SRC,
    doc_type="plaidoirie",
    title="مرافعة — يوسف العمراني / أطلس تكستيل",
    plaidoirie_type="social-travail",
    language="ar",
    city="الدار البيضاء",
    cabinet_name="Cabinet Démo Atlas",
)
print("===META===")
print("PROVIDER:", provider)
print("TITLE:", title)
print("CHECKS:", checks)
print("===BODY===")
print(body)
docx_bytes, fname = build_plaidoirie_docx(
    title=title,
    body=body,
    cabinet_name="Cabinet Démo Atlas",
    lawyer_name="دعاء العسال",
    city="الدار البيضاء",
    plaidoirie_type="social-travail",
    cabinet_logo_bytes=_logo,
)
out = Path("/tmp/preview_amrani.docx")
out.write_bytes(docx_bytes)
print("===DOCX===", out, len(docx_bytes), fname)
