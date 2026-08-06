"""Export plaidoirie → .docx réel (python-docx), ouvrable dans Microsoft Word."""

from __future__ import annotations

import io
import re
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", (name or "plaidoirie").strip())
    return (cleaned[:60] or "plaidoirie").strip("_")


def build_plaidoirie_docx(
    *,
    title: str,
    body: str,
    cabinet_name: str | None = None,
    lawyer_name: str | None = None,
    city: str | None = None,
) -> tuple[bytes, str]:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = "Traditional Arabic"
    style.font.size = Pt(13)

    h1 = doc.add_paragraph()
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h1.add_run("المملكة المغربية")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x1A, 0x3A, 0x2A)

    h2 = doc.add_paragraph()
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = h2.add_run("Royaume du Maroc")
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    kind = doc.add_paragraph()
    kind.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rk = kind.add_run("مرافعة · Plaidoirie")
    rk.bold = True
    rk.font.size = Pt(11)
    rk.font.color.rgb = RGBColor(0xC5, 0xA0, 0x28)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parts = [p for p in [cabinet_name, date.today().isoformat()] if p]
    meta.add_run(" — ".join(parts)).font.size = Pt(9)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title_p.add_run(title.strip())
    tr.bold = True
    tr.font.size = Pt(14)
    tr.font.underline = True

    for block in re.split(r"\n\s*\n", (body or "").strip()):
        text = block.strip()
        if not text:
            continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5
        run = p.add_run(text.replace("\n", " "))
        run.font.size = Pt(12)

    if lawyer_name or city:
        sign = doc.add_paragraph()
        sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        sign.paragraph_format.space_before = Pt(28)
        lines = []
        if city:
            lines.append(f"حرر بـ{city}")
        lines.append("التوقيع")
        if lawyer_name:
            lines.append(lawyer_name)
        sign.add_run("\n".join(lines)).bold = True

    buf = io.BytesIO()
    doc.save(buf)
    filename = f"{_safe_filename(title)}.docx"
    return buf.getvalue(), filename
