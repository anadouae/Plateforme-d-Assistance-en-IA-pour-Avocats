"""Validation magic-bytes des uploads (ne pas se fier à l'extension seule)."""

from __future__ import annotations

# Signatures minimales
_PDF = b"%PDF"
_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"
_TIFF_LE = b"II*\x00"
_TIFF_BE = b"MM\x00*"
# DOCX = ZIP container
_ZIP = b"PK\x03\x04"


def sniff_allowed_upload(content: bytes, ext: str) -> str | None:
    """
    Retourne un message d'erreur si le contenu ne correspond pas à l'extension,
    sinon None.
    """
    if not content or len(content) < 4:
        return "Fichier vide ou invalide."

    head = content[:16]
    ext = ext.lower()

    if ext == ".pdf":
        if not content.lstrip().startswith(_PDF):
            return "Le fichier n'est pas un PDF valide."
        return None

    if ext == ".png":
        if not head.startswith(_PNG):
            return "Le fichier n'est pas une image PNG valide."
        return None

    if ext in {".jpg", ".jpeg"}:
        if not head.startswith(_JPEG):
            return "Le fichier n'est pas une image JPEG valide."
        return None

    if ext in {".tif", ".tiff"}:
        if not (head.startswith(_TIFF_LE) or head.startswith(_TIFF_BE)):
            return "Le fichier n'est pas une image TIFF valide."
        return None

    if ext == ".docx":
        if not head.startswith(_ZIP):
            return "Le fichier n'est pas un DOCX valide."
        # DOCX doit contenir le marqueur Office Open XML
        if b"word/" not in content[:8192] and b"[Content_Types].xml" not in content[:8192]:
            # ZIP générique sans marqueurs Office — rejeter
            if b"word/" not in content and b"[Content_Types].xml" not in content:
                return "Le fichier ZIP n'est pas un document DOCX."
        return None

    return "Type de fichier non autorisé."
