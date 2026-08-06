"""Resolve clickable URLs for legal citations."""

import re

SGG_BULLETIN = "https://www.sgg.gov.ma/BulletinOfficiel.aspx"
ADALA_PORTAL = "https://adala.justice.gov.ma/"
_URL_IN_TEXT = re.compile(r"https?://[^\s\])—,]+")


def extract_url_from_label(label: str) -> str | None:
    match = _URL_IN_TEXT.search(label or "")
    if match:
        return match.group(0).rstrip(".,)")
    return None


def resolve_citation_url(label: str, excerpt: str = "") -> str | None:
    """Best-effort official link for a citation."""
    direct = extract_url_from_label(label)
    if direct:
        return direct

    blob = f"{label} {excerpt}".lower()
    if any(k in blob for k in ("sgg.gov", "bulletin officiel", "الجريدة الرسمية")):
        return SGG_BULLETIN
    if re.search(r"\bloi\s+\d{1,3}-\d{1,3}\b", blob, re.I):
        return SGG_BULLETIN
    if re.search(r"\b(cpc|doc|code de procédure)\b", blob, re.I):
        return ADALA_PORTAL
    if any(k in blob for k in ("cour de cassation", "arrêt", "المحكمة")):
        return ADALA_PORTAL
    return None


def enrich_citation(label: str, excerpt: str) -> dict:
    url = resolve_citation_url(label, excerpt)
    return {"label": label, "excerpt": excerpt, "url": url}
