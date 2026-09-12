# -*- coding: utf-8 -*-
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
rel = "backend/app/services/arabic_text_fix.py"
with open(rel, encoding="utf-8") as f:
    t = f.read()
needle = '(r"(?<!\\S)ايجار(?=\\s)", "إيجار"),'
extra = (
    '(r"(?<!\\S)ايجار(?=\\s)", "إيجار"),\n'
    '        (r"وامر[اأ]تين", "وامرأتان"),\n'
    '        (r"(?<!\\S)اعمارهم(?=\\s)", "أعمارهم"),'
)
if "وامرأتان" not in t and needle in t:
    t = t.replace(needle, extra, 1)
    with open(rel, "w", encoding="utf-8") as f:
        f.write(t)
    print("patched")
else:
    print("skip", "وامرأتان" in t, needle in t)
