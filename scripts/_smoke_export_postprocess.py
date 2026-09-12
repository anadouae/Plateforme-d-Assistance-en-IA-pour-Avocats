#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from app.services.plaidoirie_postprocess import postprocess_plaidoirie_body  # noqa: E402

SOURCE = (
    "إن المرافعة التي نحن بصدد إلقائها تخص جرائم التجارة بالمخدرات. "
    "نطلب من محكمتكم الموقرة أخذ حقوق كل الضحايا وبتشديد أقصى العقوبات."
)

BODY = """تحديد الأطراف
المتهم(ة) : (هنية بنت محمد)

أولاً : في الشكل
[يُستكمل]

ثانياً : في الوقائع
إن المرافعة التي نحن بصدد إلقائها تخص جرائم التجارة بالمخدرات.

ثالثاً : في المناقشة / الموضوع
[يُستكمل]

لهذه الأسباب :
الملتمسات :
1. تشديد أقصى العقوبات.
خاتمة قصيرة + تحفظات
واحسبكم على حسن استماعكم."""

out, warnings = postprocess_plaidoirie_body(
    BODY, source_text=SOURCE, plaidoirie_type="partie-civile", for_export=True
)

assert "[يُستكمل]" not in out, out
assert "خاتمة قصيرة" not in out, out
assert "حيث إن الدعوى" in out or "مقبولة" in out, out
assert "نطلب" in out or "أقصى" in out, out
assert "إن المرافعة" in out
print(out[:500])
print("warnings:", warnings)
print("ALL OK")
