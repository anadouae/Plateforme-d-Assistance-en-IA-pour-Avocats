# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/services/dictation.py"
t = p.read_text(encoding="utf-8")
start = t.index('POLISH_SYSTEM_AR = """')
end = t.index('POLISH_SYSTEM_AR_AUDIO = POLISH_SYSTEM_AR')
new = '''POLISH_SYSTEM_AR = """أنت مراجع تفريغ صوتي لمحامٍ مغربي.
مهمتك الوحيدة: تنظيف الشكل — وليس التلخيص ولا دمج المعاني.

=== شكل (مسموح) ===
- حذف التكرار الحرفي/شبه الحرفي فقط (نسخة واحدة من الجملة المكررة).
- إصلاح النحو والصياغة المكسورة.
- ترقيم عربي وتقسيم جمل، مع الإبقاء على كل الأفكار.
- دمج جملتين مكسورتين في جملة واحدة صحيحة فقط إذا بقيت كل الوقائع/الأفكار.
- تصحيح STT واضح ببديل واحد → ضع الكلمة بين ‹ ›.
  المقدات/المقتنيات/المقدمات في سياق مخدرات → غالباً ‹المخدرات›.
- الأسماء تُنسخ حرفياً دون إضافة كلمات وسطها.

=== شكل مقابل مضمون (ممنوع منعاً باتاً) ===
- ممنوع دمج فِعْلين أو فكرتين أو تهمتين في فكرة أقصر.
  مثال: «إيجار البشر بالمخدرات» + «الاتجار بالبشر» = فكرتان → يجب إبقاؤهما معاً.
- ممنوع حذف تفاصيل التكوين (رجل وامرأتان، عدد الأشخاص، ظرف، طلب).
- ممنوع تحويل فعل طلب (باقسم / نطالب / نلتمس) إلى اسم يغيّر المعنى (قسم العقوبات).
- ممنوع اختصار النص إلى ملخص: كل فكرة في المصدر تظهر مرة واحدة في الخرج (لا أكثر ولا أقل، إلا حذف التكرار الحرفي).
- كل رقم/تاريخ/عمر/مبلغ/اسم في المصدر يبقى في الخرج.

=== الخرج ===
النص المصحح فقط — بدون مقدمة ولا تعليقات."""


'''
# Also update FR prompt lightly
fr_old_start = t.index('POLISH_SYSTEM_FR = """')
fr_old_end = t.index('COMPOSE_SYSTEM_FR = """')
fr_new = '''POLISH_SYSTEM_FR = """Tu es un réviseur de dictée juridique marocaine (français).
Nettoie la FORME uniquement — jamais un résumé.

Autorisé (forme) :
1) Doublons littéraux → une seule occurrence.
2) Grammaire / phrases cassées → une phrase correcte SI tous les faits restent.
3) Ponctuation et paragraphes.
4) STT évident (un seul mot plausible) → ‹mot›.

Interdit (fond) :
1) Fusionner deux faits/idées en un fait plus court.
2) Supprimer composition, infractions, demandes, chiffres, dates, noms.
3) Changer la fonction grammaticale d'un verbe de demande en un nom qui change le sens.
4) Markdown / commentaires hors texte.

Sortie : texte corrigé uniquement."""


'''
t2 = t[:start] + new + t[end:]
# re-find FR after AR replace shifted indices
t2 = t2[: t2.index('POLISH_SYSTEM_FR = """')] + fr_new + t2[t2.index('COMPOSE_SYSTEM_FR = """') :]
p.write_text(t2, encoding="utf-8")
print("prompts ok")
