# -*- coding: utf-8 -*-
"""Local preview with full compose + typography."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.plaidoirie_postprocess import fidelity_structure_plaidoirie, postprocess_plaidoirie_body
from app.services.docx_export import build_plaidoirie_docx

SRC = (ROOT / "scripts" / "_amrani_dictation.txt").read_text(encoding="utf-8")
_logo = next(
    (p.read_bytes() for p in [
        ROOT / "frontend" / "public" / "logo-sanad-final.png",
        ROOT / "frontend" / "public" / "logofinale.png",
    ] if p.is_file()),
    None,
)

body = fidelity_structure_plaidoirie(SRC)
body, checks = postprocess_plaidoirie_body(
    body, source_text=SRC, plaidoirie_type="social-travail", for_export=True
)
title = "مرافعة — يوسف العمراني / أطلس تكستيل"
docx_bytes, _ = build_plaidoirie_docx(
    title=title,
    body=body,
    cabinet_name="Cabinet Démo Atlas",
    lawyer_name="دعاء العسال",
    city="الدار البيضاء",
    plaidoirie_type="social-travail",
    cabinet_logo_bytes=_logo,
)
out = Path.home() / "Desktop" / "Plaidoirie_Amrani_HEADER.docx"
out.write_bytes(docx_bytes)
print("WROTE", out, len(docx_bytes), "checks", checks)
