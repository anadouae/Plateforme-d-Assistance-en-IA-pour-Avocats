"""Dictée vocale → correction (AR/FR) → document officiel marocain."""

from __future__ import annotations

import logging
import re

from app.core.config import settings
from app.services.arabic_text_fix import (
    finalize_arabic_polish,
    light_arabic_fusha_form,
    light_arabic_punctuation,
    repair_arabic_stt,
    repair_stt_garbage,
    split_legal_phrases,
    strip_markdown_noise,
)
from app.services.free_llm_router import chat_free_tier
from app.services.plaidoirie_postprocess import (
    compose_completeness_check,
    fidelity_structure_plaidoirie,
    postprocess_plaidoirie_body,
)
from app.services.plaidoirie_prompt import (
    PLAIDOIRIE_TYPES,
    compose_fallback_system,
)

logger = logging.getLogger(__name__)

DOC_TYPES = {
    "plaidoirie": "مرافعة (Plaidoirie)",
    "general": "وثيقة قانونية عامة",
    "petition": "مقال افتتاحي / عريضة",
    "memo": "مذكرة دفاع",
    "letter": "رسالة رسمية",
    "minutes": "عرض حال / محضر",
}

DOC_TYPES_FR = {
    "plaidoirie": "Plaidoirie",
    "general": "Document juridique",
    "petition": "Requête / assignation",
    "memo": "Mémoire en défense",
    "letter": "Courrier officiel",
    "minutes": "Procès-verbal",
}

POLISH_SYSTEM_AR = """أنت مراجع تفريغ صوتي لمحامٍ مغربي — ذكي كـ ChatGPT.

الهدف: نص عربي فصيح مفهوم. إذا كان المصدر فيه أخطاء إملائية / حروف ناقصة / كلمات مكسورة،
اقترب من أقرب كلمة عربية صحيحة (تحية، صيغة محكمة، لفظ قانوني شائع). لا ترفض التصحيح بسهولة.

=== مطلوب بقوة ===
1) تقريب الأخطاء الإملائية إلى أقرب كلمة صحيحة (مثال: السلا→السلام، الؤيس→‹الرئيس›، م→من إن اتضح).
2) ضع بين ‹ › فقط الكلمات التي خمّنتها بقوة شك (بديل STT).
3) حذف التكرار العبثي والحلقات.
4) نحو وهمزات وترقيم عربي (، . ؛ ؟).
5) الأسماء والأرقام والتواريخ والمبالغ تُنسخ كما هي إن وُجدت بوضوح.

=== ممنوع ===
- اختلاق قضية كاملة / أسماء / مبالغ / مواد قانون لم تظهر في المصدر.
- تلخيص يحذف فكرتين مختلفتين.
- مقدمة أو تعليق خارج النص.

=== __NONSENSE__ فقط في هذه الحالة النادرة ===
المصدر كله نقرات لوحة / علامات فقط / حروف لاتينية عشوائية بلا أي كلمة عربية قابلة للتخمين.
لا تُخرج __NONSENSE__ لمجرد أن الجملة قصيرة أو فيها أخطاء إملائية — صحّحها.

=== الخرج ===
النص الفصيح فقط، أو __NONSENSE__."""


POLISH_SYSTEM_AR_AUDIO = POLISH_SYSTEM_AR

POLISH_SYSTEM_FR = """Tu es un réviseur intelligent de dictée juridique marocaine (français) — aussi souple que ChatGPT.

But : texte clair. Si fautes / lettres manquantes / mots cassés → approche le mot français correct le plus proche.
N’abandonne pas facilement.

Autorisé :
1) Orthographe, grammaire, ponctuation, approximation de typos.
2) Mots STT incertains → un seul mot plausible entre ‹ ›.
3) Supprimer redondances / boucles STT.

Interdit :
1) Inventer une affaire, noms, montants, articles absents.
2) Markdown / commentaires hors texte.

__NONSENSE__ uniquement si la source est du pur clavier au hasard (asdf, ;;; ) sans aucun mot récupérable.
Pas pour une phrase courte ou mal orthographiée — corrige-la.

Sortie : texte corrigé uniquement, ou __NONSENSE__."""


COMPOSE_SYSTEM_FR = """Tu es un assistant de rédaction juridique marocain (français).
À partir du texte source, produis un document structuré pour le tribunal.

Format de sortie OBLIGATOIRE :
TITLE: <titre court>
BODY:
<corps structuré avec points numérotés si pertinent>
CHECKS:
- <points à vérifier, ou « aucun »>
"""


def _normalize_lang(language: str | None) -> str:
    lang = (language or "ar").strip().lower()
    if lang.startswith("fr"):
        return "fr"
    return "ar"


def _polish_local_only() -> bool:
    """Ollama-only pour polish — désactivé sur VPS sans Ollama (défaut False)."""
    return bool(getattr(settings, "DICTATION_POLISH_LOCAL_ONLY", False))


def _llm(
    prompt: str,
    system: str,
    preferred: str = "openai",
    *,
    max_tokens: int = 4096,
    temperature: float = 0.35,
    model_override: str | None = None,
) -> tuple[str | None, str]:
    # Whisper reste local/Groq (STT). Correction = ChatGPT gpt-4o (pas mini).
    premium = (getattr(settings, "OPENAI_MODEL", None) or "gpt-4o").strip() or "gpt-4o"
    if "mini" in premium.lower():
        premium = "gpt-4o"
    model = (model_override or premium).strip()
    return chat_free_tier(
        prompt,
        system,
        preferred=preferred,
        strict_preferred=True,
        local_only=_polish_local_only(),
        allow_ollama=not bool(getattr(settings, "LLM_FORCE_OPENAI", True)),
        max_tokens=max_tokens,
        temperature=temperature,
        model_override=model,
    )


def _stt_garbage_heavy(text: str) -> bool:
    """Dictée très répétitive / bruit STT — autorise un nettoyage LLM plus agressif."""
    tokens = [t for t in re.split(r"\s+", (text or "").strip()) if t]
    if len(tokens) < 10:
        return False
    uniq = len(set(tokens)) / len(tokens)
    if uniq < 0.42:
        return True
    # Trigrammes répétés
    if len(tokens) >= 18:
        tris = [" ".join(tokens[i : i + 3]) for i in range(len(tokens) - 2)]
        if tris:
            top = max(tris.count(t) for t in set(tris))
            if top >= 4:
                return True
    return False


def _strip_fences(text: str) -> str:
    return strip_markdown_noise(text or "")


def _collapse_repeats(text: str) -> str:
    """Réduit uniquement les doublons STT évidents — ne coupe jamais le début du texte."""
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if not t:
        return ""
    # Doublons de mots consécutifs : « ان ان » / « الملف الملف »
    t = re.sub(r"(\S{1,40})(?:\s+\1){1,}", r"\1", t)
    # Doublons de phrases séparées par ponctuation
    parts = re.split(r"(?<=[.。؟!?،,;؛])\s+", t)
    if len(parts) >= 2:
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
            # Uniquement égalité quasi exacte (pas Jaccard large)
            if out and (p == out[-1] or (len(p) > 20 and p in out[-1])):
            continue
        out.append(p)
    t = " ".join(out)
    # Répétition littérale d'un long segment collé deux fois d'affilée
    for _ in range(3):
        nxt = re.sub(r"(.{24,}?)(?:\s+\1){1,}", r"\1", t)
        if nxt == t:
            break
        # Sécurité : ne jamais raccourcir de plus de 35 %
        if len(nxt) < int(len(t) * 0.65):
            break
        t = nxt
    return t.strip()


_NONSENSE_MARK = "__NONSENSE__"


_AR_GLUE = frozenset(
    {
        "في",
        "من",
        "على",
        "إلى",
        "الى",
        "أن",
        "ان",
        "إن",
        "هذا",
        "هذه",
        "ذلك",
        "تلك",
        "هو",
        "هي",
        "هم",
        "كان",
        "كانت",
        "لم",
        "لن",
        "قد",
        "أو",
        "او",
        "و",
        "ما",
        "لا",
        "بعد",
        "قبل",
        "بين",
        "عن",
        "مع",
        "كل",
        "أي",
        "اي",
        "التي",
        "الذي",
        "ثم",
        "لأن",
        "لان",
        "حيث",
        "إذا",
        "اذا",
        "حتى",
        "موكل",
        "موكلي",
        "محكمة",
        "قضية",
        "طلب",
        "يطالب",
        "السيد",
        "السيدة",
        "ضد",
        "لفائدة",
    }
)


def _norm_ar_token(w: str) -> str:
    w = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", w or "")
    w = w.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    w = w.replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"^[^\u0600-\u06FF]+|[^\u0600-\u06FF]+$", "", w)


def _arabic_looks_like_nonsense(text: str) -> bool:
    """Charabia arabe irrécupérable (pas des fautes à corriger via LLM)."""
    if not re.search(r"[\u0600-\u06FF]", text or ""):
        return False
    words = [_norm_ar_token(w) for w in re.split(r"\s+", text.strip())]
    words = [w for w in words if len(w) >= 2]
    # Lettres isolées seulement (« ك ك ك »)
    if not words:
        singles = [w for w in re.split(r"\s+", (text or "").strip()) if re.search(r"[\u0600-\u06FF]", w)]
        return len(singles) >= 3 and all(len(_norm_ar_token(w) or w) <= 1 for w in singles)
    ar_letters = len(re.findall(r"[\u0600-\u06FF]", text))
    if ar_letters < 4:
        return False
    compact = re.sub(r"\s+", "", text)
    # Même lettre répétée (ككككك)
    if re.search(r"(.)\1{4,}", compact):
        return True
    # Ne PAS traiter les fautes / mots cassés comme nonsense — ChatGPT doit approximer
    return False


def looks_like_nonsense(text: str) -> bool:
    """Pur clavier au hasard — pas une phrase fautive à corriger."""
    t = (text or "").strip()
    if not t:
        return False
    compact = re.sub(r"\s+", "", t)
    letters = re.sub(r"[^\w\u0600-\u06FF]", "", t)
    words = [w for w in re.split(r"\s+", t) if len(re.sub(r"[^\w\u0600-\u06FF]", "", w)) >= 2]
    has_ar = bool(re.search(r"[\u0600-\u06FF]", t))
    lower = t.lower()
    if re.fullmatch(r"[\W_]+", compact or ""):
        return True
    if re.search(r"(?:asdf|qwer|azerty|qwerty|zxcv|hjkl|1234|aaaa|bbbb|xxxx|zzzz|ffff|dddd)", lower) and len(words) < 6:
        return True
    if re.search(r"(.)\1{4,}", compact) and len(words) < 5:
        return True
    if (not has_ar) and len(words) <= 1 and 0 < len(letters) < 8:
        return True
    if (not has_ar) and len(letters) >= 4:
        vowels = len(re.findall(r"[aeiouyàâäéèêëïîôùûüœæAEIOUY]", t))
        if vowels == 0 and len(words) < 4:
            return True
    if (not has_ar) and 2 <= len(words) <= 8:
        tiny = sum(1 for w in words if len(re.sub(r"[^\w]", "", w)) <= 2)
        if tiny / max(len(words), 1) >= 0.7 and len(letters) < 28:
            return True
    if has_ar and _arabic_looks_like_nonsense(t):
        return True
    return False


def _near_dup(a: str, b: str) -> bool:
    """Similarité élevée (chevauchement STT) — pas une égalité stricte."""
    x = re.sub(r"\s+", " ", (a or "").strip())
    y = re.sub(r"\s+", " ", (b or "").strip())
    if not x or not y:
        return False
    if x == y:
        return True
    if len(x) < 12 or len(y) < 12:
        return False
    if x in y or y in x:
        return True
    # Jaccard sur tokens
    sx, sy = set(x.split()), set(y.split())
    if not sx or not sy:
        return False
    inter = len(sx & sy)
    union = len(sx | sy)
    return union > 0 and (inter / union) >= 0.82


def polish_arabic_dictation(raw: str) -> tuple[str, str]:
    """Rétrocompat : polish arabe."""
    return polish_dictation(raw, language="ar")


def polish_dictation(
    raw: str,
    language: str = "ar",
    *,
    source: str = "dictation",
) -> tuple[str, str]:
    """
    Nettoie une dictée AR/FR.
    Par défaut DICTATION_POLISH_USE_LLM=True : ChatGPT pour la forme fusḥā.
    Retourne (texte, provider).
    """
    lang = _normalize_lang(language)
    text = (raw or "").strip()
    if not text:
        return "", "none"
    text = _collapse_repeats(text)
    if lang == "ar":
        text = repair_stt_garbage(text)
        text = repair_arabic_stt(text)
        text = light_arabic_fusha_form(text)
        text = split_legal_phrases(text)
        text = light_arabic_punctuation(text)
        text = finalize_arabic_polish(text)
    text = text.strip()
    if not text:
        return "", "none"

    # Pur clavier (asdf / ;;;) → refuse. Fautes arabes / mots cassés → toujours vers le LLM.
    hard_mash = looks_like_nonsense(text) and not re.search(r"[\u0600-\u06FF]{2,}", text or "")
    if hard_mash and looks_like_nonsense(raw or ""):
        return text, "nonsense"

    use_llm = bool(getattr(settings, "DICTATION_POLISH_USE_LLM", True))
    if not use_llm:
        # Forme fusḥā locale (sans LLM) — conserve ‹…› des substitutions STT
        return text, "fidelity"

    if len(text) < 4:
        return text, "passthrough"

    garbage = _stt_garbage_heavy(text) or _stt_garbage_heavy(raw or "")
    # Phrase courte / fautive : pousser l’approximation (température un peu plus haute)
    typo_short = len(text) < 320 or len(text.split()) <= 45

    if lang == "fr":
        system = POLISH_SYSTEM_FR
        prompt = (
            "Corrige et approche les mots corrects (typos, lettres manquantes). "
            "N’invente aucun fait juridique absent. "
            + ("Source très bruitée — nettoie et approximate.\n\n" if garbage else "\n")
            + f"Texte source :\n\n{text}"
        )
    else:
        system = POLISH_SYSTEM_AR_AUDIO if source == "audio" else POLISH_SYSTEM_AR
        prompt = (
            "صحّح وقرّب الكلمات الصحيحة (أخطاء إملائية، حروف ناقصة). "
            "لا تختلق وقائع قانونية غائبة. "
            + ("المصدر مليء بالضوضاء — نظّف وقرّب.\n\n" if garbage else "\n")
            + f"النص المصدر:\n\n{text}"
        )

    out, provider = _llm(prompt, system, temperature=0.45 if (garbage or typo_short) else 0.3)
    if not out:
        logger.warning("Dictation polish LLM unavailable — returning fidelity clean")
        return text, "fidelity"
    cleaned = strip_markdown_noise(_strip_fences(out))
    if _NONSENSE_MARK in (cleaned or "").upper().replace(" ", ""):
        # Si le modèle refuse à tort une phrase arabe fautive, on garde le local (pas d’effacement)
        if re.search(r"[\u0600-\u06FF]{3,}", text):
            logger.info("LLM returned NONSENSE on Arabic typos — keeping local text for user edit")
            return text, "fidelity"
        return text, "nonsense"
    # Normaliser les marqueurs de substitution STT vers ‹…›
    cleaned = cleaned.replace("«", "‹").replace("»", "›")
    cleaned = re.sub(r"<([^<>]{2,60})>", r"‹\1›", cleaned)
    if lang == "ar":
        cleaned = repair_arabic_stt(cleaned)
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if "،" not in cleaned and "." not in cleaned and "؟" not in cleaned:
            cleaned = light_arabic_punctuation(cleaned)
    # Garde-fous : inventer ≠ raccourcir du bruit STT / approximation courte
    tokens = text.split()
    uniq_ratio = (len(set(tokens)) / max(1, len(tokens))) if tokens else 1.0
    if garbage or uniq_ratio < 0.42 or typo_short:
        min_keep = 0.12
        max_expand = 2.4
    else:
        min_keep = 0.78
        max_expand = 1.55
    if len(cleaned) > int(len(text) * max_expand) + 100:
        logger.warning("Polish LLM expanded text — falling back to fidelity")
        cleaned = text
        provider = "fidelity"
    elif len(cleaned) < max(8, int(len(text) * min_keep)):
        # Bruit STT / approximation : un raccourci fort est OK si le résultat reste non vide
        if (garbage or typo_short) and len(cleaned) >= 6:
            logger.info(
                "Polish LLM shortened/approximated (%s→%s) — kept",
                len(text),
                len(cleaned),
            )
        else:
            logger.warning(
                "Polish LLM shortened text (likely summary) — falling back to fidelity (%s→%s)",
                len(text),
                len(cleaned),
            )
            cleaned = text
            provider = "fidelity"
    else:
        cleaned = cleaned or text

    # Post-traitement déterministe (même en mode fidelity)
    try:
        from app.services.dictation_contradictions import (
            annotate_stt_guesses,
            content_word_coverage,
            list_missing_source_facts,
            preserve_source_facts,
            restore_source_names,
            strip_reinjection_notes,
        )

        if provider != "fidelity" and not garbage and not typo_short:
            # Textes longs « propres » : empêcher un résumé qui efface le fond.
            # Mais ne pas jeter ChatGPT pour de simples corrections orthographiques
            # (cov un peu bas alors que missing=0).
            body = strip_reinjection_notes(cleaned)
            body = restore_source_names(text, body)
            missing = list_missing_source_facts(text, body)
            hard_missing = [m for m in missing if m[0] != "idea"]
            cov = content_word_coverage(text, body)
            cov_floor = 0.42 if uniq_ratio < 0.40 else 0.78
            soft_floor = 0.35  # orthographe / fusḥā / STT cassé — garder ChatGPT
            drop = False
            if hard_missing:
                drop = True
            elif cov < soft_floor:
                drop = True
            elif cov < cov_floor:
                # cov moyen : garder ChatGPT (correction de forme), log seulement
                logger.info(
                    "Polish LLM cov soft-keep (missing=0 cov=%.2f floor=%.2f) — keep %s",
                    cov,
                    cov_floor,
                    provider,
                )
            if drop:
                logger.warning(
                    "Polish LLM dropped fond (missing=%s cov=%.2f uniq=%.2f) — fidelity",
                    len(hard_missing),
                    cov,
                    uniq_ratio,
                )
                cleaned = text
                provider = "fidelity"
        elif provider != "fidelity" and (garbage or typo_short):
            # Approximation ChatGPT : garder le résultat, juste restaurer les noms clairs
            cleaned = restore_source_names(text, cleaned)
            logger.info(
                "Polish LLM kept (typo/garbage path) provider=%s len %s→%s",
                provider,
                len(text),
                len(cleaned),
            )
        if lang == "ar":
            # Réappliquer les substitutions STT→fusḥā (‹…›) après le LLM,
            # qui omet souvent les marqueurs.
            cleaned = light_arabic_fusha_form(repair_arabic_stt(cleaned))
        cleaned, _guessed = annotate_stt_guesses(text, cleaned)
        # Garder ‹…› (surlignage orange) pour substitutions STT locales / LLM
        cleaned = restore_source_names(text, cleaned)
        if provider != "fidelity" and not garbage and not typo_short:
            cleaned = preserve_source_facts(text, cleaned)
    except Exception as exc:
        logger.warning("Post-polish fact/annotate failed: %s", exc)
    return cleaned, provider


def _clean_compose_body(body: str) -> str:
    """Retire tags parasites, placeholders vides, en-tête/pied dupliqués (export les ajoute)."""
    text = (body or "").strip()
    if not text:
        return text
    # Artefact LLM / STT : « جده وحيد » n'est PAS une formule judiciaire marocaine
    text = re.sub(
        r"^\s*جده\s*وحيد[،,]?\s*",
        "السيد رئيس المحكمة المحترم،\n\n",
        text,
        count=1,
    )
    text = re.sub(r"جده\s*وحيد[،,]?\s*", "", text)
    text = re.sub(r"محامي\s*لـ?\s*ة", "المحامية", text)
    text = re.sub(r"المحامي\s*لـ?\s*ة", "المحامية", text)
    text = re.sub(r"حزام\s*الجنائي", "محامية بهيئة المحامين", text)
    # Tags FR → marqueur arabe
    text = re.sub(
        r"\[\s*(?:À\s*VÉRIFIER|A\s*VERIFIER|TO\s*VERIFY|ART\.?\s*À\s*COMPLÉTER|"
        r"ART\.?\s*A\s*COMPLETER)[^\]]*\]",
        "[يُستكمل]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\[\s*اسم[^\]]*\]", "[يُستكمل: الاسم]", text)
    # Crochets vides / tirets orphelins après les titres de section
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"([:：])\s*[—\-–]+\s*", r"\1 ", text)
    text = re.sub(r"([:：])\s*/\s*", r"\1 ", text)
    # …… après libellé → marqueur clair (pas de [] vide)
    def _label_placeholder(m: re.Match) -> str:
        label = m.group(1).strip().rstrip(":")
        return f"{label}: [يُستكمل: {label}]"

    text = re.sub(
        r"([^\n:：]{2,40})\s*[:：]\s*(?:\.{3,}|…{2,}|……+)\s*",
        _label_placeholder,
        text,
    )
    text = re.sub(r"(?:\.{4,}|…{3,}|……+)", "[يُستكمل]", text)
    # Titre « صيغة الختام » → phrase courte sans inventer signature (l'export ajoute حرر/توقيع)
    text = re.sub(
        r"(?m)^\s*(?:7[\)\.]?\s*)?صيغة\s*الختام\s*:?\s*",
        "تحت جميع التحفظات القانونية.\n",
        text,
    )
    text = re.sub(r"صيغة\s*الختام\s*[:：]?\s*", "", text)
    # Pied déjà géré à l'export Word/PDF — retirer du corps
    text = re.sub(
        r"(?ms)(?:^|\n)\s*حرر\s*بـ?[^\n]*(?:\n\s*التوقيع[^\n]*)?(?:\n\s*(?:ذ\.|الأستاذ|خاتم)[^\n]*)*\s*$",
        "",
        text,
    )
    text = re.sub(r"(?m)^\s*التوقيع\s*(?:—|-)?\s*(?:ذ\.?)?\s*[.…\[]*[^\n]*$", "", text)
    text = re.sub(r"(?m)^\s*خاتم\s*المحامي\s*$", "", text)
    text = re.sub(r"\bCasablanca\b", "الدار البيضاء", text, flags=re.IGNORECASE)
    # Retirer en-tête institutionnel du corps (ajouté à l'export)
    lines = text.split("\n")
    cleaned_lines: list[str] = []
    skipping_header = True
    header_markers = (
        "المملكة المغربية",
        "Royaume du Maroc",
        "المحكمة",
        "الجهة القضائية",
        "رقم الملف",
        "تاريخ الجلسة",
        "تاريخ التحرير",
        "المكتب",
        "المحامي",
        "المحامية",
    )
    for raw in lines:
        line = raw.strip()
        if skipping_header:
            if not line:
                continue
            if any(line.startswith(m) for m in header_markers):
                continue
            if re.match(r"^[\.\…]{3,}$", line):
                continue
            skipping_header = False
        if not line:
            cleaned_lines.append(raw)
            continue
        if re.match(r"^(حرر\s*ب|التوقيع|خاتم\s*المحامي)\b", line):
            continue
        cleaned_lines.append(raw)
    text = "\n".join(cleaned_lines).strip() or text
    text = re.sub(
        r"(?<!\n)\s*(تحديد\s*الأطراف|أولاً|ثانياً|ثالثاً|رابعاً|خامساً|سادساً|لهذه\s*الأسباب|الملتمسات)\s*[:：]?",
        r"\n\n\1 :",
        text,
    )
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def _parse_compose_output(
    cleaned: str,
    hint_title: str,
    plaidoirie_type: str | None = None,
    source_text: str = "",
) -> tuple[str, str, list[str]]:
    title_out = hint_title
    body_out = cleaned
    checks: list[str] = []

    if "TITLE:" in cleaned and "BODY:" in cleaned:
        try:
            after_title = cleaned.split("TITLE:", 1)[1]
            if "BODY:" in after_title:
                title_part, rest = after_title.split("BODY:", 1)
                title_out = title_part.strip().splitlines()[0].strip() or hint_title
                if "CHECKS:" in rest:
                    body_part, checks_part = rest.split("CHECKS:", 1)
                    body_out = body_part.strip()
                    for line in checks_part.strip().splitlines():
                        item = line.strip().lstrip("-•*").strip()
                        if item and item not in {"لا شيء", "aucun", "none", "—"}:
                            checks.append(item)
                else:
                    body_out = rest.strip()
        except Exception:
            body_out = cleaned
    body_out = _clean_compose_body(body_out)
    body_out, section_warnings = postprocess_plaidoirie_body(
        body_out,
        source_text=source_text or body_out,
        plaidoirie_type=plaidoirie_type,
        for_export=False,
    )
    checks.extend(section_warnings)
    return title_out, body_out, checks


def compose_official_document(
    body: str,
    *,
    doc_type: str = "plaidoirie",
    title: str | None = None,
    city: str | None = None,
    cabinet_name: str | None = None,
    plaidoirie_type: str | None = None,
    language: str = "ar",
) -> tuple[str, str, str, list[str]]:
    """
    Rédige le corps du document officiel.
    Retourne (title, body, provider, checks).
    """
    lang = _normalize_lang(language)
    body = (body or "").strip()
    source_text = body
    if not body:
        return "", "", "none", []

    if lang == "fr":
        kind = DOC_TYPES_FR.get(doc_type, DOC_TYPES_FR["general"])
        hint_title = title.strip() if title else kind
        extras = []
        if city:
            extras.append(f"Ville proposée : {city}")
        if cabinet_name:
            extras.append(f"Cabinet : {cabinet_name}")
        system = COMPOSE_SYSTEM_FR
        prompt = (
            f"Type de document : {kind}\n"
            f"Titre suggéré : {hint_title}\n"
            + ("\n".join(extras) + "\n" if extras else "")
            + "\nTexte source :\n\n"
            f"{body}\n\n"
            "Réponds au format TITLE / BODY / CHECKS."
        )
        text, provider = _llm(prompt, system)
        if not text:
            return hint_title, body, "none", []
        cleaned = strip_markdown_noise(_strip_fences(text))
        title_out, body_out, checks = _parse_compose_output(
            cleaned, hint_title, plaidoirie_type=None, source_text=source_text
        )
        return strip_markdown_noise(title_out), strip_markdown_noise(body_out), provider, checks

    kind = DOC_TYPES.get(doc_type, DOC_TYPES["general"])
    hint_title = title.strip() if title else kind
    extras = []
    if city:
        extras.append(f"المدينة المقترحة للتذييل: {city}")
    if cabinet_name:
        extras.append(f"اسم المكتب: {cabinet_name}")

    type_id = (plaidoirie_type or "").strip()
    if doc_type == "plaidoirie":
        if type_id not in PLAIDOIRIE_TYPES:
            type_id = "libre"

    # === RÈGLE D’OR ===
    # Contenu = 100 % dictée avocat. On ne fait QUE la mise en page
    # (sections, parties, espaces) — JAMAIS de réécriture LLM.
    if doc_type == "plaidoirie":
        fidelity_body = fidelity_structure_plaidoirie(source_text) or source_text
        body_out, section_warnings = postprocess_plaidoirie_body(
            fidelity_body,
            source_text=source_text,
            plaidoirie_type=type_id,
            for_export=False,
        )
        # Si le postprocess a trop réduit le texte → revenir au source structuré brut
        src_len = len(re.sub(r"\s+", "", source_text))
        out_len = len(re.sub(r"\s+", "", body_out or ""))
        if src_len >= 200 and out_len < int(src_len * 0.7):
            body_out = fidelity_structure_plaidoirie(source_text) or source_text
            section_warnings.append(
                "⚠️ Mise en page seule — le texte de l’avocat a été conservé intégralement."
            )
        _, completeness = compose_completeness_check(source_text, body_out)
        type_label = PLAIDOIRIE_TYPES.get(type_id, type_id)
        checks = [
            f"نوع المرافعة المعتمد: {type_label} ({type_id})",
        ] + section_warnings + completeness
        title_out = hint_title or "مرافعة"
        return (
            strip_markdown_noise(title_out),
            strip_markdown_noise(body_out),
            "fidelity",
            checks,
        )

    # Autres types (non-plaidoirie) : LLM encore possible, avec filet fidélité
        system = compose_fallback_system()
        type_line = f"نوع الوثيقة: {kind}\n"
    role_block = ""

    prompt = (
        type_line
        + role_block
        + f"عنوان مقترح: {hint_title}\n"
        + ("\n".join(extras) + "\n" if extras else "")
        + "\nالنص المصدر:\n\n"
        f"{body}\n\n"
        "أرجع TITLE / BODY / CHECKS.\n"
        "انسخ النص المصدر كاملاً — ممنوع التلخيص أو الاختلاق."
    )
    text, provider = _llm(prompt, system, max_tokens=8192, temperature=0.1)
    if not text:
        return hint_title, source_text, "none", []

    cleaned = strip_markdown_noise(_strip_fences(text))
    title_out, body_out, checks = _parse_compose_output(
        cleaned, hint_title, None, source_text=source_text
    )
    body_out = strip_markdown_noise(repair_arabic_stt(body_out))
    title_out = strip_markdown_noise(title_out)
    ok, completeness = compose_completeness_check(source_text, body_out)
    checks.extend(completeness)
    if not ok:
        body_out = source_text
        provider = "fidelity"
        checks.append(
            "⚠️ Contenu LLM incomplet — texte de l’avocat restauré sans modification."
        )
    return title_out, body_out, provider, checks
