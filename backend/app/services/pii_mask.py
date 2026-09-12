"""Anonymisation PII avant envoi LLM — mapping local, démasquage après réponse.

Principe cabinet : les vrais noms (client, adverse) ne partent jamais vers l'IA.
Ils sont remplacés par PARTIE_A, PARTIE_B… puis restaurés dans le document final.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PiiMaskResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # token -> original

    def unmask(self, text: str) -> str:
        return unmask_text(text, self.mapping)


def _normalize_name(name: str) -> str:
    return " ".join((name or "").strip().split())


def _name_variants(name: str) -> list[str]:
    """Variantes d'écriture pour mieux attraper le nom dans dictée / pièces."""
    n = _normalize_name(name)
    if not n or len(n) < 2:
        return []
    out = [n]
    parts = n.split()
    if len(parts) >= 2:
        out.append(" ".join(reversed(parts)))
        # Nom de famille seul si suffisamment distinctif
        last = parts[-1]
        if len(last) >= 4:
            out.append(last)
        first = parts[0]
        if len(first) >= 4 and first.lower() not in {
            "mohamed",
            "mohammed",
            "ahmed",
            "fatima",
            "hassan",
            "said",
            "saïd",
            "youssef",
            "omar",
        }:
            out.append(first)
    # Déduplique en gardant l'ordre (plus long d'abord plus tard)
    seen: set[str] = set()
    uniq: list[str] = []
    for v in out:
        k = v.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return uniq


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
    # Plus longs d'abord pour éviter les sous-chaînes
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
            # Variantes → même jeton
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


def unmask_text(text: str, mapping: dict[str, str]) -> str:
    """Restaure les vrais noms. Tolère PARTIE-A / PARTIE A / partie_a."""
    out = text or ""
    if not mapping:
        return out
    for token, original in sorted(mapping.items(), key=lambda x: -len(x[0])):
        out = out.replace(token, original)
        # Variantes de jeton que le LLM peut produire
        letter = token.replace("PARTIE_", "").strip()
        if letter:
            for alt in (
                f"PARTIE-{letter}",
                f"PARTIE {letter}",
                f"Partie_{letter}",
                f"Partie {letter}",
                f"partie_{letter.lower()}",
                f"partie {letter.lower()}",
            ):
                out = out.replace(alt, original)
    return out


def party_tokens_legend(mapping: dict[str, str]) -> str:
    """Légende pour le prompt IA (sans révéler le vrai nom)."""
    if not mapping:
        return ""
    lines = ["Légende anonymisation (ne pas inventer d'autres noms) :"]
    for token in sorted(mapping.keys()):
        lines.append(f"- {token} = une partie du dossier (identité masquée)")
    return "\n".join(lines)


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

    # Plus longs d'abord, plafond pour éviter le bruit
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


def mask_corpus(
    *texts: str,
    parties: list[str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Masque plusieurs textes avec le même mapping. Retourne (texts_masked, mapping)."""
    parties = parties or []
    if not parties:
        return list(texts), {}
    # Construire le mapping sur la concaténation pour un alphabet stable
    joined = "\n\n".join(texts)
    base = build_mask_from_parties(joined, parties=parties)
    mapping = base.mapping
    masked = [build_mask_from_parties(t or "", parties=parties).text for t in texts]
    # Fusionner mapping (même tokens)
    return masked, mapping
