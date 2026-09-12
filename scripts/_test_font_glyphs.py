from pathlib import Path
import pymupdf as fitz

assets = Path("backend/app/assets")
font_reg = assets / "NotoNaskhArabic-Regular.ttf"

doc = fitz.open()
page = doc.new_page()

# Let's check what glyphs are in NotoNaskhArabic
font = fitz.Font(fontfile=str(font_reg))
test_chars = ["—", "–", "-", "•", "▪", "[", "]", "2)", "(", ")", "،", "\u200F", "\u200E"]
for ch in test_chars:
    glyph = font.has_glyph(ord(ch))
    print(f"Char {repr(ch)} (U+{ord(ch):04X}): has_glyph = {glyph}")
