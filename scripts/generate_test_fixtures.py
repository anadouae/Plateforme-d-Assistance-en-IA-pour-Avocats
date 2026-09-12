"""Génère des fichiers de test PDF + WAV pour upload Sanad."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)


def write_minimal_pdf(path: Path) -> None:
    # PDF minimal avec texte FR/AR (couche texte native — pas besoin OCR)
    text_lines = [
        "SANAD — Document de test",
        "Dossier: TEST-2026-001",
        "Parties: Société Atlas SARL / M. Karim Benali",
        "Date: 12/08/2026",
        "Montant: 25 000 MAD",
        "Objet: Contrat de prestation de services juridiques.",
        "Clause: En cas de résiliation, une pénalité de 10% s'applique.",
        "",
        "وثيقة اختبار — سند",
        "الأطراف: شركة أطلس / السيد كريم بنعلي",
        "المبلغ: 25000 درهم",
    ]
    # Escape for PDF literal strings (Latin-1 safe subset + drop Arabic for raw PDF simplicity)
    # Keep Arabic in a second content stream as UTF-16BE hex for better extraction
    content_fr = "\\n".join(text_lines[:7])
    # Simple PDF with Helvetica
    objects = []

    def add(obj: str) -> int:
        objects.append(obj)
        return len(objects)

    add("<< /Type /Catalog /Pages 2 0 R >>")
    add("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    add(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    # Text drawing
    y = 800
    stream_parts = ["BT", "/F1 12 Tf", "50 800 Td", "14 TL"]
    for i, line in enumerate(
        [
            "SANAD - Document de test",
            "Dossier: TEST-2026-001",
            "Parties: Societe Atlas SARL / M. Karim Benali",
            "Date: 12/08/2026",
            "Montant: 25000 MAD",
            "Objet: Contrat de prestation de services juridiques.",
            "Clause: En cas de resiliation, penalite de 10%.",
            "Document de test pour upload Sanad.",
        ]
    ):
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_parts.append(f"({safe}) Tj")
        else:
            stream_parts.append(f"T* ({safe}) Tj")
    stream_parts.append("ET")
    stream = "\n".join(stream_parts).encode("latin-1")
    add(f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1").decode("latin-1") + stream.decode("latin-1") + "\nendstream")
    # Fix object 4 properly as bytes assembly below instead
    objects[3] = None  # placeholder rewritten

    # Rebuild cleanly with bytes
    body_parts: list[bytes] = []
    offsets = [0]

    def obj_bytes(n: int, payload: bytes) -> bytes:
        return f"{n} 0 obj\n".encode() + payload + b"\nendobj\n"

    font = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
    pages = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    content_stream = (
        b"BT /F1 12 Tf 50 780 Td 16 TL "
        b"(SANAD - Document de test) Tj T* "
        b"(Dossier: TEST-2026-001) Tj T* "
        b"(Parties: Societe Atlas SARL / Karim Benali) Tj T* "
        b"(Date: 12/08/2026) Tj T* "
        b"(Montant: 25000 MAD) Tj T* "
        b"(Objet: Contrat de prestation juridique.) Tj T* "
        b"(Clause: resiliation - penalite 10 pct.) Tj T* "
        b"(Fichier de test pour upload Sanad.) Tj "
        b"ET"
    )
    contents = f"<< /Length {len(content_stream)} >>\nstream\n".encode() + content_stream + b"\nendstream"

    objs = [catalog, pages, page, contents, font]
    out = bytearray(b"%PDF-1.4\n")
    xref_positions = [0]
    for i, payload in enumerate(objs, start=1):
        xref_positions.append(len(out))
        out.extend(obj_bytes(i, payload))
    xref_start = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for pos in xref_positions[1:]:
        out.extend(f"{pos:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    )
    path.write_bytes(bytes(out))


def write_wav(path: Path, seconds: float = 3.0, freq: float = 440.0) -> None:
    """WAV court (bip) — pour tester upload audio. Whisper peut rendre peu de texte."""
    rate = 16000
    n = int(rate * seconds)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            # enveloppe douce + silence entre tons pour VAD
            t = i / rate
            env = 0.35 if (int(t * 2) % 2 == 0) else 0.0
            sample = int(env * 32767 * math.sin(2 * math.pi * freq * t))
            frames.extend(struct.pack("<h", sample))
        w.writeframes(frames)


def write_arabic_wav_placeholder_note(path: Path) -> None:
    path.write_text(
        "Pour un vrai test Whisper arabe, enregistre 5–10 s au micro "
        "(plaidoirie) ou utilise un .mp3/.m4a avec de la parole arabe.\n"
        "Le fichier sanad-test-audio.wav sert surtout à valider l'upload + stockage.\n",
        encoding="utf-8",
    )


def main() -> None:
    pdf = OUT / "sanad-test-document.pdf"
    wav = OUT / "sanad-test-audio.wav"
    note = OUT / "README-fixtures.txt"
    write_minimal_pdf(pdf)
    write_wav(wav, seconds=4.0)
    write_arabic_wav_placeholder_note(note)
    print(f"PDF: {pdf} ({pdf.stat().st_size} bytes)")
    print(f"WAV: {wav} ({wav.stat().st_size} bytes)")
    print(f"NOTE: {note}")


if __name__ == "__main__":
    main()
