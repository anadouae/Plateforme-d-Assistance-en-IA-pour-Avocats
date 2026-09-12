# -*- coding: utf-8 -*-
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
rel = "backend/app/services/arabic_text_fix.py"
with open(rel, encoding="utf-8") as f:
    text = f.read()

cut_at = text.find("def light_arabic_punctuation")
if cut_at < 0:
    cut_at = text.find("def light_arabic_fusha_form")
if cut_at < 0:
    raise SystemExit("no cut point: " + str(text.find("def light_")))

head = text[:cut_at].rstrip() + "\n\n"

# Write via a separate data file to avoid escape hell
data_path = "scripts/_fusha_tail.py.txt"
with open(data_path, "w", encoding="utf-8") as f:
    f.write(
        "def light_arabic_punctuation(text: str) -> str:\n"
        '    """Ajoute une ponctuation légère (، .) sans changer les mots."""\n'
        "    t = (text or \"\").strip()\n"
        "    if not t:\n"
        '        return ""\n'
        '    t = re.sub(r"\\s+", " ", t)\n'
        '    t = re.sub(r"\\s*([،؛:])\\s*", r"\\1 ", t)\n'
        '    t = re.sub(r"\\s+([.!?؟])\\s*", r"\\1 ", t)\n'
        "    connectors = (\n"
        '        "وحيث", "حيث", "لذلك", "وعليه", "وبناء عليه", "وبناءً عليه",\n'
        '        "أولا", "ثانيا", "ثالثا", "لهذه الأسباب",\n'
        "    )\n"
        "    for c in connectors:\n"
        '        t = re.sub(rf"({re.escape(c)})(?![،:])\\s+", rf"\\1، ", t)\n'
        '    if len(t) > 40 and t[-1] not in ".!?؟۔":\n'
        '        t = t.rstrip(" ،,") + "."\n'
        '    return re.sub(r"\\s{2,}", " ", t).strip()\n'
        "\n"
        "\n"
        "def light_arabic_fusha_form(text: str) -> str:\n"
        '    """Corrections de FORME fusḥā — sans résumer ni supprimer de faits."""\n'
        "    t = (text or \"\").strip()\n"
        "    if not t:\n"
        '        return ""\n'
        '    t = re.sub(r"\\s+", " ", t)\n'
        "    replacements = [\n"
        '        (r"(?<!\\S)ان(?=\\s)", "إن"),\n'
        '        (r"(?<=[.。؟!\\n،])\\s*ان(?=\\s)", "إن"),\n'
        '        (r"(?<!\\S)الى(?=\\s|[.،]|$)", "إلى"),\n'
        '        (r"القائها", "إلقائها"),\n'
        '        (r"القاءها", "إلقاءها"),\n'
        '        (r"القاء(?=\\s)", "إلقاء"),\n'
        '        (r"(?<!\\S)الاشخاص(?=\\s|[.،]|$)", "الأشخاص"),\n'
        '        (r"(?<!\\S)اشخاص(?=\\s|[.،]|$)", "أشخاص"),\n'
        '        (r"(?<!\\S)الاولى(?=\\s)", "الأولى"),\n'
        '        (r"(?<!\\S)اخر(?=\\s)", "آخر"),\n'
        '        (r"(?<!\\S)اخرين(?=\\s)", "آخرين"),\n'
        '        (r"(?<!\\S)ايضا(?=\\s|[.،]|$)", "أيضاً"),\n'
        '        (r"(?<!\\S)ايضاً(?=\\s|[.،]|$)", "أيضاً"),\n'
        '        (r"والتي تورط (?!فيها)", "والتي تورط فيها "),\n'
        '        (r"والتي تورطت (?!فيها)", "والتي تورطت فيها "),\n'
        '        (r"باقسم (?=العقوبات)", "نطالب بأقصى "),\n'
        '        (r"(?<!\\S)ايجار(?=\\s)", "إيجار"),\n'
        '        (r"سيدي الرئيس(?![،,])", "سيدي الرئيس،"),\n'
        "    ]\n"
        "    for pat, repl in replacements:\n"
        "        t = re.sub(pat, repl, t)\n"
        '    for marker in ("ملف رقم", "وتاريخ الجلسة", "تاريخ الجلسة", "ولذلك", "وعليه"):\n'
        '        t = re.sub(rf"(?<![،.\\n])\\s+({re.escape(marker)})", rf"، \\1", t)\n'
        '    t = re.sub(r"،\\s*،+", "،", t)\n'
        '    t = re.sub(r"\\s{2,}", " ", t).strip()\n'
        '    if len(t) > 40 and t[-1] not in ".!?؟۔":\n'
        '        t = t.rstrip(" ،,") + "."\n'
        "    return t\n"
    )

with open(data_path, encoding="utf-8") as f:
    tail = f.read()

with open(rel, "w", encoding="utf-8") as f:
    f.write(head + tail)

import importlib.util
spec = importlib.util.spec_from_file_location("atf", rel)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sample = (
    "ان المرافعة التي نحن بصدد القائها سيدي الرئيس تخص قضية "
    "والتي تورط الاشخاص ان الملف ملف رقم 180 وتاريخ الجلسة 18 يوليوز 2023"
)
out = mod.light_arabic_fusha_form(sample)
assert "إن المرافعة" in out, out
assert "إلقائها" in out, out
assert "الأشخاص" in out, out
assert hasattr(mod, "light_arabic_punctuation")
print("LOCAL_OK")
print(out)
