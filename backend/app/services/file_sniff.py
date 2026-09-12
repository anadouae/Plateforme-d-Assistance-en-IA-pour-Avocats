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
# Audio
_RIFF = b"RIFF"
_WAVE = b"WAVE"
_OGG = b"OggS"
_ID3 = b"ID3"
_EBML = b"\x1a\x45\xdf\xa3"  # WebM / Matroska
_FTIP = b"ftyp"


def _is_mp3_frame(head: bytes) -> bool:
    """Syncword MPEG audio (FF Ex / FF Fx) sans tag ID3."""
    if len(head) < 2:
        return False
    return head[0] == 0xFF and (head[1] & 0xE0) == 0xE0


def _is_mp4_family(content: bytes) -> bool:
    """ISO BMFF (m4a / mp4) : ....ftyp...."""
    if len(content) < 12:
        return False
    return content[4:8] == _FTIP


def sniff_allowed_upload(content: bytes, ext: str) -> str | None:
    """
    Retourne un message d'erreur si le contenu ne correspond pas à l'extension,
    sinon None.
    """
    ext = (ext or "").lower()
    if not content:
        return "Fichier vide ou invalide."

    # TXT / Markdown : accepter même un court fichier ; UTF-16 OK
    if ext in {".txt", ".md", ".markdown"}:
        sample = content[:8192]
        nulls = sample.count(b"\x00")
        if nulls > 2:
            for enc in ("utf-16", "utf-16-le", "utf-16-be"):
                try:
                    sample.decode(enc)
                    return None
                except UnicodeDecodeError:
                    continue
            if nulls > max(8, len(sample) // 3):
                return "Le fichier texte semble binaire."
        return None

    if len(content) < 4:
        return "Fichier vide ou invalide."

    head = content[:16]

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

    if ext == ".wav":
        if not (head.startswith(_RIFF) and content[8:12] == _WAVE):
            return "Le fichier n'est pas un WAV valide."
        return None

    if ext == ".ogg":
        if not head.startswith(_OGG):
            return "Le fichier n'est pas un OGG valide."
        return None

    if ext == ".webm":
        if not head.startswith(_EBML):
            return "Le fichier n'est pas un WebM valide."
        return None

    if ext in {".mp3", ".mpeg", ".mpga"}:
        if not (head.startswith(_ID3) or _is_mp3_frame(head)):
            return "Le fichier n'est pas un MP3 valide."
        return None

    if ext in {".m4a", ".mp4"}:
        if not _is_mp4_family(content):
            return "Le fichier n'est pas un M4A/MP4 valide."
        return None

    return "Type de fichier non autorisé."
