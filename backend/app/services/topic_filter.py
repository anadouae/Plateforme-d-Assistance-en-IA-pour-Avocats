"""Filtrage thématique des sources (évite réformes / web hors sujet)."""

from __future__ import annotations

import re
import unicodedata

from app.schemas import Citation

_GENERIC_TOKENS = {
    "loi", "lois", "droit", "législation", "legislation", "réforme", "reforme",
    "réformes", "reformes", "nouveau", "nouvelle", "nouveaux", "nouvelles",
    "dernier", "derniere", "dernière", "derniers", "dernieres", "dernières",
    "mise", "mises", "jour", "update", "maroc", "morocco", "marocain", "marocaine",
    "maghrib", "maghribi", "مغرب", "مغربي", "مغربية", "مملكة", "المملكة",
    "قانون", "قوانين", "تشريع",
    "تشريعي", "آخر", "اخر", "أحدث", "احدث", "جديد", "جديدة", "تجديد", "تجديدات",
    "أريد", "اريد", "عرف", "اعرف", "أريد", "ما", "في", "من", "عن", "ال", "على",
    "الى", "إلى", "هذا", "هذه", "ذلك", "هل", "انا", "أنا", "ان", "أن", "إن",
    "او", "أو", "ثم", "قد", "كان", "كل", "les", "des", "une", "un", "the", "and",
    "pour", "avec", "sur", "dans", "que", "qui", "site", "bulletin", "officiel",
    "جريدة", "رسمية", "want", "know", "latest", "quoi", "cest", "comment",
    # Mots de conversation (ne doivent pas devenir le « sujet »)
    "veux", "vouloir", "voudrais", "savoir", "connais", "connaitre", "connaître",
    "explique", "expliquer", "dis", "donne", "donner", "parle", "parler",
    "peux", "pouvez", "please", "merci", "hello", "bonjour",
}

_NOISE_URL_HINTS = (
    "gmail", "mail.google", "baidu.com", "bing.com", "youtube.com", "youtu.be",
    "facebook.com", "tiktok", "instagram", "twitter.com", "x.com", "reddit.com",
    "pinterest", "excel", "microsoft.com/excel", "office.com", "sagrada",
    "liquid staking", "eigenlayer", "restaking", "crypto", "binance", "coinbase",
    "wikipedia.org/wiki/temple", "entradas", "tickets",
)

# Bruit « automobile » quand le sujet est animalier (faux positifs DDG sur « auto »)
_ANIMAL_TOPIC = {
    "animal", "animaux", "animale", "animales", "nanimaux", "errant", "errants",
    "chien", "chiens", "chat", "chats", "حيواني", "حيوانات", "حيوان", "ضالة", "ضال",
}
_AUTO_NOISE = (
    "assurance auto", "assurance voiture", "devis auto", "cote auto", "cote moto",
    "lelynx", "lesfurets", "autotrader", "argus", "maif", "groupama",
    "comparateur auto", "formule auto",
)
_ANIMAL_BILL_RE = re.compile(
    r"(?i)\b(?:19[\s.\-]?25|loi\s*n?[°ºo]?\s*19|projet\s+de\s+loi\s*n?[°ºo]?\s*19|"
    r"قانون\s*(?:رقم)?\s*19)\b"
)


def _strip_diacritics(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in norm if not unicodedata.combining(c))


_IMMOBILIER_TOPIC = {
    "immobilier", "immobiliere", "immobilière", "foncier", "fonciere", "foncière",
    "bail", "baux", "location", "loyer", "propriete", "propriété", "copropriete",
    "copropriété", "cadastre", "ancfcc", "عقار", "عقاري", "كراء", "إيجار",
    "dimmobile",
}

_TOPIC_EXPAND = {
    "animaux": {"animal", "animale", "animales", "errant", "errants", "chien", "chiens", "19.25"},
    "animal": {"animaux", "animale", "errant", "errants", "chien", "chiens", "19.25"},
    "nanimaux": {"animaux", "animal", "errant", "errants", "19.25"},
    "errant": {"animaux", "animal", "errants", "19.25"},
    "errants": {"animaux", "animal", "errant", "19.25"},
    "حيوانات": {"حيوان", "ضالة", "كلاب", "19.25"},
    "ضالة": {"حيوانات", "حيوان", "19.25"},
    "immobilier": {"immobiliere", "foncier", "bail", "baux", "location", "propriete", "عقار", "كراء"},
    "immobiliere": {"immobilier", "foncier", "bail", "baux"},
    "foncier": {"immobilier", "fonciere", "propriete", "cadastre"},
    "bail": {"baux", "location", "loyer", "immobilier", "كراء"},
    "baux": {"bail", "location", "immobilier"},
    "عقار": {"عقاري", "كراء", "immobilier"},
    "عقاري": {"عقار", "كراء", "immobilier"},
    "كراء": {"إيجار", "bail", "baux", "immobilier"},
}


def is_animal_law_query(question: str) -> bool:
    q = _strip_diacritics((question or "").lower())
    if _ANIMAL_BILL_RE.search(q):
        return True
    tokens = tokenize_question(question)
    return bool(tokens & _ANIMAL_TOPIC)


def is_immobilier_query(question: str) -> bool:
    q = _strip_diacritics((question or "").lower())
    q = q.replace("dimmobile", "immobilier").replace("immobile r", "immobilier")
    if any(
        w in q
        for w in (
            "immobilier",
            "immobili",
            "foncier",
            "bail",
            "baux",
            "location",
            "loyer",
            "copropri",
            "ancfcc",
            "عقار",
            "كراء",
            "إيجار",
        )
    ):
        return True
    tokens = tokenize_question(question)
    return bool(tokens & _IMMOBILIER_TOPIC)


def tokenize_question(question: str) -> set[str]:
    q = _strip_diacritics((question or "").lower())
    # Typos fréquents
    q = q.replace("nanimaux", "animaux").replace("nanimal", "animal")
    q = q.replace("dimmobile", "immobilier").replace("immobile r", "immobilier")
    # Latin (≥3) + Arabic (≥3) — évite « ان » qui matche partout
    parts = re.findall(r"[a-z0-9]{3,}|[\u0600-\u06ff]{3,}", q)
    tokens: set[str] = set()
    for p in parts:
        # Enlever l'article arabe « ال »
        if p.startswith("ال") and len(p) > 4:
            p = p[2:]
        if p in _GENERIC_TOKENS or len(p) < 3:
            continue
        tokens.add(p)
        # Variante singulier/pluriel arabe légère
        if p.endswith("ات") and len(p) > 4:
            tokens.add(p[:-2])
        if p.endswith("ين") and len(p) > 4:
            tokens.add(p[:-2])
    if _ANIMAL_BILL_RE.search(q) or "19.25" in q or "19-25" in q.replace(" ", ""):
        tokens.update({"animaux", "animal", "errant", "errants", "19.25", "حيوانات", "ضالة"})
    # Synonymes (animaux ↔ errants) pour matcher la presse
    expanded = set(tokens)
    for t in list(tokens):
        expanded.update(_TOPIC_EXPAND.get(t, ()))
    return expanded


_PANORAMA_LAWS_RE = re.compile(
    r"(?i)("
    r"tous\s+les\s+lois|toutes\s+les\s+lois|liste\s+(?:compl[eè]te\s+des\s+)?lois|"
    r"ensemble\s+des\s+lois|panorama\s+(?:des\s+)?lois|recensement\s+(?:des\s+)?lois|"
    r"lois?\s+(?:adopt[ée]es?|publi[ée]es?|vot[ée]es?|promulgu[ée]es?).{0,40}20\d{2}|"
    r"20\d{2}.{0,40}lois?\s+(?:adopt|publi|vot|promulgu)|"
    r"جميع\s+القوانين|كل\s+القوانين|لائحة\s+(?:تتضمن\s+)?(?:جميع\s+)?القوانين|"
    r"القوانين\s+التي\s+تم\s+المصادق|المصادق\s+عليها\s+خلال|"
    r"دون\s+ان\s+تنسى|دون\s+أن\s+تنسى|"
    r"كل\s+التغييرات\s+التي\s+وقعت|"
    r"recherch(?:e|er).{0,40}(?:toutes?\s+les\s+lois|جميع\s+القوانين)"
    r")"
)


def is_panorama_laws_query(question: str) -> bool:
    """True si l'utilisateur veut une LISTE / panorama des lois (pas un seul thème)."""
    q = (question or "").strip()
    if not q:
        return False
    # Ne pas traiter « dernières mises à jour sur la loi animaux » comme panorama
    if is_animal_law_query(q) and not re.search(
        r"(?i)جميع\s+القوانين|كل\s+القوانين|toutes\s+les\s+lois|tous\s+les\s+lois|"
        r"liste\s+(?:des\s+)?lois|دون\s+أ?ن\s+تنسى",
        q,
    ):
        return False
    if _PANORAMA_LAWS_RE.search(q):
        return True
    q_low = _strip_diacritics(q.lower())
    has_year = bool(re.search(r"20[12]\d", q_low))
    asks_list = any(
        w in q_low
        for w in (
            "liste",
            "toutes les lois",
            "tous les lois",
            "جميع القوانين",
            "كل القوانين",
            "لائحة",
            "panorama",
        )
    )
    if has_year and asks_list:
        return True
    return False


def is_generic_recent_laws_query(question: str) -> bool:
    """True si « dernières lois Maroc » sans thème précis (animaux, travail…)."""
    if is_panorama_laws_query(question):
        return True
    return len(tokenize_question(question)) == 0


def text_matches_topic(text: str, topic_tokens: set[str], min_hits: int = 1) -> bool:
    if not topic_tokens:
        return True
    blob = _strip_diacritics((text or "").lower())
    # Tokens trop courts (<4) : match mot entier approximatif pour limiter les faux positifs
    hits = 0
    for t in topic_tokens:
        if len(t) >= 4 and t in blob:
            hits += 1
        elif len(t) == 3 and re.search(rf"(?<![a-z0-9\u0600-\u06ff]){re.escape(t)}(?![a-z0-9\u0600-\u06ff])", blob):
            hits += 1
    return hits >= min_hits


def filter_hits_by_topic(hits: list[dict], question: str) -> list[dict]:
    """Garde les hits corpus/RAG alignés sur le sujet (évite DOC pour « animaux »)."""
    tokens = tokenize_question(question)
    if not hits:
        return []
    if not tokens:
        return hits
    # Sujet animalier → exclure DOC / civil générique hors sujet
    animalish = bool(tokens & _ANIMAL_TOPIC) or any(
        t in tokens for t in ("errant", "errants", "chien", "chiens")
    )
    matched = []
    for h in hits:
        src = str(h.get("source", "")).lower()
        blob = f"{h.get('source', '')} {h.get('text', '')}"
        if animalish and (
            "dahir des obligations" in src
            or "obligations et contrats" in src
            or src.startswith("doc-")
            or "doc-1963" in blob.lower()
        ):
            continue
        if text_matches_topic(blob, tokens):
            matched.append(h)
    return matched


def is_thin_legal_context(citations: list[Citation], question: str) -> bool:
    """True si on n'a que le portail officiel / rien d'utile sur le thème."""
    if not citations:
        return True
    tokens = tokenize_question(question)
    topical = 0
    for c in citations:
        blob = f"{c.label or ''} {c.excerpt or ''} {c.url or ''}"
        url = (c.url or "").lower()
        is_portal = "sgg.gov.ma" in url or "legifrance" in url
        if tokens and text_matches_topic(blob, tokens) and not is_portal:
            topical += 1
        elif not tokens and not is_portal and len((c.excerpt or "").strip()) > 80:
            topical += 1
    return topical == 0


def filter_reforms_by_topic(reforms: list[dict], question: str) -> list[dict]:
    tokens = tokenize_question(question)
    if not tokens:
        return reforms
    matched = []
    for r in reforms:
        blob = " ".join(
            str(r.get(k, ""))
            for k in ("title_fr", "title_ar", "summary_fr", "summary_ar", "domain", "instrument")
        )
        if text_matches_topic(blob, tokens):
            matched.append(r)
    return matched


def is_noise_citation(citation: Citation, question: str | None = None) -> bool:
    blob = f"{citation.label or ''} {citation.excerpt or ''} {citation.url or ''}".lower()
    if any(h in blob for h in _NOISE_URL_HINTS):
        return True
    tokens = tokenize_question(question or "")
    if tokens & _ANIMAL_TOPIC and any(p in blob for p in _AUTO_NOISE):
        return True
    return False


def filter_citations_by_topic(
    citations: list[Citation],
    question: str,
    *,
    keep_official_portal: bool = True,
    soft: bool = True,
) -> list[Citation]:
    """Classe les citations par pertinence — mode soft = enrichissement, pas kill-switch."""
    if not citations:
        return []
    cleaned = [c for c in citations if not is_noise_citation(c, question)]
    tokens = tokenize_question(question)
    if not tokens:
        return cleaned

    animalish = is_animal_law_query(question) or bool(tokens & _ANIMAL_TOPIC)
    kept: list[Citation] = []
    portals: list[Citation] = []
    other: list[Citation] = []
    for c in cleaned:
        blob = f"{c.label or ''} {c.excerpt or ''} {c.url or ''}"
        blob_l = _strip_diacritics(blob.lower())
        url = (c.url or "").lower()
        is_portal = "sgg.gov.ma" in url or "legifrance" in url or "adala" in url
        # Bruit évident seulement (sujet animalier)
        if animalish and (
            "sucrerie" in blob_l
            or "assurance auto" in blob_l
            or "lelynx" in blob_l
            or "dahir des obligations" in blob_l
            or "obligations et contrats" in blob_l
        ):
            continue
        animal_hit = any(
            k in blob_l
            for k in (
                "animal", "animaux", "errant", "chien", "chat", "19.25", "19-25",
                "ضالة", "حيوانات", "حيوان", "spa",
            )
        )
        if animalish:
            if animal_hit or (is_portal and "animal" in blob_l):
                kept.append(c)
            elif keep_official_portal and is_portal:
                portals.append(c)
            elif soft:
                other.append(c)
            continue
        if text_matches_topic(blob, tokens):
            kept.append(c)
        elif keep_official_portal and is_portal:
            portals.append(c)
        elif soft:
            other.append(c)

    if kept:
        extra = portals[:2] + (other[:4] if soft and len(kept) < 5 else [])
        return kept + extra
    # Soft : garder un panel utile plutôt qu'un seul portail
    if soft and (other or portals):
        return (portals[:2] + other)[:10]
    return portals[:2]
