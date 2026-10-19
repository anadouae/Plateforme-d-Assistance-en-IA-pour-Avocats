"""LexHub — pseudonymisation PII avant IA externe, restauration locale Word/PDF.

Conformité : Loi 09-08 (protection des données à caractère personnel) et secret
professionnel de l'avocat. Les identités, CIN, téléphones et e-mails ne quittent
jamais le cabinet vers un fournisseur d'IA : ils sont remplacés par des jetons
(PARTIE_*, CIN_*, TEL_*, EMAIL_*) puis restaurés localement à l'export.

Principe cabinet :
- Masquer avant tout appel LLM / STT externe.
- Conserver le mapping côté serveur (dossier) ou en mémoire de requête.
- Démasquer uniquement dans les documents finaux (Word, PDF, prévisualisation).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class PiiMaskResult:
    """Résultat de masquage : texte pseudonymisé + mapping jeton → original."""

    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # token -> original

    def unmask(self, text: str | None = None) -> str:
        """Restaure les valeurs originales dans `text` (défaut : self.text)."""
        return unmask_text(text if text is not None else self.text, self.mapping)


# ---------------------------------------------------------------------------
# Normalisation & variantes de noms
# ---------------------------------------------------------------------------


def _normalize_name(name: str) -> str:
    return " ".join((name or "").strip().split())


_COMMON_FIRST = {
    "mohamed",
    "mohammed",
    "ahmed",
    "fatima",
    "hassan",
    "said",
    "saïd",
    "youssef",
    "omar",
    "karim",
    "rachid",
    "najat",
    "khadija",
    "amina",
    "samira",
    "mustapha",
    "abdellah",
    "abdelilah",
    "hicham",
    "mehdi",
    "sara",
    "sarah",
}


def _name_variants(name: str) -> list[str]:
    """Variantes d'écriture pour mieux attraper le nom dans dictée / pièces."""
    n = _normalize_name(name)
    if not n or len(n) < 2:
        return []
    out = [n]
    parts = n.split()
    if len(parts) >= 2:
        out.append(" ".join(reversed(parts)))
        last = parts[-1]
        if len(last) >= 4:
            out.append(last)
        first = parts[0]
        if len(first) >= 4 and first.lower() not in _COMMON_FIRST:
            out.append(first)
    seen: set[str] = set()
    uniq: list[str] = []
    for v in out:
        k = v.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return uniq


# ---------------------------------------------------------------------------
# Détection structurée (CIN / téléphone / e-mail) — Maroc
# ---------------------------------------------------------------------------

# Labels explicites : CIN / CNIE / بطاقة وطنية / رقم البطاقة …
_CIN_LABELED_RE = re.compile(
    r"(?:"
    r"(?:N[°ºo.\s]*)?(?:CIN|CNIE|C\.?I\.?N\.?E?\.?)"
    r"|(?:بطاقة\s*(?:ال)?وطنية)"
    r"|(?:رقم\s*(?:ال)?بطاقة)"
    r"|(?:carte\s+nationale(?:\s+d['’]identité)?)"
    r")"
    r"[\s:=\-–—]*"
    r"([A-Za-z]{1,2}\s*[0-9]{4,8})",
    re.IGNORECASE,
)

# Bare CIN (ex. BK123456, BH 554321) près d'un contexte identité
_CIN_BARE_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z]{1,2}\s*[0-9]{5,7})(?![A-Za-z0-9])"
)

_CIN_CONTEXT_RE = re.compile(
    r"(?:"
    r"CIN|CNIE|identité|identite|carte\s+nationale|pièce\s+d['’]identité|"
    r"piece\s+d['’]identite|رقم|بطاقة|وطنية|هوية|porteur|titulaire|"
    r"né[e]?\s+le|née\s+le|domicilié|demeurant|client|partie|"
    r"défendeur|demanderesse|demandeur"
    r")",
    re.IGNORECASE,
)

# Téléphones Maroc : +212, 00212, 06/05/07 locaux (avec ou sans espaces/tirets)
_PHONE_RE = re.compile(
    r"(?<![\w@])"
    r"(?:"
    r"(?:\+|00)\s*212\s*[5-7](?:[\s.\-]*\d){8}"
    r"|(?:0)\s*[5-7](?:[\s.\-]*\d){8}"
    r")"
    r"(?![\w@])"
)

_EMAIL_RE = re.compile(
    r"(?<![\w.+-])"
    r"([A-Za-z0-9](?:[A-Za-z0-9._%+\-]*[A-Za-z0-9])?"
    r"@"
    r"[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?"
    r"\.[A-Za-z]{2,})"
    r"(?![\w.+-])"
)


def _norm_cin(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip()).upper()


def _norm_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("00212"):
        digits = "212" + digits[5:]
    if digits.startswith("212") and len(digits) >= 12:
        return "+" + digits
    if digits.startswith("0") and len(digits) == 10:
        return digits
    return digits or (value or "").strip()


def _norm_email(value: str) -> str:
    return (value or "").strip().lower()


def detect_structured_hits(text: str) -> list[tuple[str, str]]:
    """
    Détecte CIN, téléphones et e-mails dans `text`.

    Retourne une liste de (kind, value) avec kind ∈ {cin, phone, email}.
    Les valeurs sont normalisées (CIN majuscules sans espaces, e-mail lower, etc.).
    """
    src = text or ""
    hits: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def _add(kind: str, value: str) -> None:
        v = (value or "").strip()
        if not v:
            return
        if kind == "cin":
            v = _norm_cin(v)
            if not re.fullmatch(r"[A-Z]{1,2}[0-9]{4,8}", v):
                return
        elif kind == "phone":
            v = _norm_phone(v)
            if len(re.sub(r"\D", "", v)) < 9:
                return
        elif kind == "email":
            v = _norm_email(v)
            if "@" not in v:
                return
        key = (kind, v)
        if key in seen:
            return
        seen.add(key)
        hits.append((kind, v))

    for m in _EMAIL_RE.finditer(src):
        _add("email", m.group(1))

    for m in _PHONE_RE.finditer(src):
        _add("phone", m.group(0))

    for m in _CIN_LABELED_RE.finditer(src):
        _add("cin", m.group(1))

    # Bare CIN seulement près d'un contexte identité (±80 chars)
    for m in _CIN_BARE_RE.finditer(src):
        start, end = m.span(1)
        window = src[max(0, start - 80) : min(len(src), end + 80)]
        if _CIN_CONTEXT_RE.search(window):
            _add("cin", m.group(1))

    return hits


def _next_indexed_token(prefix: str, mapping: dict[str, str], start: int = 1) -> str:
    """Alloue CIN_1, TEL_2, EMAIL_3… sans collision avec mapping existant."""
    n = start
    while f"{prefix}_{n}" in mapping:
        n += 1
    return f"{prefix}_{n}"


def _next_partie_token(mapping: dict[str, str]) -> str:
    used_letters = {
        tok.replace("PARTIE_", "")
        for tok in mapping
        if tok.startswith("PARTIE_") and len(tok) == 8
    }
    for i in range(26):
        letter = chr(ord("A") + i)
        if letter not in used_letters and f"PARTIE_{letter}" not in mapping:
            return f"PARTIE_{letter}"
    n = 1
    while f"PARTIE_{n}" in mapping:
        n += 1
    return f"PARTIE_{n}"


def mask_structured_pii(
    text: str,
    mapping: dict[str, str] | None = None,
) -> PiiMaskResult:
    """
    Masque CIN, téléphones et e-mails détectés.

    Si `mapping` est fourni, il est enrichi (même objet logique : nouveau dict
    fusionné) et les jetons déjà connus sont réutilisés pour la même valeur.
    """
    out = text or ""
    result_map: dict[str, str] = dict(mapping or {})
    # reverse: (kind, normalized) -> token
    reverse: dict[tuple[str, str], str] = {}
    for tok, orig in result_map.items():
        if tok.startswith("CIN_"):
            reverse[("cin", _norm_cin(orig))] = tok
        elif tok.startswith("TEL_"):
            reverse[("phone", _norm_phone(orig))] = tok
        elif tok.startswith("EMAIL_"):
            reverse[("email", _norm_email(orig))] = tok

    # Remplacer e-mails d'abord (évite collision avec @ dans patterns)
    def _sub_email(m: re.Match[str]) -> str:
        raw = m.group(1)
        key = ("email", _norm_email(raw))
        if key in reverse:
            tok = reverse[key]
        else:
            tok = _next_indexed_token("EMAIL", result_map)
            reverse[key] = tok
            result_map[tok] = raw.strip()
        return tok

    out = _EMAIL_RE.sub(_sub_email, out)

    def _sub_phone(m: re.Match[str]) -> str:
        raw = m.group(0)
        key = ("phone", _norm_phone(raw))
        if key in reverse:
            tok = reverse[key]
        else:
            tok = _next_indexed_token("TEL", result_map)
            reverse[key] = tok
            result_map[tok] = raw.strip()
        return tok

    out = _PHONE_RE.sub(_sub_phone, out)

    def _sub_cin_labeled(m: re.Match[str]) -> str:
        raw = m.group(1)
        key = ("cin", _norm_cin(raw))
        if key in reverse:
            tok = reverse[key]
        else:
            tok = _next_indexed_token("CIN", result_map)
            reverse[key] = tok
            result_map[tok] = _norm_cin(raw)
        # Conserve le label, remplace seulement la valeur
        full = m.group(0)
        return full[: m.start(1) - m.start(0)] + tok

    out = _CIN_LABELED_RE.sub(_sub_cin_labeled, out)

    # Bare CIN près d'un contexte identité (positions après les remplacements précédents)
    bare_hits: list[tuple[int, int, str]] = []
    for m in _CIN_BARE_RE.finditer(out):
        raw = m.group(1)
        start, end = m.span(1)
        if re.search(r"\b(?:CIN|TEL|EMAIL|PARTIE)[_-]", raw, re.I):
            continue
        window = out[max(0, start - 80) : min(len(out), end + 80)]
        if _CIN_CONTEXT_RE.search(window):
            bare_hits.append((start, end, raw))

    for start, end, raw in sorted(bare_hits, key=lambda x: -x[0]):
        key = ("cin", _norm_cin(raw))
        if key in reverse:
            tok = reverse[key]
        else:
            tok = _next_indexed_token("CIN", result_map)
            reverse[key] = tok
            result_map[tok] = _norm_cin(raw)
        out = out[:start] + tok + out[end:]

    return PiiMaskResult(text=out, mapping=result_map)


# ---------------------------------------------------------------------------
# Parties (noms)
# ---------------------------------------------------------------------------


def build_mask_from_parties(
    text: str,
    *,
    parties: list[str] | None = None,
) -> PiiMaskResult:
    """Remplace les noms fournis (parties du dossier) par PARTIE_A, PARTIE_B…"""
    mapping: dict[str, str] = {}
    reverse: dict[str, str] = {}  # original lower -> token
    out = text or ""
    names = [_normalize_name(n) for n in (parties or []) if _normalize_name(n)]
    names = sorted(set(names), key=len, reverse=True)
    letter = ord("A")
    for name in names:
        if len(name) < 2:
            continue
        key = name.lower()
        if key in reverse:
            token = reverse[key]
        else:
            if letter <= ord("Z"):
                token = f"PARTIE_{chr(letter)}"
                letter += 1
            else:
                token = f"PARTIE_{len(mapping) + 1}"
            reverse[key] = token
            mapping[token] = name
            for variant in _name_variants(name):
                reverse[variant.lower()] = token

        for variant in _name_variants(name):
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            out = pattern.sub(token, out)
    return PiiMaskResult(text=out, mapping=mapping)


def mask_known_entities(text: str, entities: dict[str, str] | None = None) -> PiiMaskResult:
    """
    entities: {original: token} ou {label: "PARTIE_A"}.
    """
    mapping: dict[str, str] = {}
    out = text or ""
    if not entities:
        return PiiMaskResult(text=out, mapping=mapping)
    items: list[tuple[str, str]] = []
    for k, v in entities.items():
        original = _normalize_name(k)
        token = v.strip() if v and v.strip().startswith("PARTIE_") else ""
        if not original:
            continue
        items.append((original, token))
    items.sort(key=lambda x: -len(x[0]))
    auto = ord("A")
    for original, token in items:
        if not token:
            token = f"PARTIE_{chr(auto)}"
            auto += 1
        mapping[token] = original
        for variant in _name_variants(original):
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            out = pattern.sub(token, out)
    return PiiMaskResult(text=out, mapping=mapping)


def _apply_parties_with_base(
    text: str,
    parties: list[str] | None,
    base_mapping: dict[str, str] | None,
) -> PiiMaskResult:
    """Masque les parties en réutilisant les jetons déjà présents dans base_mapping."""
    mapping: dict[str, str] = dict(base_mapping or {})
    reverse: dict[str, str] = {}
    for tok, orig in mapping.items():
        if tok.startswith("PARTIE_"):
            reverse[_normalize_name(orig).lower()] = tok
            for v in _name_variants(orig):
                reverse[v.lower()] = tok

    out = text or ""
    names = [_normalize_name(n) for n in (parties or []) if _normalize_name(n)]
    names = sorted(set(names), key=len, reverse=True)

    for name in names:
        if len(name) < 2:
            continue
        key = name.lower()
        if key in reverse:
            token = reverse[key]
        else:
            # Cherche si une variante connue pointe déjà vers un jeton
            token = None
            for variant in _name_variants(name):
                if variant.lower() in reverse:
                    token = reverse[variant.lower()]
                    break
            if not token:
                token = _next_partie_token(mapping)
                mapping[token] = name
            reverse[key] = token
            for variant in _name_variants(name):
                reverse[variant.lower()] = token

        for variant in _name_variants(name):
            pattern = re.compile(re.escape(variant), re.IGNORECASE)
            out = pattern.sub(token, out)

    return PiiMaskResult(text=out, mapping=mapping)


# ---------------------------------------------------------------------------
# Fusion & inventaire
# ---------------------------------------------------------------------------


def merge_mappings(*maps: dict[str, str] | None) -> dict[str, str]:
    """
    Fusionne plusieurs mappings jeton → original.

    En cas de conflit de jeton, la première valeur non vide gagne.
    Les valeurs identiques sous des jetons différents sont conservées (pas de
    collapse) pour ne pas casser un unmask déjà planifié.
    """
    out: dict[str, str] = {}
    for m in maps:
        if not m:
            continue
        for k, v in m.items():
            tok = str(k).strip()
            val = str(v).strip() if v is not None else ""
            if not tok or not val:
                continue
            if tok not in out:
                out[tok] = val
    return out


def inventory_summary(mapping: dict[str, str] | None) -> dict[str, int]:
    """Compte les jetons par catégorie : parties, cin, phone, email, other."""
    summary = {"parties": 0, "cin": 0, "phone": 0, "email": 0, "other": 0}
    if not mapping:
        return summary
    for tok in mapping:
        t = tok.upper()
        if t.startswith("PARTIE_") or t.startswith("PARTIE-"):
            summary["parties"] += 1
        elif t.startswith("CIN_") or t.startswith("CIN-"):
            summary["cin"] += 1
        elif t.startswith("TEL_") or t.startswith("TEL-"):
            summary["phone"] += 1
        elif t.startswith("EMAIL_") or t.startswith("EMAIL-"):
            summary["email"] += 1
        else:
            summary["other"] += 1
    return summary


# ---------------------------------------------------------------------------
# Masquage complet
# ---------------------------------------------------------------------------


def build_full_mask(
    text: str,
    parties: list[str] | None = None,
    structured: bool = True,
    base_mapping: dict[str, str] | None = None,
) -> PiiMaskResult:
    """
    Pipeline complet : parties du dossier puis PII structurée (CIN/tél/e-mail).

    `base_mapping` permet de continuer un alphabet déjà alloué (ex. dossier).
    """
    party_result = _apply_parties_with_base(text or "", parties, base_mapping)
    mapping = dict(party_result.mapping)
    out = party_result.text

    if structured:
        struct = mask_structured_pii(out, mapping=mapping)
        out = struct.text
        mapping = struct.mapping

    return PiiMaskResult(text=out, mapping=mapping)


# ---------------------------------------------------------------------------
# Unmask (tolérant aux variantes LLM)
# ---------------------------------------------------------------------------


def _token_llm_variants(token: str) -> list[str]:
    """Génère les formes que le LLM peut produire pour un jeton canonique."""
    token = (token or "").strip()
    if not token or "_" not in token:
        return [token] if token else []

    prefix, _, rest = token.partition("_")
    if not rest:
        return [token]

    prefix_u = prefix.upper()
    prefix_t = prefix_u[:1] + prefix_u[1:].lower() if prefix_u else prefix
    prefix_l = prefix.lower()
    rest_u = rest.upper()
    rest_l = rest.lower()

    alts = [
        token,
        f"{prefix_u}_{rest}",
        f"{prefix_u}_{rest_u}",
        f"{prefix_u}-{rest}",
        f"{prefix_u}-{rest_u}",
        f"{prefix_u} {rest}",
        f"{prefix_u} {rest_u}",
        f"{prefix_t}_{rest}",
        f"{prefix_t} {rest}",
        f"{prefix_t}-{rest}",
        f"{prefix_l}_{rest_l}",
        f"{prefix_l} {rest_l}",
        f"{prefix_l}-{rest_l}",
        f"{prefix_l}_{rest}",
        f"{prefix_l}-{rest}",
    ]
    # Formes spécifiques historiques PARTIE
    if prefix_u == "PARTIE":
        alts.extend(
            [
                f"Partie_{rest}",
                f"Partie {rest}",
                f"Partie-{rest}",
                f"partie_{rest_l}",
                f"partie {rest_l}",
                f"partie-{rest_l}",
            ]
        )
    if prefix_u == "CIN":
        alts.extend([f"Cin_{rest}", f"Cin-{rest}", f"cin_{rest_l}", f"cin-{rest_l}"])
    if prefix_u == "TEL":
        alts.extend(
            [
                f"Tel_{rest}",
                f"Tel-{rest}",
                f"Tél_{rest}",
                f"Tél-{rest}",
                f"tel_{rest_l}",
                f"tel-{rest_l}",
            ]
        )
    if prefix_u == "EMAIL":
        alts.extend(
            [
                f"Email_{rest}",
                f"Email-{rest}",
                f"E-mail_{rest}",
                f"email_{rest_l}",
                f"email-{rest_l}",
            ]
        )

    seen: set[str] = set()
    uniq: list[str] = []
    for a in alts:
        if a and a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def unmask_text(text: str, mapping: dict[str, str]) -> str:
    """
    Restaure les valeurs originales.

    Tolère les variantes LLM : PARTIE-A, PARTIE A, partie_a, CIN-1, TEL_2,
    EMAIL-3, etc. Remplace les jetons les plus longs d'abord.
    """
    out = text or ""
    if not mapping:
        return out

    # Construire toutes les substitutions (variant -> original)
    subs: list[tuple[str, str]] = []
    for token, original in mapping.items():
        if not token or original is None:
            continue
        for alt in _token_llm_variants(token):
            subs.append((alt, original))

    # Plus long d'abord pour éviter PARTIE_A avant PARTIE_AB
    subs.sort(key=lambda x: -len(x[0]))
    for alt, original in subs:
        if alt in out:
            out = out.replace(alt, original)

    # Passe regex souple : PREFIX[_\\-\\s]+REST (insensible à la casse)
    for token, original in sorted(mapping.items(), key=lambda x: -len(x[0])):
        if "_" not in token:
            continue
        prefix, _, rest = token.partition("_")
        if not rest:
            continue
        pattern = re.compile(
            rf"\b{re.escape(prefix)}[\s_\-–—]+{re.escape(rest)}\b",
            re.IGNORECASE,
        )
        out = pattern.sub(original, out)

    return out


def party_tokens_legend(mapping: dict[str, str]) -> str:
    """Légende pour le prompt IA (sans révéler le vrai nom / PII)."""
    if not mapping:
        return ""
    lines = ["Légende anonymisation (ne pas inventer d'autres noms ni d'autres jetons) :"]
    for token in sorted(mapping.keys()):
        t = token.upper()
        if t.startswith("PARTIE"):
            lines.append(f"- {token} = une partie du dossier (identité masquée)")
        elif t.startswith("CIN"):
            lines.append(f"- {token} = numéro CIN/CNIE masqué")
        elif t.startswith("TEL"):
            lines.append(f"- {token} = numéro de téléphone masqué")
        elif t.startswith("EMAIL"):
            lines.append(f"- {token} = adresse e-mail masquée")
        else:
            lines.append(f"- {token} = donnée personnelle masquée")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Collecte de noms
# ---------------------------------------------------------------------------

_LATIN_NAME_RE = re.compile(
    r"\b(?:M\.|Mme|Mr|Mrs|Me|Dr)?\s*"
    r"([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][a-zàâäéèêëïîôùûüç'’-]+"
    r"(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][a-zàâäéèêëïîôùûüç'’-]+){1,3})\b"
)

_LATIN_STOP = {
    "tribunal",
    "cour",
    "Royaume",
    "Maroc",
    "Code",
    "Article",
    "Loi",
    "République",
    "Ministère",
}


def _extract_latin_names(text: str) -> list[str]:
    found: list[str] = []
    for m in _LATIN_NAME_RE.finditer(text or ""):
        name = _normalize_name(m.group(1))
        if len(name) < 5:
            continue
        first = name.split()[0]
        if first in _LATIN_STOP:
            continue
        found.append(name)
    return found


def collect_all_party_names(
    *,
    known_parties: list[str] | None = None,
    texts: list[str] | None = None,
    max_extra: int = 12,
) -> list[str]:
    """
    Fusion intelligente : noms fiche dossier + détection auto dans pièces/dictée.
    Ordre : known d'abord (PARTIE_A = client, PARTIE_B = adverse), puis extraits.
    """
    ordered: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        n = _normalize_name(name)
        if len(n) < 2:
            return
        key = n.lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(n)

    for n in known_parties or []:
        _add(n)

    blob = "\n".join(t for t in (texts or []) if t)
    if not blob.strip():
        return ordered

    extra: list[str] = []
    try:
        from app.services.dictation_contradictions import (
            _extract_bint_names,
            _extract_person_names,
        )

        extra.extend(_extract_person_names(blob))
        extra.extend(_extract_bint_names(blob))
    except Exception:
        pass
    extra.extend(_extract_latin_names(blob))

    extra_sorted = sorted(
        {_normalize_name(x) for x in extra if _normalize_name(x)},
        key=len,
        reverse=True,
    )
    added = 0
    for name in extra_sorted:
        if added >= max_extra:
            break
        before = len(ordered)
        _add(name)
        if len(ordered) > before:
            added += 1
    return ordered


# ---------------------------------------------------------------------------
# Corpus multi-textes
# ---------------------------------------------------------------------------


def mask_corpus(
    *texts: str,
    parties: list[str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """
    Masque plusieurs textes avec le même mapping (parties + PII structurée).

    Utilise `build_full_mask` pour un alphabet stable sur l'ensemble du corpus.
    Retourne (texts_masked, mapping).
    """
    text_list = [(t or "") for t in texts]
    if not any(text_list) and not parties:
        return text_list, {}

    # Alphabet stable : concaténation puis réapplication par texte
    joined = "\n\n".join(text_list)
    base = build_full_mask(joined, parties=parties, structured=True)
    mapping = base.mapping

    masked: list[str] = []
    running = dict(mapping)
    # Rejouer chaque texte avec le mapping déjà alloué (pas de nouveaux jetons
    # pour les mêmes valeurs ; build_full_mask réutilise base_mapping).
    for t in text_list:
        r = build_full_mask(
            t,
            parties=parties,
            structured=True,
            base_mapping=running,
        )
        masked.append(r.text)
        running = merge_mappings(running, r.mapping)

    return masked, running


# ---------------------------------------------------------------------------
# Helpers exportés pour tests / intégration
# ---------------------------------------------------------------------------


def list_token_kinds() -> tuple[str, ...]:
    """Kinds structurés supportés par detect_structured_hits."""
    return ("cin", "phone", "email")


__all__ = [
    "PiiMaskResult",
    "build_mask_from_parties",
    "mask_known_entities",
    "unmask_text",
    "party_tokens_legend",
    "collect_all_party_names",
    "mask_corpus",
    "detect_structured_hits",
    "mask_structured_pii",
    "build_full_mask",
    "merge_mappings",
    "inventory_summary",
    "list_token_kinds",
]
