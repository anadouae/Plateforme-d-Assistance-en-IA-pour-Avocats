# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\schemas\__init__.py")
t = p.read_text(encoding="utf-8")
needle = '    error_message: Optional[str] = None\n\n    class Config:\n        from_attributes = True\n\n\nclass DocumentDetailResponse'
insert = (
    "    error_message: Optional[str] = None\n"
    "    inventory_number: Optional[int] = None\n"
    "    exhibit_type: Optional[str] = None\n"
    "    produced_by: Optional[str] = None\n"
    "    exhibit_version: Optional[str] = None\n"
    "    cited_in_plea: Optional[str] = None\n\n"
    "    class Config:\n"
    "        from_attributes = True\n\n\n"
    "class DocumentDetailResponse"
)
if "inventory_number: Optional[int] = None\n    exhibit_type" in t.split("class DocumentResponse")[1].split("class DocumentDetail")[0]:
    print("already")
elif needle not in t:
    print("MISS needle")
else:
    t = t.replace(needle, insert, 1)
    tmp = p.with_suffix(".py.tmp2")
    tmp.write_text(t, encoding="utf-8")
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
    print("OK")
