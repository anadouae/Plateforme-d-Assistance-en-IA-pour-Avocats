# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\schemas\__init__.py")
t = p.read_text(encoding="utf-8")
old = '    phone: str = Field(..., min_length=8, max_length=30)'
new = '    phone: Optional[str] = Field(None, max_length=30)'
if old not in t:
    print("MISS phone field")
else:
    t = t.replace(old, new, 1)

old_v = '''    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        cleaned = "".join(c for c in v.strip() if c.isdigit() or c in "+ ")
        if len(cleaned.replace(" ", "").replace("+", "")) < 8:
            raise ValueError("Numéro de téléphone invalide.")
        return cleaned.strip()
'''
new_v = '''    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        cleaned = "".join(c for c in str(v).strip() if c.isdigit() or c in "+ ")
        digits = cleaned.replace(" ", "").replace("+", "")
        if digits and len(digits) < 8:
            raise ValueError("Numéro de téléphone invalide.")
        return cleaned.strip() or None
'''
if old_v not in t:
    print("MISS validator")
else:
    t = t.replace(old_v, new_v, 1)
    print("validator OK")

tmp = p.with_suffix(".py.wtmp")
tmp.write_text(t, encoding="utf-8")
p.write_bytes(tmp.read_bytes())
tmp.unlink(missing_ok=True)
print("done")
