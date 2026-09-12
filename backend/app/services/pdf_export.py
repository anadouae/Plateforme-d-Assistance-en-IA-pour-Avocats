"""Export plaidoirie → PDF réel (PyMuPDF) — corps arabe réellement RTL."""

from __future__ import annotations

import logging
import re
import tempfile
from datetime import date
from pathlib import Path

from app.services.docx_export import _ensure_export_preamble
from app.services.plaidoirie_layout import (
    is_section_heading,
    prepare_plaidoirie_blocks,
    split_typography_runs,
)
from app.services.plaidoirie_postprocess import postprocess_plaidoirie_body

logger = logging.getLogger(__name__)

_ASSETS = Path(__file__).resolve().parents[1] / "assets"
_FONT_REG = _ASSETS / "NotoNaskhArabic-Regular.ttf"
_FONT_BOLD = _ASSETS / "NotoNaskhArabic-Bold.ttf"

_CSS = """
@font-face {
  font-family: Naskh;
  src: url(NotoNaskhArabic-Regular.ttf);
  font-weight: normal;
}
@font-face {
  font-family: Naskh;
  src: url(NotoNaskhArabic-Bold.ttf);
  font-weight: bold;
}
* { box-sizing: border-box; }
body, p, td, div, span {
  font-family: Naskh, serif;
}
"""


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", (name or "plaidoirie").strip())
    return (cleaned[:60] or "plaidoirie").strip("_")


def _escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _logo_ext(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


def _mostly_arabic(s: str) -> bool:
    ar = sum(1 for c in s if "\u0600" <= c <= "\u06FF")
    lat = sum(1 for c in s if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return ar > lat


def _block_kind(text: str) -> str:
    t = (text or "").strip()
    if is_section_heading(t):
        return "sec"
    if re.match(r"^(?:واحسبكم|وذلك\s*مع\s*الاحتفاظ|تحت\s*جميع)", t):
        return "close"
    if "[يُستكمل" in t or "يُستكمل" in t or "……" in t:
        return "todo"
    if re.match(r"^(?:–|-)\s+\S", t) or re.match(r"^\d{1,2}\s*[.)]", t):
        return "item"
    return "p"


def _inner_html(text: str) -> str:
    """Runs RTL + îlots LTR (comme Word) pour éviter chiffres/noms à l'envers."""
    parts: list[str] = []
    for chunk, bold, ltr in split_typography_runs(text):
        if not chunk:
            continue
        esc = _escape(chunk)
        weight = "font-weight:bold;" if bold else ""
        if ltr:
            parts.append(
                f'<span dir="ltr" style="unicode-bidi:embed;direction:ltr;{weight}">{esc}</span>'
            )
        elif bold:
            parts.append(f'<span style="{weight}">{esc}</span>')
        else:
            parts.append(esc)
    return "".join(parts) if parts else _escape(text)


def _para_html(text: str, kind: str) -> str:
    inner = _inner_html(text)
    base = (
        'dir="rtl" style="margin:0;width:100%;text-align:right;direction:rtl;'
        'unicode-bidi:embed;font-family:Naskh,serif;'
    )
    if kind == "title":
        return (
            f'<p dir="rtl" style="margin:0;width:100%;text-align:center;direction:rtl;'
            f'unicode-bidi:embed;font-family:Naskh,serif;font-size:14pt;font-weight:bold;'
            f'color:#1a3a2a;text-decoration:underline;">{inner}</p>'
        )
    if kind == "meta":
        return f'<p {base}font-size:10.5pt;color:#334155;">{inner}</p>'
    if kind == "sec":
        return (
            f'<p {base}font-size:12.5pt;font-weight:bold;color:#1F4E79;">{inner}</p>'
        )
    if kind == "close":
        return (
            f'<p {base}font-size:12pt;font-weight:bold;color:#1F4E79;">{inner}</p>'
        )
    if kind == "todo":
        return (
            f'<p {base}font-size:12pt;font-weight:bold;color:#b45309;">{inner}</p>'
        )
    # item / p
    return f'<p {base}font-size:11.5pt;line-height:1.45;">{inner}</p>'


def _put_html(page, rect, html: str, css: str, archive, *, scale_low: float = 1.0) -> float:
    wrapped = (
        f'<div dir="rtl" style="direction:rtl;text-align:right;width:100%;'
        f'unicode-bidi:embed;">{html}</div>'
    )
    result = page.insert_htmlbox(
        rect, wrapped, css=css, archive=archive, scale_low=scale_low
    )
    if isinstance(result, (tuple, list)):
        return float(result[0])
    return float(result)


def _draw_letterhead(
    page,
    box,
    *,
    name_fr: str,
    name_ar: str,
    logo_path: Path | None,
    css: str,
    archive,
) -> float:
    """
    Même disposition que Word : AR (gauche) | logo CENTRÉ | FR (droite).
    Logo placé en coordonnées absolues (fiable), pas seulement en cellule HTML.
    """
    y0 = box.y0
    head_h = 78.0
    mid_x = (box.x0 + box.x1) / 2.0
    logo_w, logo_h = 56.0, 56.0

    if logo_path and logo_path.is_file():
        try:
            img_rect = fitz_rect(
                mid_x - logo_w / 2,
                y0 + 4,
                mid_x + logo_w / 2,
                y0 + 4 + logo_h,
            )
            page.insert_image(img_rect, filename=logo_path.as_posix(), keep_proportion=True)
        except Exception as exc:
            logger.warning("Logo PDF insert_image: %s", exc)

    col_w = (box.x1 - box.x0 - logo_w - 16) / 2.0
    left = fitz_rect(box.x0, y0, box.x0 + col_w, y0 + head_h)
    right = fitz_rect(box.x1 - col_w, y0, box.x1, y0 + head_h)

    if name_fr:
        fr_html = (
            f'<p dir="ltr" style="margin:0;text-align:left;direction:ltr;'
            f'font-family:Naskh,serif;font-size:11pt;font-weight:bold;color:#0B1A4D;">'
            f"{_escape(name_fr)}</p>"
        )
        page.insert_htmlbox(left, fr_html, css=css, archive=archive)

    if name_ar:
        ar_html = (
            f'<p dir="rtl" style="margin:0;text-align:right;direction:rtl;'
            f'font-family:Naskh,serif;font-size:12pt;font-weight:bold;color:#1a3a2a;">'
            f"{_escape(name_ar)}</p>"
        )
        _put_html(page, right, ar_html, css, archive)

    line_y = y0 + head_h - 2
    page.draw_line(
        fitz_point(box.x0, line_y),
        fitz_point(box.x1, line_y),
        color=(0x1A / 255, 0x3A / 255, 0x2A / 255),
        width=1.5,
    )
    return line_y + 14


def fitz_rect(x0, y0, x1, y1):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # type: ignore
    return fitz.Rect(x0, y0, x1, y1)


def fitz_point(x, y):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # type: ignore
    return fitz.Point(x, y)


def build_plaidoirie_pdf(
    *,
    title: str,
    body: str,
    cabinet_name: str | None = None,
    cabinet_name_ar: str | None = None,
    lawyer_name: str | None = None,
    city: str | None = None,
    case_reference: str | None = None,
    client_name: str | None = None,
    cabinet_logo_bytes: bytes | None = None,
    include_esignature: bool = False,
    plaidoirie_type: str | None = None,
) -> tuple[bytes, str]:
    """Retourne (bytes PDF, filename.pdf) — structure alignée sur build_plaidoirie_docx."""
    body = _ensure_export_preamble(
        body,
        case_reference=case_reference,
        client_name=client_name,
    )
    body, _section_warn = postprocess_plaidoirie_body(
        body,
        source_text=body,
        plaidoirie_type=plaidoirie_type,
        for_export=True,
    )
    if not _FONT_REG.is_file():
        raise FileNotFoundError(f"Police arabe manquante: {_FONT_REG}")

    today = date.today().strftime("%d/%m/%Y")
    name_fr = (cabinet_name or "").strip()
    name_ar = (cabinet_name_ar or "").strip()
    if name_fr and _mostly_arabic(name_fr):
        if not name_ar:
            name_ar = name_fr
        name_fr = ""
    if not name_ar and name_fr:
        name_ar = name_fr
    # Éviter doublon AR dans la colonne FR
    if name_fr and name_ar and name_fr == name_ar:
        name_fr = ""

    city_ar = (city or "").strip()
    if city_ar.lower() in ("casablanca", "casa"):
        city_ar = "الدار البيضاء"

    meta_lines: list[str] = []
    if lawyer_name:
        meta_lines.append(f"المحامي : {lawyer_name}")
    if case_reference:
        meta_lines.append(f"مرجع الملف : {case_reference}")
    if city_ar:
        meta_lines.append(f"{city_ar}، في {today}")
    else:
        meta_lines.append(f"تاريخ التحرير : {today}")

    sign_lines: list[str] = []
    if city_ar:
        sign_lines.append(f"حرر بـ {city_ar}")
    if include_esignature and lawyer_name:
        sign_lines.append("التوقيع الإلكتروني")
        sign_lines.append(lawyer_name)
        sign_lines.append(today)
    else:
        sign_lines.append("التوقيع")
        if lawyer_name:
            sign_lines.append(lawyer_name)
        sign_lines.append("خاتم المحامي")

    blocks: list[tuple[str, str]] = [("meta", line) for line in meta_lines]
    blocks.append(("title", (title or "").strip() or "مرافعة"))
    for text in prepare_plaidoirie_blocks(body):
        blocks.append((_block_kind(text), text))
    for i, line in enumerate(sign_lines):
        blocks.append(("close" if i == 0 else "meta", line))

    try:
        import pymupdf as fitz
    except ImportError:
        import fitz  # type: ignore

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for font in (_FONT_REG, _FONT_BOLD):
            if font.is_file():
                (tmp_path / font.name).write_bytes(font.read_bytes())
        logo_path: Path | None = None
        if cabinet_logo_bytes:
            try:
                logo_path = tmp_path / f"cabinet_logo{_logo_ext(cabinet_logo_bytes)}"
                logo_path.write_bytes(cabinet_logo_bytes)
            except Exception as exc:
                logger.warning("Logo cabinet PDF ignoré: %s", exc)
                logo_path = None
        if not logo_path:
            for cand in (
                _ASSETS / "armoiries-maroc.png",
                Path("/app/app/assets/armoiries-maroc.png"),
                Path("/opt/sanad/backend/app/assets/armoiries-maroc.png"),
                Path("/opt/lexhub/backend/app/assets/armoiries-maroc.png"),
                Path(__file__).resolve().parents[3] / "frontend" / "public" / "armoiries-maroc.png",
                Path("/opt/sanad/frontend/public/armoiries-maroc.png"),
                Path("/opt/lexhub/frontend/public/armoiries-maroc.png"),
            ):
                if cand.is_file():
                    logo_path = cand
                    break

        archive = fitz.Archive(tmp_path.as_posix())
        doc = fitz.open()
        page_rect = fitz.paper_rect("a4")
        ml, mt, mr, mb = 56, 50, 56, 54

        def _new_page():
            pg = doc.new_page(width=page_rect.width, height=page_rect.height)
            usable = fitz.Rect(ml, mt, page_rect.width - mr, page_rect.height - mb)
            return pg, usable

        page, box = _new_page()
        y = _draw_letterhead(
            page,
            box,
            name_fr=name_fr,
            name_ar=name_ar,
            logo_path=logo_path,
            css=_CSS,
            archive=archive,
        )

        for kind, text in blocks:
            html = _para_html(text, kind)
            gap = 9 if kind == "sec" else 8 if kind == "title" else 5
            min_remaining = 85 if kind == "sec" else 55 if kind == "title" else 30
            remaining = box.y1 - y
            if remaining < min_remaining:
                page, box = _new_page()
                y = box.y0
                remaining = box.y1 - y
            rect = fitz.Rect(box.x0, y, box.x1, box.y1)
            spare = _put_html(page, rect, html, _CSS, archive)
            if spare < 0:
                page, box = _new_page()
                y = box.y0
                remaining = box.y1 - y
                rect = fitz.Rect(box.x0, y, box.x1, box.y1)
                spare = _put_html(page, rect, html, _CSS, archive)
                if spare < 0:
                    _put_html(page, rect, html, _CSS, archive, scale_low=0)
                    page, box = _new_page()
                    y = box.y0
                    continue
            y += max(remaining - spare, 16) + gap

        try:
            doc.subset_fonts()
        except Exception:
            pass
        try:
            pdf_bytes = doc.tobytes(garbage=4, deflate=True)
        except TypeError:
            pdf_bytes = doc.tobytes()
        doc.close()

    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("Génération PDF invalide (pas d'en-tête %PDF)")
    return pdf_bytes, f"{_safe_filename(title)}.pdf"
