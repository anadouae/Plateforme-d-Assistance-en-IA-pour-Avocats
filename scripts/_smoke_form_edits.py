# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from app.services.dictation import polish_dictation
from app.services.dictation_assist import build_form_edits

src = (
    "حيث إن المدعى عليها تقدمت بمذكراتها الجوابية "
    "واعتبرت أن الفصل كان سيباقتصاديا وطلبت رفض الطلب. "
    "باعتبار الذين دينا أجريا. شركة أطلس تكسيتيل ذ.م.م."
)
pol, prov = polish_dictation(src, language="ar", source="audio")
print("PROVIDER", prov)
print("POLISHED", pol)
print("MARKS", re.findall(r"‹([^›]+)›", pol))
assert "‹" not in pol
assert "سيباقتصاديا" not in pol
assert "سببا اقتصاديا" in pol
assert "بمذكراتهالجوابية" not in pol
assert "مذكراتها" in pol
edits = build_form_edits(src, pol)
print("EDITS", [(e.original, e.proposed) for e in edits])
# Texte déjà corrigé → panneau vide (pas de faux positifs)
assert edits == [], edits
print("OK")
