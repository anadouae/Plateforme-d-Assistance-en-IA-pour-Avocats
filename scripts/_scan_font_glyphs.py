from pathlib import Path
import pymupdf as fitz

assets = Path("backend/app/assets")
font = fitz.Font(fontfile=str(assets / "NotoNaskhArabic-Regular.ttf"))

symbols = []
for cp in range(0x0000, 0xFFFF):
    if font.has_glyph(cp):
        ch = chr(cp)
        cat = ""
        # Print non-alphanumeric
        if not (ch.isalnum() or '\u0621' <= ch <= '\u064A'):
            symbols.append((hex(cp), repr(ch)))

print("Total non-alpha glyphs in font:", len(symbols))
for s in symbols[:60]:
    print(s)
