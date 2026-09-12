#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from app.services.arabic_text_fix import (  # noqa: E402
    finalize_arabic_polish,
    light_arabic_fusha_form,
    light_arabic_punctuation,
    repair_arabic_stt,
    repair_stt_garbage,
    split_legal_phrases,
)


def collapse(s: str) -> str:
    return re.sub(r"(\S{3,})\s+\1(\s|$)", r"\1\2", s)


RAW = (
    "انا المربع التي نحن ان المرافعة التي نحن بصدد إلقائها، سيدي الرئيس، "
    "امامحكمتكم الموقرة تخص قضية من قضايا جرائم التجارة بالمخدرات والاتجار بالبشر، "
    "والتي تورطت فيها سيدة تدعى هنية بنت محمد والتي تقطن بضواحي مدينة الدار البيضاء "
    "تحديدا بحي أولاد الفقراء، وتتكون العصابة من أكثر من 10 سيدات وثلاثة رجال "
    "وضحايا هذه العصابة تتراوح اعمارهما بين 16 و 25 سنة ويستهدفون في اغلب الاحيان "
    "الثانويات والجامعات من اجل بيع المواد المخدرة واستقطاب فتيات وذكور من اجل الدعارة "
    "ولهذا، ولذلك، سيدي الرئيس، نطلب من محكمتكم الموقرة وكل فصولة نلتمس من محكمتكم "
    "الموقرة اخذ حقوق كل الضحايا وذلك بتشديد اقصى العقوبات على كل من ساهم في كل هذه "
    "الجرائم الملف الذي نحن بصددي معالجتة هو، ملف رقم 120، تاريخ الجلسة 16 يوليوز "
    "2026 2020 شكرا."
)


def polish(raw: str) -> str:
    t = collapse(raw.strip())
    for fn in (
        repair_stt_garbage,
        repair_arabic_stt,
        light_arabic_fusha_form,
        split_legal_phrases,
        light_arabic_punctuation,
        finalize_arabic_polish,
    ):
        t = fn(t)
    return t


def main() -> None:
    t = polish(RAW)
    print(t[:200])
    print("---")
    checks = [
        ("no double in", "إن إن" not in t[:40]),
        ("court space", "أمام محكمتكم" in t),
        ("ages", "أعمارهم" in t),
        ("file", "معالجته" in t),
        ("year dup", "2026 2020" not in t),
        ("start", t.startswith("إن المرافعة")),
    ]
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(name, "OK" if ok else "FAIL")
    if failed:
        sys.exit(1)
    print("ALL OK")


if __name__ == "__main__":
    main()
