from pathlib import Path
import pymupdf as fitz

assets = Path("backend/app/assets")
font_reg = assets / "NotoNaskhArabic-Regular.ttf"
font = fitz.Font(fontfile=str(font_reg))

sample_chars = [
    "ا", "ب", "ت", "0", "1", "2", "٩", "١", 
    "-", "–", "—", "•", "▪", "[", "]", "(", ")", 
    "،", "؛", ":", ".", "؟", "!", "«", "»", " ", "\n"
]
for ch in sample_chars:
    if len(ch) == 1:
        print(f"Char {repr(ch)} (U+{ord(ch):04X}): glyph = {font.has_glyph(ord(ch))}")
