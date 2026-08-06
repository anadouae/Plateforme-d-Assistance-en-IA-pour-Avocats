import logging
import re
from io import BytesIO
from pathlib import Path

import fitz
from docx import Document as DocxDocument
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/tiff",
}

OCR_LANG = "fra+ara"
MAX_PDF_OCR_PAGES = 20

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
# Mots / particules souvent en DÉBUT de phrase arabe (ordre logique)
_AR_STARTERS = {
    "في", "من", "على", "إلى", "الى", "إن", "أن", "هذا", "هذه", "ذلك", "تلك",
    "وقد", "فقد", "تحت", "بعد", "قبل", "مع", "عن", "بين", "كل", "أي", "لا",
    "ما", "هل", "تم", "يتم", "يمكن", "حيث", "إذ", "اذا", "إذا", "لكن", "غير",
    "مقدمة", "المبحث", "المطلب", "الفقرة", "خاتمة", "أولا", "ثانيا", "ثالثا",
    "ملخص", "بحث", "الفصل", "الباب", "المادة", "القانون", "قانون",
}
# Mots souvent en FIN visuelle quand la ligne est inversée (donc début logique)
_AR_TRAILERS_WHEN_REVERSED = {
    "في", "من", "على", "إلى", "الى", "و", "أو", "ثم",
}


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def arabic_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha() or "\u0600" <= c <= "\u06FF"]
    if not letters:
        return 0.0
    ar = sum(1 for c in letters if _ARABIC_RE.match(c))
    return ar / len(letters)


def _strip_word(w: str) -> str:
    return re.sub(r"^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$", "", w or "")


_AR_VERBS_START = {
    "يقوم", "يتم", "يمكن", "يعتمد", "يهدف", "يشهد", "ساهم", "يساهم", "يتعلق",
    "تنص", "ينص", "تبرز", "يبرز", "توجد", "يوجد", "تشهد", "واكب", "اعتمد",
}


def _line_reading_score(words: list[str]) -> int:
    """Score heuristique : ordre logique arabe vs ordre visuel inversé."""
    if not words:
        return 0
    clean = [_strip_word(w) for w in words]
    clean = [w for w in clean if w]
    if not clean:
        return 0
    n = len(clean)
    score = 0
    first = clean[0]
    last = clean[-1]
    if first in _AR_STARTERS or first in _AR_VERBS_START:
        score += 4
    if last in _AR_STARTERS and first not in _AR_STARTERS:
        score -= 3
    if last in _AR_TRAILERS_WHEN_REVERSED and n >= 3:
        score -= 2
    # Prépositions / verbes mieux en début de ligne qu'en fin
    for i, w in enumerate(clean):
        pos = i / max(n - 1, 1)  # 0 = début, 1 = fin
        if w in ("في", "من", "على", "إلى", "الى", "مع", "عن", "بين"):
            score += 2 if pos < 0.35 else (-2 if pos > 0.65 else 0)
        if w in _AR_VERBS_START:
            score += 3 if pos < 0.35 else (-3 if pos > 0.65 else 0)
    for a, b in zip(clean, clean[1:]):
        if a in ("في", "من", "على", "إلى", "الى", "مع", "عن", "بين") and len(b) > 2:
            score += 1
        if b in ("في", "من", "على") and len(a) > 3:
            score -= 1
    return score


def repair_arabic_line(line: str) -> str:
    """Corrige l'ordre des mots arabes souvent inversé par PyMuPDF / OCR LTR."""
    raw = (line or "").strip()
    if not raw or arabic_char_ratio(raw) < 0.35:
        return line
    words = raw.split()
    if len(words) < 3:
        return line
    fwd = _line_reading_score(words)
    rev_words = list(reversed(words))
    rev = _line_reading_score(rev_words)
    if rev > fwd:
        return " ".join(rev_words)
    return line


def repair_arabic_extracted_text(text: str) -> str:
    """Répare le texte extrait (lignes arabes mot-inversées). Sûr pour FR/EN."""
    if not text or arabic_char_ratio(text) < 0.12:
        return text
    parts: list[str] = []
    for line in text.splitlines():
        if line.strip():
            parts.append(repair_arabic_line(line))
        else:
            parts.append(line)
    return "\n".join(parts)


def safe_repair_arabic_text(text: str) -> str:
    """Applique la réparation seulement si le score de lecture s'améliore."""
    if not text:
        return text
    fixed = repair_arabic_extracted_text(text)
    if fixed == text:
        return text
    if _arabic_quality_score(fixed) >= _arabic_quality_score(text):
        return fixed
    return text


def is_scrambled_arabic(text: str) -> bool:
    """Détecte une couche PDF arabe illisible (BIDI cassé / mots coupés)."""
    if not text or arabic_char_ratio(text) < 0.2:
        return False
    # Fragments typiques des PDF arabes mal encodés
    if re.search(
        r"(العقا\b|،?\s*رية\b|المعامالت|المعامﻼت|صصُخ|زّويمي|قّالموث|الّوفع)",
        text,
    ):
        return True
    lines = [ln.strip() for ln in text.splitlines() if len(ln.split()) >= 4]
    if not lines:
        return _arabic_quality_score(text) < 12
    bad = 0
    for ln in lines:
        if ln[:1] in "،.؛!?ًٌٍَُِّْ":
            bad += 1
        elif ln.split()[0] in ("سواء", "جانب", "و", "أو") and "مقدمة" not in ln[:20]:
            # Souvent la fin de phrase placée en tête
            if arabic_char_ratio(ln) > 0.5:
                bad += 0.5
    if bad / max(len(lines), 1) >= 0.25:
        return True
    return _arabic_quality_score(text) < 12


def _arabic_quality_score(text: str) -> int:
    """Plus le score est haut, plus l'ordre de lecture semble correct."""
    if not text:
        return 0
    score = 0
    for line in text.splitlines():
        words = line.split()
        if len(words) >= 3 and arabic_char_ratio(line) > 0.35:
            score += _line_reading_score(words)
    # Bonus si des titres arabes classiques apparaissent au début d'une ligne
    for marker in ("مقدمة", "المبحث", "ملخص", "خاتمة", "المطلب"):
        if re.search(rf"(?m)^{marker}", text):
            score += 5
        if re.search(rf"(?m){marker}$", text):
            score -= 3
    return score


def _page_text_reading_order(page) -> str:
    """Extraction dict + tri RTL pour lignes arabes (évite get_text() LTR)."""
    try:
        data = page.get_text("dict")
    except Exception:
        return page.get_text() or ""

    lines_out: list[str] = []
    blocks = sorted(
        data.get("blocks", []),
        key=lambda b: (round(b.get("bbox", [0, 0, 0, 0])[1], 1), b.get("bbox", [0, 0, 0, 0])[0]),
    )
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans") or []
            if not spans:
                continue
            span_bits = []
            for s in spans:
                t = s.get("text") or ""
                bbox = s.get("bbox") or [0, 0, 0, 0]
                span_bits.append((float(bbox[0]), t))
            probe = "".join(t for _, t in span_bits)
            if arabic_char_ratio(probe) > 0.3:
                span_bits.sort(key=lambda x: x[0], reverse=True)
            else:
                span_bits.sort(key=lambda x: x[0])
            line_text = "".join(t for _, t in span_bits)
            # Normaliser espaces
            line_text = re.sub(r"[ \t]+", " ", line_text).strip()
            if line_text:
                lines_out.append(repair_arabic_line(line_text))
    return "\n".join(lines_out)


def _ocr_image(image: Image.Image) -> tuple[str, int]:
    import pytesseract

    # Essai arabe-prioritaire puis bilingue
    configs = [
        ("ara+fra", "--psm 6"),
        ("fra+ara", "--psm 6"),
        (OCR_LANG, "--psm 4"),
    ]
    best_text = ""
    best_score = -10**9
    for lang, cfg in configs:
        try:
            text = pytesseract.image_to_string(image, lang=lang, config=cfg)
            cleaned = repair_arabic_extracted_text(text.strip())
            q = _arabic_quality_score(cleaned) + len(cleaned) // 40
            if q > best_score and cleaned:
                best_score = q
                best_text = cleaned
        except Exception as exc:
            logger.debug("OCR lang=%s failed: %s", lang, exc)
    if not best_text:
        try:
            best_text = pytesseract.image_to_string(image, lang=OCR_LANG).strip()
            best_text = repair_arabic_extracted_text(best_text)
        except Exception as exc:
            logger.warning("OCR failed: %s", exc)
            return "", 35
    score = min(95, max(35, int(len(best_text) / 8))) if best_text else 35
    return best_text, score


def _ocr_pdf_pymupdf(content: bytes, *, arabic: bool = True) -> tuple[str, int | None]:
    """OCR intégré PyMuPDF (souvent meilleur que la couche texte BIDI cassée)."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        parts: list[str] = []
        lang = "ara" if arabic else "fra+ara"
        n_pages = min(len(doc), MAX_PDF_OCR_PAGES)
        for i in range(n_pages):
            page = doc[i]
            try:
                tp = page.get_textpage_ocr(language=lang, dpi=280, full=True)
                t = page.get_text(textpage=tp) or ""
            except Exception:
                t = page.get_text() or ""
            if t.strip():
                parts.append(t.strip())
        doc.close()
        if not parts:
            return "", 0
        combined = safe_repair_arabic_text("\n\n".join(parts))
        score = min(92, max(50, 40 + len(combined) // 40))
        return combined, score
    except Exception as exc:
        logger.warning("PyMuPDF OCR failed: %s", exc)
        return "", 0


def _ocr_pdf_scanned(content: bytes) -> tuple[str, int | None]:
    try:
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(content, dpi=280, first_page=1, last_page=MAX_PDF_OCR_PAGES)
        parts: list[str] = []
        scores: list[int] = []
        for img in images:
            page_text, page_score = _ocr_image(img)
            if page_text:
                parts.append(page_text)
                scores.append(page_score)
        if not parts:
            return "", 0
        combined = safe_repair_arabic_text("\n\n".join(parts))
        avg_score = sum(scores) // len(scores)
        return combined, avg_score
    except Exception as exc:
        logger.warning("PDF OCR failed: %s", exc)
        return "", 0


def _pick_best_text(*candidates: str) -> str:
    scored = []
    for t in candidates:
        if not t or not t.strip():
            continue
        # Pénaliser fort le texte brouillé
        pen = 40 if is_scrambled_arabic(t) else 0
        scored.append((_arabic_quality_score(t) + min(len(t), 5000) // 100 - pen, t))
    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def extract_from_pdf(content: bytes) -> tuple[str, int | None]:
    doc = fitz.open(stream=content, filetype="pdf")
    naive_parts: list[str] = []
    ordered_parts: list[str] = []
    for page in doc:
        try:
            naive_parts.append(page.get_text("text", sort=True) or page.get_text() or "")
        except TypeError:
            naive_parts.append(page.get_text() or "")
        ordered_parts.append(_page_text_reading_order(page))
    doc.close()

    naive = "\n".join(naive_parts).strip()
    ordered = "\n".join(ordered_parts).strip()
    naive_fixed = safe_repair_arabic_text(naive)
    ordered_fixed = safe_repair_arabic_text(ordered)
    text = _pick_best_text(ordered_fixed, naive_fixed, ordered, naive)
    ar_heavy = arabic_char_ratio(text) > 0.25 or arabic_char_ratio(naive) > 0.25

    # Couche texte arabe corrompue → OCR obligatoire (ne pas renvoyer OCR 100% faux)
    must_ocr = (not text or len(text) < 50) or (ar_heavy and is_scrambled_arabic(text))

    if must_ocr:
        logger.info("Arabic/scrambled PDF → forcing OCR (pymupdf + tesseract)")
        ocr_a, score_a = _ocr_pdf_pymupdf(content, arabic=ar_heavy)
        ocr_b, score_b = _ocr_pdf_scanned(content)
        best = _pick_best_text(ocr_a, ocr_b, text)
        if best and not is_scrambled_arabic(best):
            sc = score_a if best == ocr_a else (score_b if best == ocr_b else 70)
            return best, sc or 75
        if best and len(best) > len(text):
            return best, max(score_a or 0, score_b or 0, 55)
        if text:
            return text, 55  # couche texte, qualité douteuse
        return best, 40

    if len(text) > 50:
        return text, 100

    ocr_text, ocr_score = _ocr_pdf_scanned(content)
    if len(ocr_text) > 20:
        return ocr_text, ocr_score

    return text, (85 if text else 0)


def extract_from_docx(content: bytes) -> tuple[str, int | None]:
    doc = DocxDocument(BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    return repair_arabic_extracted_text(text), None


def extract_from_image(content: bytes) -> tuple[str, int | None]:
    try:
        image = Image.open(BytesIO(content))
        return _ocr_image(image)
    except Exception:
        return "", 35


def extract_text(content: bytes, filename: str, mime_type: str) -> tuple[str, int | None]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf" or mime_type == "application/pdf":
        return extract_from_pdf(content)
    if ext == "docx" or "wordprocessingml" in mime_type:
        return extract_from_docx(content)
    if ext in ("png", "jpg", "jpeg", "tiff", "tif") or mime_type.startswith("image/"):
        return extract_from_image(content)
    return "", None


def extract_parties(text: str) -> list[str]:
    patterns = [
        r"(?:entre|parties?)\s*:?\s*(.+?)(?:\n|$)",
        r"(?:locataire|bailleur|vendeur|acheteur|employeur|salarié)\s*:?\s*([^\n,;]+)",
    ]
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = match.group(1).strip()
            if 3 < len(val) < 80 and val not in found:
                found.append(val)
    return found[:5]


def extract_dates(text: str) -> list[str]:
    dates = re.findall(
        r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|\b\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\b",
        text,
    )
    return list(dict.fromkeys(dates))[:10]


def extract_amounts(text: str) -> list[str]:
    amounts = re.findall(
        r"\b\d{1,3}(?:[ \u00a0]\d{3})*(?:[.,]\d+)?\s*(?:MAD|DH|Dhs|dirhams?|€|EUR|USD|\$)\b",
        text,
        flags=re.IGNORECASE,
    )
    return list(dict.fromkeys(amounts))[:10]


def extract_risk_clauses(text: str) -> list[str]:
    keywords = (
        r"résiliation|résilier|pénalité|amende|responsabilité|garantie|caution|"
        r"indemnité|clause\s+pénale|force\s+majeure|exclusivité|"
        r"فسخ|غرامة|مسؤولية|ضمان|تعويض"
    )
    found = []
    for m in re.finditer(rf"([^\n.!?…]{{0,80}}(?:{keywords})[^\n.!?…]{{0,80}})", text, re.IGNORECASE):
        snippet = re.sub(r"\s+", " ", m.group(1)).strip()
        if 20 < len(snippet) < 200 and snippet not in found:
            found.append(snippet)
    return found[:8]


def get_document_context_excerpt(text: str, question: str, max_len: int = 8000) -> str:
    """Extrait pertinent autour des mots de la question (sinon début du doc)."""
    if not text:
        return ""
    text = repair_arabic_extracted_text(text)
    if len(text) <= max_len:
        return text
    q_tokens = [t for t in re.findall(r"[\w\u0600-\u06FF]{3,}", (question or "").lower())]
    if not q_tokens:
        return text[:max_len]
    best_i = 0
    best_hits = -1
    step = max(200, max_len // 4)
    for i in range(0, max(1, len(text) - max_len), step):
        chunk = text[i : i + max_len].lower()
        hits = sum(1 for t in q_tokens if t in chunk)
        if hits > best_hits:
            best_hits = hits
            best_i = i
    return text[best_i : best_i + max_len]


def find_relevant_excerpt(text: str, question: str, max_len: int = 1200) -> str:
    return get_document_context_excerpt(text, question, max_len=max_len)
