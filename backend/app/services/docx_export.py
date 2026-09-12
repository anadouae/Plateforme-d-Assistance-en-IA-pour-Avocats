"""Export plaidoirie → .docx réel (python-docx), ouvrable dans Microsoft Word."""

from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor

from app.services.plaidoirie_layout import (
    is_section_heading,
    normalize_arabic_commas,
    prepare_plaidoirie_blocks,
    split_typography_runs,
)
from app.services.plaidoirie_postprocess import postprocess_plaidoirie_body

_ARMS_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "assets" / "armoiries-maroc.png",
    Path(__file__).resolve().parents[3] / "frontend" / "public" / "armoiries-maroc.png",
    Path("/app/app/assets/armoiries-maroc.png"),
    Path("/opt/lexhub/frontend/public/armoiries-maroc.png"),
    Path("/opt/sanad/frontend/public/armoiries-maroc.png"),
]

_SECTION_COLOR = RGBColor(0x1F, 0x4E, 0x79)
_META_COLOR = RGBColor(0x33, 0x41, 0x55)
_LTR_RE = re.compile(r"[A-Za-z]")


def _arms_path() -> Path | None:
    for p in _ARMS_CANDIDATES:
        if p.is_file():
            return p
    return None


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", (name or "plaidoirie").strip())
    return (cleaned[:60] or "plaidoirie").strip("_")


def _set_run_rtl(run) -> None:
    run.font.name = "Traditional Arabic"
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Traditional Arabic")
    rFonts.set(qn("w:hAnsi"), "Traditional Arabic")
    rFonts.set(qn("w:cs"), "Traditional Arabic")
    rtl = OxmlElement("w:rtl")
    rPr.append(rtl)


def _set_paragraph_ltr(paragraph, *, align: str = "left") -> None:
    """Paragraphe LTR (colonne cabinet, texte latin)."""
    pPr = paragraph._element.get_or_add_pPr()
    for tag in ("bidi", "jc"):
        existing = pPr.find(qn(f"w:{tag}"))
        if existing is not None:
            pPr.remove(existing)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), align)
    pPr.append(jc)
    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def _set_table_visual_ltr(table) -> None:
    """Tableau en ordre LTR : col.0 = gauche (cabinet), col.1 = droite (royaume)."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    bidi_visual = tblPr.find(qn("w:bidiVisual"))
    if bidi_visual is None:
        bidi_visual = OxmlElement("w:bidiVisual")
        tblPr.append(bidi_visual)
    bidi_visual.set(qn("w:val"), "0")


# Avec w:bidi, Word inverse gauche/droite : jc=left → marge physique droite.
_RTL_JC = {"right": "left", "left": "right", "center": "center", "both": "both"}


def _set_paragraph_rtl(paragraph, *, align: str = "right") -> None:
    """Paragraphe RTL — align = marge physique souhaitée (right = texte à droite)."""
    pPr = paragraph._element.get_or_add_pPr()
    for tag in ("bidi", "jc"):
        existing = pPr.find(qn(f"w:{tag}"))
        if existing is not None:
            pPr.remove(existing)
    pPr.append(OxmlElement("w:bidi"))
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), _RTL_JC.get(align, align))
    pPr.append(jc)


def _set_run_ltr(run) -> None:
    run.font.name = "Calibri"
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:hAnsi"), "Calibri")
    rtl = OxmlElement("w:rtl")
    rtl.set(qn("w:val"), "0")
    rPr.append(rtl)


def _paragraph_border_top(paragraph) -> None:
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "single")
    top.set(qn("w:sz"), "6")
    top.set(qn("w:space"), "4")
    top.set(qn("w:color"), "B0BEC5")
    pBdr.append(top)


def _paragraph_border_bottom(paragraph) -> None:
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1F4E79")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _keep_with_next(paragraph) -> None:
    pPr = paragraph._element.get_or_add_pPr()
    keep_next = OxmlElement("w:keepNext")
    pPr.append(keep_next)


def _set_table_ind_zero(table) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tbl_ind = tblPr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tblPr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "0")
    tbl_ind.set(qn("w:type"), "dxa")


def _set_table_column_layout(table, doc, col_widths: list[int]) -> None:
    """Tableau pleine largeur avec colonnes explicites (twips)."""
    section = doc.sections[0]
    usable_twips = Emu(section.page_width - section.left_margin - section.right_margin).twips
    if sum(col_widths) != usable_twips:
        total = sum(col_widths)
        col_widths = [int(usable_twips * w / total) for w in col_widths]
        col_widths[-1] = usable_twips - sum(col_widths[:-1])
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tbl_w = tblPr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tblPr.insert(0, tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(usable_twips))
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")
    _set_table_ind_zero(table)
    tbl_grid = tbl.find(qn("w:tblGrid"))
    if tbl_grid is not None:
        for grid_col, width in zip(tbl_grid.findall(qn("w:gridCol")), col_widths):
            grid_col.set(qn("w:w"), str(width))
    for cell, width in zip(table.rows[0].cells, col_widths):
        tc_pr = cell._tc.get_or_add_tcPr()
        tc_w = tc_pr.find(qn("w:tcW"))
        if tc_w is None:
            tc_w = OxmlElement("w:tcW")
            tc_pr.append(tc_w)
        tc_w.set(qn("w:type"), "dxa")
        tc_w.set(qn("w:w"), str(width))
        v_align = tc_pr.find(qn("w:vAlign"))
        if v_align is None:
            v_align = OxmlElement("w:vAlign")
            tc_pr.append(v_align)
        v_align.set(qn("w:val"), "top")
        _set_cell_margins(cell, top=0, start=0, bottom=0, end=0)


def _set_table_full_width(table, doc) -> None:
    section = doc.sections[0]
    usable_twips = Emu(section.page_width - section.left_margin - section.right_margin).twips
    half = usable_twips // 2
    _set_table_column_layout(table, doc, [half, half])


def _table_no_borders(table) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)


def _set_cell_margins(cell, *, top: int = 0, start: int = 0, bottom: int = 0, end: int = 0) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    old = tcPr.find(qn("w:tcMar"))
    if old is not None:
        tcPr.remove(old)
    tc_mar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        tc_mar.append(el)
    tcPr.append(tc_mar)


def _add_letterhead(
    doc,
    *,
    cabinet_name: str | None,
    cabinet_name_ar: str | None = None,
    cabinet_logo_bytes: bytes | None,
) -> None:
    """
    En-tête cabinet : nom AR (gauche) | logo (centre) | nom FR (droite).
    Pas d’armoiries du Royaume.
    """
    section = doc.sections[0]
    usable_twips = Emu(section.page_width - section.left_margin - section.right_margin).twips
    side = max(int(usable_twips * 0.36), 1800)
    mid_w = max(usable_twips - 2 * side, 1400)

    name_fr = (cabinet_name or "").strip() or None
    name_ar = (cabinet_name_ar or "").strip() or None

    def _mostly_arabic(s: str) -> bool:
        ar = sum(1 for c in s if "\u0600" <= c <= "\u06FF")
        lat = sum(1 for c in s if ("A" <= c <= "Z") or ("a" <= c <= "z"))
        return ar > lat

    if name_fr and _mostly_arabic(name_fr):
        if not name_ar:
            name_ar = name_fr
        name_fr = None
    if name_fr and not name_ar:
        name_ar = name_fr
    # Ne pas doubler l’arabe dans la colonne FR

    table = doc.add_table(rows=1, cols=3)
    _table_no_borders(table)
    _set_table_visual_ltr(table)
    _set_table_column_layout(table, doc, [side, mid_w, side])
    table.autofit = False
    left = table.rows[0].cells[0]
    mid = table.rows[0].cells[1]
    right = table.rows[0].cells[2]

    # Gauche — nom français
    lp = left.paragraphs[0]
    _set_paragraph_ltr(lp, align="left")
    lp.paragraph_format.space_before = Pt(0)
    lp.paragraph_format.space_after = Pt(0)
    if name_fr:
        lr = lp.add_run(name_fr)
        lr.font.size = Pt(11)
        lr.bold = True
        lr.font.color.rgb = RGBColor(0x0B, 0x1A, 0x4D)
        _set_run_ltr(lr)

    # Centre — logo cabinet (ou armoiries de secours)
    mp = mid.paragraphs[0]
    _set_paragraph_ltr(mp, align="center")
    mp.paragraph_format.space_before = Pt(0)
    mp.paragraph_format.space_after = Pt(0)
    logo_data = cabinet_logo_bytes
    if not logo_data:
        for cand in _ARMS_CANDIDATES:
            if cand.is_file():
                try:
                    logo_data = cand.read_bytes()
                    break
                except Exception:
                    pass
    if logo_data:
        try:
            mr = mp.add_run()
            mr.add_picture(io.BytesIO(logo_data), width=Cm(1.6))
        except Exception:
            pass

    # Droite — nom arabe
    rp = right.paragraphs[0]
    _set_paragraph_rtl(rp, align="right")
    rp.paragraph_format.space_before = Pt(0)
    rp.paragraph_format.space_after = Pt(0)
    if name_ar:
        rr = rp.add_run(name_ar)
        rr.font.size = Pt(11)
        rr.bold = True
        rr.font.color.rgb = RGBColor(0x1A, 0x3A, 0x2A)
        _set_run_rtl(rr)

    sep = doc.add_paragraph()
    _set_paragraph_ltr(sep, align="left")
    sep.paragraph_format.space_before = Pt(4)
    sep.paragraph_format.space_after = Pt(3)
    _paragraph_border_bottom(sep)


def _add_meta_line(doc, text: str) -> None:
    """Ligne méta sous l'en-tête — alignée à droite, graisse medium (regular 11 pt)."""
    p = doc.add_paragraph()
    _set_paragraph_rtl(p, align="right")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for chunk, _, is_ltr in split_typography_runs(text):
        run = p.add_run(chunk)
        run.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = _META_COLOR
        if is_ltr:
            _set_run_ltr(run)
        else:
            _set_run_rtl(run)


def _ensure_export_preamble(
    body: str,
    *,
    case_reference: str | None = None,
    client_name: str | None = None,
) -> str:
    """Injecte parties + référence dossier si absents du corps dicté."""
    t = (body or "").strip()
    if not case_reference and not client_name:
        return t
    if "تحديد الأطراف" in t:
        if case_reference and case_reference not in t:
            return f"مرجع الملف : {case_reference.strip()}\n\n{t}"
        return t
    lines: list[str] = ["تحديد الأطراف", ""]
    if client_name and client_name.strip():
        lines.append(f"المدعي : {client_name.strip()}")
    if case_reference and case_reference.strip():
        lines.append(f"مرجع الملف : {case_reference.strip()}")
    lines.append("")
    return "\n".join(lines) + t


def _add_header_meta(
    doc,
    *,
    lawyer_name: str | None,
    city: str | None = None,
    doc_date: date | None = None,
    case_reference: str | None = None,
) -> None:
    d = (doc_date or date.today()).strftime("%d/%m/%Y")
    if lawyer_name:
        _add_meta_line(doc, f"المحامي : {lawyer_name.strip()}")
    if case_reference:
        _add_meta_line(doc, f"مرجع الملف : {case_reference.strip()}")
    if city:
        city_ar = city.strip()
        if city_ar.lower() in ("casablanca", "casa"):
            city_ar = "الدار البيضاء"
        _add_meta_line(doc, f"{city_ar}، في {d}")
    else:
        _add_meta_line(doc, f"تاريخ التحرير : {d}")
    doc.paragraphs[-1].paragraph_format.space_after = Pt(5)


def _add_document_title(doc, title: str) -> None:
    title_p = doc.add_paragraph()
    _set_paragraph_rtl(title_p, align="center")
    title_p.paragraph_format.space_before = Pt(2)
    title_p.paragraph_format.space_after = Pt(10)
    tr = title_p.add_run((title or "مرافعة").strip())
    tr.bold = True
    tr.font.size = Pt(14)
    tr.underline = True
    tr.font.color.rgb = RGBColor(0x1A, 0x3A, 0x2A)
    _set_run_rtl(tr)


def _add_mixed_rtl_paragraph(doc, text: str, *, bold: bool = False, size: int = 12) -> None:
    p = doc.add_paragraph()
    _set_paragraph_rtl(p, align="right")
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    for chunk, emph, is_ltr in split_typography_runs(text):
        run = p.add_run(chunk)
        run.bold = bold or emph
        run.font.size = Pt(size)
        if is_ltr:
            _set_run_ltr(run)
        else:
            _set_run_rtl(run)
            if not bold and not emph:
                run.font.color.rgb = _META_COLOR


def _is_parties_line(text: str) -> bool:
    return bool(re.match(r"^(?:المدعي|المدعى\s*عليها|المتهم|الضحايا)", (text or "").strip()))


def _add_body_paragraph(
    doc,
    text: str,
    *,
    heading: bool = False,
    closing: bool = False,
    parties: bool = False,
) -> None:
    p = doc.add_paragraph()
    _set_paragraph_rtl(p, align="right")
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if heading:
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.first_line_indent = Cm(0)
        _paragraph_border_top(p)
    elif closing:
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.first_line_indent = Cm(0)
    elif parties:
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.first_line_indent = Cm(0)
    else:
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.first_line_indent = Cm(0)

    text = normalize_arabic_commas(text)
    for chunk, emph, is_ltr in split_typography_runs(text):
        run = p.add_run(chunk)
        if heading:
            run.font.size = Pt(13)
            run.bold = True
            run.font.color.rgb = _SECTION_COLOR
            run.font.underline = True
        elif closing:
            run.font.size = Pt(12)
            run.bold = emph
        else:
            run.font.size = Pt(12)
            run.bold = emph  # corps regular ; gras seulement dates/montants/مواد
        if is_ltr:
            _set_run_ltr(run)
        else:
            _set_run_rtl(run)


def build_plaidoirie_docx(
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

    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = "Traditional Arabic"
    style.font.size = Pt(12)
    style._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), "Traditional Arabic")
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    normal_ppr = style._element.get_or_add_pPr()
    if normal_ppr.find(qn("w:bidi")) is None:
        normal_ppr.append(OxmlElement("w:bidi"))
    jc = normal_ppr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        normal_ppr.append(jc)
    jc.set(qn("w:val"), "left")

    _add_letterhead(
        doc,
        cabinet_name=cabinet_name,
        cabinet_name_ar=cabinet_name_ar,
        cabinet_logo_bytes=cabinet_logo_bytes,
    )
    _add_header_meta(
        doc,
        lawyer_name=lawyer_name,
        city=city,
        case_reference=case_reference,
    )
    _add_document_title(doc, title)

    blocks = prepare_plaidoirie_blocks(body)
    body_paragraphs = []
    for text in blocks:
        is_heading = is_section_heading(text)
        is_parties = _is_parties_line(text)
        is_closing = bool(re.match(r"^(?:واحسبكم|وذلك\s*مع\s*الاحتفاظ|تحت\s*جميع)", text.strip()))
        _add_body_paragraph(
            doc,
            text,
            heading=is_heading,
            closing=is_closing,
            parties=is_parties and not is_heading,
        )
        body_paragraphs.append(doc.paragraphs[-1])

    if body_paragraphs:
        for p in body_paragraphs[-2:]:
            _keep_with_next(p)

    sign = doc.add_paragraph()
    _set_paragraph_rtl(sign, align="right")
    sign.paragraph_format.space_before = Pt(12)
    sign.paragraph_format.space_after = Pt(0)
    _keep_with_next(sign)
    lines: list[str] = []
    if city:
        city_ar = city.strip()
        if city_ar.lower() in ("casablanca", "casa"):
            city_ar = "الدار البيضاء"
        lines.append(f"حرر بـ {city_ar}")
    if include_esignature and lawyer_name:
        lines.append("التوقيع الإلكتروني")
        lines.append(lawyer_name)
        lines.append(date.today().strftime("%d/%m/%Y"))
    else:
        lines.append("التوقيع")
        if lawyer_name:
            lines.append(lawyer_name)
        lines.append("خاتم المحامي")
    sr = sign.add_run("\n".join(lines))
    sr.font.size = Pt(12)
    _set_run_rtl(sr)

    buf = io.BytesIO()
    doc.save(buf)
    filename = f"{_safe_filename(title)}.docx"
    return buf.getvalue(), filename
