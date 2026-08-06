"""Politique de mot de passe (inscription / reset)."""

from __future__ import annotations

import re

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")

# Hash bcrypt valide (mot de passe factice) — égalise le temps si l'email n'existe pas.
DUMMY_PASSWORD_HASH = (
    "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
)

MIN_PASSWORD_LENGTH = 12


def validate_password_strength(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        )
    if len(password) > 72:
        raise ValueError("Le mot de passe ne peut pas dépasser 72 caractères.")
    if not _UPPER.search(password):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
    if not _LOWER.search(password):
        raise ValueError("Le mot de passe doit contenir au moins une minuscule.")
    if not _DIGIT.search(password):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
    if not _SPECIAL.search(password):
        raise ValueError("Le mot de passe doit contenir au moins un symbole.")
    return password
