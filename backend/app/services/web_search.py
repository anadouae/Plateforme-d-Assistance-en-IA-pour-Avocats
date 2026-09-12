"""Web search ouverte (DuckDuckGo / Google News RSS / Tavily) — Maroc, France ou général."""

import hashlib
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import httpx

from app.core.config import settings
from app.schemas import Citation

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, tuple[str, list[Citation], int]]] = {}
_CACHE_TTL = 300  # 5 min
_MAX_CACHE_ENTRIES = 48

_SGG_PORTAL = Citation(
    label="Bulletin officiel du Royaume du Maroc — sgg.gov.ma",
    excerpt=(
        "Portail officiel du Secrétariat général du Gouvernement pour consulter "
        "les lois, décrets et textes publiés au Bulletin officiel."
    ),
    url="https://www.sgg.gov.ma/BulletinOfficiel.aspx",
)
_SGG_URL = "https://www.sgg.gov.ma/BulletinOfficiel.aspx"

_LEGIFRANCE_PORTAL = Citation(
    label="Légifrance — Journal officiel de la République française",
    excerpt=(
        "Portail officiel de la diffusion du droit français : lois, codes, "
        "décrets et Journal officiel."
    ),
    url="https://www.legifrance.gouv.fr/",
)


def _cache_key(question: str, max_results: int, mode: str = "default") -> str:
    raw = f"{question}|{max_results}|{settings.WEB_SEARCH_PROVIDER}|{mode}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str) -> tuple[str, list[Citation], int] | None:
    if key in _CACHE:
        ts, data = _CACHE[key]
        if time.time() - ts < _CACHE_TTL:
            return data
        del _CACHE[key]
    return None


def _set_cache(key: str, data: tuple[str, list[Citation], int]) -> None:
    if len(_CACHE) >= _MAX_CACHE_ENTRIES:
        oldest_key = min(_CACHE.items(), key=lambda item: item[1][0])[0]
        _CACHE.pop(oldest_key, None)
    _CACHE[key] = (time.time(), data)


_NOISE_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "fb.com",
    "tiktok.com",
    "instagram.com",
    "pinterest.",
    "twitter.com",
    "x.com",
    "reddit.com",
    "dailymotion.com",
    "ureed.com",
    "reverso.net",
    "arid.my",
    "dictionary.",
    "translate.google",
    "linguee.",
    "gmail.com",
    "mail.google.com",
    "accounts.google.com",
    "baidu.com",
    "bing.com",
    "microsoft.com",
    "office.com",
    "support.google.com",
    "coinbase.com",
    "binance.com",
    "medium.com",
    "nordark",
    "sagradafamilia",
)


def _result_url(result: dict) -> str:
    return str(result.get("url") or result.get("href") or result.get("link") or "").strip()


def _is_noise_result(result: dict) -> bool:
    url = _result_url(result).lower()
    title = str(result.get("title", "")).lower()
    body = str(result.get("body", result.get("content", ""))).lower()
    blob = f"{url} {title} {body}"
    if any(d in url for d in _NOISE_DOMAINS):
        return True
    if "youtube" in title or "/videos/search" in url:
        return True
    noise_phrases = (
        "liquid staking", "restaking", "eigenlayer", "iniciar sesión",
        "se connecter à gmail", "inloggen bij gmail", "excel if",
        "sagrada familia", "entradas", "随机数", "带圈数字",
        "javascript must be enabled", "enable javascript", "change your browser options",
        "sorry, javascript",
    )
    if any(p in blob for p in noise_phrases):
        return True
    return False


def _is_ma_relevant(result: dict) -> bool:
    blob = " ".join(
        str(result.get(k, "")) for k in ("title", "body", "url", "href", "link")
    ).lower()
    return any(h in blob for h in (".ma", "maroc", "morocco", "sgg.gov", "justice.gov", "adala"))


def _is_fr_relevant(result: dict) -> bool:
    blob = " ".join(
        str(result.get(k, "")) for k in ("title", "body", "url", "href", "link")
    ).lower()
    return any(
        h in blob
        for h in (
            "legifrance",
            ".gouv.fr",
            "france",
            "français",
            "francais",
            "journal officiel",
            "république française",
        )
    )


def _looks_legal(result: dict) -> bool:
    blob = " ".join(
        str(result.get(k, "")) for k in ("title", "body", "content", "url", "href", "link")
    ).lower()
    legal_hints = (
        "loi", "dahir", "décret", "decret", "code", "juridique", "législ",
        "bulletin officiel", "journal officiel", "محكمة", "قانون", "ظهير",
        "مرسوم", "جريدة رسمية", "tribunal", "article",
    )
    return any(h in blob for h in legal_hints)


def _is_relevant_for_jurisdiction(result: dict, jurisdiction: str) -> bool:
    """Recherche ouverte (style Groq/Kimi) : on garde tout sauf le bruit évident."""
    if _is_noise_result(result):
        return False
    return True


def _dedupe_results(results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for r in results:
        if _is_noise_result(r):
            continue
        url = _result_url(r)
        key = url or r.get("title", "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _rank_results(results: list[dict], jurisdiction: str = "ma") -> list[dict]:
    def score(r: dict) -> int:
        url = _result_url(r).lower()
        title = str(r.get("title", "")).lower()
        body = str(r.get("body", r.get("content", ""))).lower()
        s = 0
        if jurisdiction == "fr":
            if "legifrance.gouv.fr" in url:
                s += 80
            elif ".gouv.fr" in url:
                s += 50
            if any(k in title or k in body for k in ("journal officiel", "loi n", "décret", "code")):
                s += 20
            if _is_ma_relevant(r) and not _is_fr_relevant(r):
                s -= 40
        else:
            if "sgg.gov.ma" in url:
                s += 80
            elif "justice.gov.ma" in url or "adala.justice.gov.ma" in url:
                s += 60
            elif ".gov.ma" in url:
                s += 50
            elif ".ma" in url:
                s += 30
            if any(k in url for k in ("justice", "adala", "parlement", "finances", "bulletin")):
                s += 15
            if any(
                k in title or k in body
                for k in ("bulletin officiel", "loi n", "décret", "dahir", "جريدة رسمية", "amende", "animal")
            ):
                s += 20
            if _is_fr_relevant(r) and not _is_ma_relevant(r) and jurisdiction == "ma":
                s -= 20
        if _is_noise_result(r):
            s -= 100
        return s

    return sorted(results, key=score, reverse=True)


def _parse_results(results: list[dict]) -> tuple[str, list[Citation], int]:
    if not results:
        return "", [], 0

    citations = []
    excerpts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Source web")
        body = r.get("body", r.get("content", ""))[:900]
        url = r.get("url", r.get("href", r.get("link", "")))
        label = f"[{i}] {title}"
        if url:
            label += f" — {url}"
        citations.append(Citation(label=label, excerpt=body, url=url or None))
        excerpts.append(f"SOURCE {i} — {title}\nURL: {url}\n{body}")
    confidence = min(78, 48 + len(results) * 5)
    return "\n\n".join(excerpts), citations, confidence


def _search_tavily(question: str, max_results: int) -> tuple[str, list[Citation], int]:
    from tavily import TavilyClient
    from app.services.language import detect_jurisdiction

    clean = (question or "").strip()
    jur = detect_jurisdiction(question)
    suffix = {
        "fr": "droit français législation France",
        "ma": "droit marocain législation Maroc",
        "general": "législation droit",
    }[jur]

    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    response = client.search(
        query=f"{clean} {suffix}",
        max_results=max_results,
        search_depth="basic",
        include_answer=False,
    )
    results = [
        {
            "title": r.get("title", "Source web"),
            "body": r.get("content", ""),
            "url": r.get("url", ""),
        }
        for r in response.get("results", [])
        if not _is_noise_result(
            {"title": r.get("title", ""), "url": r.get("url", ""), "body": r.get("content", "")}
        )
    ]
    return _parse_results(_rank_results(_dedupe_results(results), jur))


def _ddg_text(query: str, max_results: int, region: str = "fr-fr", jurisdiction: str = "ma") -> list[dict]:
    from duckduckgo_search import DDGS

    results: list[dict] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=region, max_results=max_results * 3):
                item = {
                    "title": r.get("title", "Source web"),
                    "body": r.get("body", ""),
                    "url": r.get("href", r.get("link", "")),
                }
                if _is_noise_result(item):
                    continue
                if not _is_relevant_for_jurisdiction(item, jurisdiction):
                    continue
                if jurisdiction == "fr" and _is_ma_relevant(item) and not _is_fr_relevant(item):
                    continue
                results.append(item)
                if len(results) >= max_results:
                    break
    except Exception as exc:
        logger.warning("DDG text failed (%s): %s", query[:50], exc)
    return results


def _ddg_news(query: str, max_results: int = 6) -> list[dict]:
    """Actualités DDG (souvent plus riches que text pour les lois récentes)."""
    from duckduckgo_search import DDGS

    out: list[dict] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, region="wt-wt", max_results=max_results):
                item = {
                    "title": r.get("title", "Actualité"),
                    "body": r.get("body", r.get("excerpt", "")),
                    "url": r.get("url", r.get("href", "")),
                }
                if item["url"] and not _is_noise_result(item):
                    out.append(item)
    except Exception as exc:
        logger.warning("DDG news failed (%s): %s", query[:50], exc)
    return out


def _google_news_rss(query: str, max_results: int = 8, locale: str = "fr") -> list[dict]:
    """Fallback fiable quand DuckDuckGo est vide / rate-limité (ex. loi 19.25)."""
    q = (query or "").strip()
    if not q:
        return []
    # hl/gl adaptés Maroc / France
    if locale == "ar":
        params = "hl=ar&gl=MA&ceid=MA:ar"
    else:
        params = "hl=fr&gl=MA&ceid=MA:fr"
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&{params}"
    try:
        with httpx.Client(timeout=18.0, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; LexHubLegal/2.0)"},
            )
        if resp.status_code >= 400:
            logger.warning("Google News RSS HTTP %s", resp.status_code)
            return []
        root = ET.fromstring(resp.text)
    except Exception as exc:
        logger.warning("Google News RSS failed: %s", exc)
        return []

    out: list[dict] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        raw_desc = item.findtext("description") or ""
        body = re.sub(r"<[^>]+>", " ", raw_desc)
        body = re.sub(r"\s+", " ", body).strip()
        if not title:
            continue
        row = {"title": title, "body": body[:900], "url": link}
        if _is_noise_result(row):
            continue
        out.append(row)
        if len(out) >= max_results:
            break
    return out


def _collect_web_results(
    question: str,
    queries: list[str],
    *,
    max_results: int,
    jurisdiction: str,
    locale: str = "fr",
) -> list[dict]:
    """Google News RSS d'abord (fiable), puis DDG si besoin — style Kimi Search."""
    merged: list[dict] = []
    news_queries = (queries[:4] if queries else []) + ([question] if question.strip() else [])
    seen_q: set[str] = set()
    for q in news_queries:
        qn = (q or "").strip().lower()
        if not qn or qn in seen_q:
            continue
        seen_q.add(qn)
        try:
            merged.extend(_google_news_rss(q, max_results=6, locale=locale))
        except Exception as exc:
            logger.warning("news rss failed (%s): %s", q[:60], exc)
        if len(merged) >= max_results:
            break

    # DDG seulement si RSS insuffisant (souvent rate-limité depuis Docker)
    if len(merged) < max(3, max_results // 2):
        for q in (queries or [question])[:2]:
            try:
                merged.extend(
                    _ddg_text(q, max_results=3, region="wt-wt", jurisdiction=jurisdiction)
                )
            except Exception as exc:
                logger.warning("web text query failed (%s): %s", q[:60], exc)
            try:
                merged.extend(_ddg_news(q, max_results=3))
            except Exception as exc:
                logger.warning("web news query failed (%s): %s", q[:60], exc)

    return _dedupe_results(merged)


def _search_duckduckgo(question: str, max_results: int) -> tuple[str, list[Citation], int]:
    from app.services.language import build_open_web_queries, detect_jurisdiction

    jur = detect_jurisdiction(question)
    queries = build_open_web_queries(question)
    merged = _collect_web_results(
        question, queries, max_results=max_results, jurisdiction=jur, locale="fr"
    )
    ranked = _rank_results(merged, jur)
    chosen = ranked[:max_results]
    return _parse_results(chosen)


def _ensure_official_portal(citations: list[Citation], jurisdiction: str) -> list[Citation]:
    if jurisdiction == "fr":
        if any("legifrance" in (c.label or "").lower() or "legifrance" in (c.url or "").lower() for c in citations):
            return citations
        return [_LEGIFRANCE_PORTAL, *citations]
    if jurisdiction == "ma":
        if any("sgg.gov.ma" in (c.label or "") or "sgg.gov.ma" in (c.url or "") for c in citations):
            return citations
        return [_SGG_PORTAL, *citations]
    return citations


def search_web(question: str, max_results: int = 5) -> tuple[str, list[Citation], int]:
    """Search the open web — queries follow the question (MA / FR / general)."""
    from app.services.language import detect_jurisdiction

    jur = detect_jurisdiction(question)
    key = _cache_key(question, max_results, mode=f"open-{jur}-v4")
    cached = _get_cached(key)
    if cached:
        return cached

    provider = settings.WEB_SEARCH_PROVIDER.lower()
    data: tuple[str, list[Citation], int] = ("", [], 0)

    if provider == "tavily" and settings.TAVILY_API_KEY:
        try:
            data = _search_tavily(question, max_results)
        except Exception as exc:
            logger.warning("Tavily search failed (%s), falling back to DuckDuckGo", exc)

    if not data[1]:
        try:
            data = _search_duckduckgo(question, max_results)
        except Exception as exc:
            logger.warning("Web search failed: %s", exc)

    if data[1]:
        text, citations, score = data
        from app.services.topic_filter import filter_citations_by_topic, tokenize_question

        # Ne pas filtrer trop fort les actus (loi 19.25, etc.)
        if tokenize_question(question):
            topical = filter_citations_by_topic(
                citations, question, keep_official_portal=False
            )
            if topical:
                citations = topical
                excerpts = [
                    f"SOURCE {i} — {c.label}\nURL: {c.url or ''}\n{c.excerpt}"
                    for i, c in enumerate(citations, 1)
                ]
                text = "\n\n".join(excerpts)
                score = min(78, 50 + len(citations) * 5)
            # sinon garder les citations brutes (mieux que portail seul)
        if citations:
            # Portail SGG en appoint seulement s'il y a déjà du contenu utile
            if not is_thin_portal_only(citations):
                citations = _ensure_official_portal(citations, jur)
            data = (text, citations, score)
            _set_cache(key, data)
        else:
            data = ("", [], 0)
    return data


def is_thin_portal_only(citations: list[Citation]) -> bool:
    if not citations:
        return True
    non_portal = [
        c
        for c in citations
        if "sgg.gov.ma" not in (c.url or "").lower()
        and "legifrance" not in (c.url or "").lower()
        and "bulletin officiel" not in (c.label or "").lower()
    ]
    return len(non_portal) == 0


def search_web_for_recent_laws(
    question: str, max_results: int = 6, locale: str = "fr"
) -> tuple[str, list[Citation], int]:
    """Multi-query web search for recent legislation (MA or FR)."""
    from app.services.language import build_open_web_queries, build_recent_law_web_queries, detect_jurisdiction

    jur = detect_jurisdiction(question)
    key = _cache_key(question, max_results, mode=f"recent-laws-{locale}-{jur}-v4")
    cached = _get_cached(key)
    if cached:
        return cached

    if jur == "fr":
        queries = build_open_web_queries(question)
    else:
        queries = build_recent_law_web_queries(question, locale=locale)

    merged = _collect_web_results(
        question, queries, max_results=max_results, jurisdiction=jur, locale=locale
    )

    from app.services.topic_filter import filter_citations_by_topic, tokenize_question

    ranked = _rank_results(merged, jur)
    topic = tokenize_question(question)
    if topic:
        topical = [
            r
            for r in ranked
            if any(
                t in " ".join(str(r.get(k, "")).lower() for k in ("title", "body", "url"))
                for t in topic
            )
        ]
        chosen = (topical or ranked)[:max_results]
    else:
        chosen = ranked[:max_results]

    if not chosen:
        portal = _LEGIFRANCE_PORTAL if jur == "fr" else _SGG_PORTAL
        url = portal.url or ""
        citations = [portal]
        text = f"SOURCE 1 — {portal.label}\nURL: {url}\n{portal.excerpt}"
        data = (text, citations, 40)
    else:
        text, citations, score = _parse_results(chosen)
        filtered = filter_citations_by_topic(
            citations, question, keep_official_portal=False
        )
        citations = filtered or citations
        if not is_thin_portal_only(citations):
            citations = _ensure_official_portal(citations, jur)
        excerpts = [
            f"SOURCE {i} — {c.label}\nURL: {c.url or ''}\n{c.excerpt}"
            for i, c in enumerate(citations, 1)
        ]
        text = "\n\n".join(excerpts)
        score = min(82, 52 + len(citations) * 5)
        data = (text, citations, score)

    _set_cache(key, data)
    return data


def search_web_parallel(questions: list[str], max_results: int = 3) -> list[tuple[str, list[Citation], int]]:
    """Run multiple web queries in parallel (for hybrid agent)."""
    results: list[tuple[str, list[Citation], int]] = [("", [], 0)] * len(questions)
    with ThreadPoolExecutor(max_workers=min(3, len(questions))) as pool:
        futures = {pool.submit(search_web, q, max_results): i for i, q in enumerate(questions)}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                results[idx] = fut.result()
            except Exception as exc:
                logger.warning("Parallel web search error: %s", exc)
    return results
