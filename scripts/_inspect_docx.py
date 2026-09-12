# -*- coding: utf-8 -*-
import re
import sys
import zipfile
from pathlib import Path

p = Path(sys.argv[1])
with zipfile.ZipFile(p) as z:
    xml = z.read("word/document.xml").decode("utf-8")

m = re.search(r"<w:tbl>.*?</w:tbl>", xml, re.DOTALL)
if m:
    t = m.group(0)
    print("TABLE LEN", len(t))
    for tag in ("bidiVisual", "tblW", "jc", "bidi"):
        print(tag, t.count(tag))
    print(t[:3000])

print("--- paragraphs ---")
for i, pm in enumerate(re.finditer(r"<w:p[ >].*?</w:p>", xml, re.DOTALL)):
    if i > 8:
        break
    text = re.sub(r"<[^>]+>", "", pm.group(0)).strip()[:90]
    jc_m = re.search(r'w:jc[^/]*w:val="([^"]+)"', pm.group(0))
    has_bidi = bool(re.search(r"<w:bidi(?:/>|[^>]*>)", pm.group(0)))
    print(i, "jc=", jc_m.group(1) if jc_m else "-", "bidi=", has_bidi, text)
