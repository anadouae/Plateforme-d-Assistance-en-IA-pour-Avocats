from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\dictation.py")
t = p.read_text(encoding="utf-8")
old = """        _, completeness = compose_completeness_check(source_text, body_out)
        checks = section_warnings + completeness
        title_out = hint_title or \"مرافعة\""""
new = """        _, completeness = compose_completeness_check(source_text, body_out)
        type_label = PLAIDOIRIE_TYPES.get(type_id, type_id)
        checks = [
            f\"نوع المرافعة المعتمد: {type_label} ({type_id})\",
        ] + section_warnings + completeness
        title_out = hint_title or \"مرافعة\""""
if old not in t:
    raise SystemExit("checks block not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("dictation type check ok")
