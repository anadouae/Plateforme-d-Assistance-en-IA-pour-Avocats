from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\billing.py")
t = p.read_text(encoding="utf-8")
if "import html" not in t:
    t = t.replace(
        "from __future__ import annotations\n\nimport json",
        "from __future__ import annotations\n\nimport html\nimport json",
    )
needle = '    html = f"""<!DOCTYPE html>'
if "safe_name = html.escape" not in t and needle in t:
    t = t.replace(
        needle,
        "    safe_name = html.escape(cabinet_name or \"\")\n"
        "    safe_addr = html.escape(address or \"\")\n"
        "    safe_city = html.escape(city or \"\")\n"
        "    safe_plan = html.escape(plan.name or \"\")\n"
        + needle,
    )
    t = t.replace(
        "{cabinet_name}<br/>{address}<br/>{city}",
        "{safe_name}<br/>{safe_addr}<br/>{safe_city}",
    )
    t = t.replace("Abonnement {plan.name}", "Abonnement {safe_plan}")
p.write_text(t, encoding="utf-8")
print("ok")
