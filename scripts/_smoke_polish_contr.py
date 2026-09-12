# -*- coding: utf-8 -*-
"""Smoke: preserve facts + annotate guesses + contradictions union."""
import sys
from pathlib import Path

for p in ("/app", "/opt/sanad/backend"):
    if Path(p).is_dir() and p not in sys.path:
        sys.path.insert(0, p)

from app.services.dictation_contradictions import (
    annotate_stt_guesses,
    detect_dictation_contradictions,
    preserve_source_facts,
)

source = (
    "في ملف رقم 45 على 12 ثم ملف رقم 210 والمتهم يتعلق بالمقد ات "
    "والجلسة 18 من شهر اغسطس 2023 2026"
)
# Simule un LLM qui droppe 45/12 et invente « بيع المقتنيات »
fake_llm = "في ملف رقم 210 والمتهم يتعلق ببيع المقتنيات والجلسة 18 من شهر اغسطس 2023 2026"

marked, guessed = annotate_stt_guesses(source, fake_llm)
print("guessed:", guessed)
assert "‹" in marked
assert any("بيع" in g or "مقتنيات" in g or "المقتنيات" in g for g in guessed) or "‹بيع" in marked or "‹المقتنيات" in marked, (guessed, marked)

restored = preserve_source_facts(source, marked)
print("restored:", restored)
assert "45" in restored and ("12" in restored or "على" in restored), restored
# Ne pas marquer la clause d'append
assert "‹أسماء›" not in restored and "‹مذكورة›" not in restored, restored

alerts = detect_dictation_contradictions(restored, source=source)
kinds = {a.kind: a.values for a in alerts}
print("alerts:", kinds)
assert "case_number" in kinds and len(kinds["case_number"]) >= 2, kinds
assert "date" in kinds, kinds
print("SMOKE_OK")
