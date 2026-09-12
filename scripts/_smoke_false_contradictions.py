#!/usr/bin/env python3
"""Smoke: false-positive contradictions + amount thousands parsing."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from app.services.dictation_contradictions import (  # noqa: E402
    _extract_amounts,
    _extract_case_numbers,
    _amount_key,
    detect_dictation_contradictions,
)

SAMPLE = """
السيد الرئيس، اشتغل موكلي، السيد يوسف العمراني، لمدة إحدى عشرة سنة، من 3 شتنبر 2013 إلى 17 يناير 2025،
بمنصب رئيس فريق في ورشة الصباغة بشركة أطلس تكستيل.
يوم الجمعة 17 يناير 2025، مُنع من ولوج الورشة. وبتاريخ 22 يناير 2025، وجّه إنذارا للشركة (إشعار 24 يناير 2025).
تلزم المادة 62 من القانون رقم 65.99. وقد أكدت محكمة النقض في قرار 12 ماي 2021 (ملف اجتماعي عدد 2245/5/1/2020).
كان يتقاضى أجرة شهرية قدرها 6800 درهم. التعويض: 6800 × 1.5 × 11 = 112,200 درهم
تعويض الإخطار ← 13,600 درهم. تعويض قانوني ← 20,604 درهم. عطلة ← 4,080 درهم.
ضرر معنوي ← 30,000 درهم. أي ما مجموعة 180,484 درهم. غرامة تهديدية قدرها 500 درهم.
في مذكرتها الجوابية المؤرخة في 5 مارس 2025. وفي مذكرتنا الكتابية المؤرخة في 10 مارس 2025.
"""


def test_amounts_no_fragments():
    amts = _extract_amounts(SAMPLE)
    keys = {_amount_key(a) for a in amts}
    print("amounts:", amts)
    for frag in ("200", "484", "080", "000", "604", "600"):
        assert frag not in keys, f"fragment {frag} leaked: {amts}"
    assert "180484" in keys
    assert "112200" in keys
    assert "20604" in keys
    assert "4080" in keys
    assert "30000" in keys
    assert "6800" in keys


def test_no_false_case_numbers():
    cases = _extract_case_numbers(SAMPLE)
    print("cases:", cases)
    joined = " ".join(cases)
    assert "2245" not in joined
    assert "65" not in joined
    assert "1/2020" not in joined


def test_no_false_contradictions():
    alerts = detect_dictation_contradictions(SAMPLE, source=SAMPLE)
    kinds = [a.kind for a in alerts]
    print("alerts:", [(a.kind, a.values) for a in alerts])
    assert "case_number" not in kinds
    assert "date" not in kinds
    assert "amount" not in kinds


def test_memo_dates_not_conflict():
    alerts = detect_dictation_contradictions(SAMPLE, source=SAMPLE)
    date_alerts = [a for a in alerts if a.kind == "date"]
    assert not date_alerts, f"false memo conflict: {[a.values for a in date_alerts]}"


def test_real_amount_conflict():
    text = "أجرة شهرية قدرها 6800 درهم. ويتقاضى أجرة شهرية بمبلغ 7200 درهم."
    alerts = detect_dictation_contradictions(text, source=text)
    amts = [a for a in alerts if a.kind == "amount"]
    assert amts, "expected salary conflict"
    print("real conflict OK:", amts[0].values)


if __name__ == "__main__":
    test_amounts_no_fragments()
    test_no_false_case_numbers()
    test_no_false_contradictions()
    test_memo_dates_not_conflict()
    test_real_amount_conflict()
    print("ALL OK")
