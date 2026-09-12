# -*- coding: utf-8 -*-
"""Kit dossier commercial complet (AR) — test plaidoirie LexHub / ChatGPT compose."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)


def save_doc(name: str, title: str, paragraphs: list[str]) -> None:
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)
        s.left_margin = Cm(2)
        s.right_margin = Cm(2)
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(title)
    r.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(0x0A, 0x12, 0x28)
    for p in paragraphs:
        para = doc.add_paragraph(p)
        for run in para.runs:
            run.font.size = Pt(11)
    path = OUT / name
    doc.save(path)
    print("OK", path.name)


def main() -> None:
    # --- Pièces ---
    save_doc(
        "01_contrat_fourniture_Layla_Ihsan.docx",
        "عقد توريد وتوزيع — وثيقة اختبار LexHub",
        [
            "المملكة المغربية — الدار البيضاء",
            "عقد رقم CT-2024/088 مؤرخ في 12 مارس 2024",
            "الطرف الأول (المورّد / المدعية): السيدة ليلى بنعمر، مغربية، مزدادة بتاريخ 08/05/1987 بالدار البيضاء، "
            "حاملة للبطاقة الوطنية رقم BK445566، القاطنة بحي المعاريف، زنقة 12، رقم 45، الدار البيضاء. "
            "تمارس نشاط توزيع مواد غذائية تحت اسم تجاري «ليلى فود».",
            "الطرف الثاني (الموزّع / المدعى عليه): السيد إحسان التازي، مغربي، مزداد بتاريخ 21/11/1984 بمراكش، "
            "حامل للبطاقة الوطنية رقم CD778899، القاطن بحي الفداء، الدار البيضاء. "
            "يملك محل «إحسان ماركت» الكائن بشارع الزرقطوني رقم 210.",
            "موضوع العقد: توريد شهري لمواد غذائية جافة ومعلبات بقيمة تقديرية شهرية ثمانون ألف درهم (80.000 درهم)، "
            "على أن يتم الأداء خلال أجل ثلاثين (30) يوماً من تاريخ كل فاتورة.",
            "مدة العقد: سنة واحدة قابلة للتجديد ضمنياً، ابتداءً من 01 أبريل 2024.",
            "شرط جزائي: في حالة التأخر عن الأداء لمدة تفوق خمسة عشر يوماً بعد الأجل، يستحق الطرف الأول تعويضاً "
            "جزافياً قدره خمسة آلاف درهم (5.000 درهم) عن كل شهر تأخير، دون الإخلال بالمطالبة بالدين الأصلي والفوائد.",
            "الاختصاص: المحكمة التجارية بالدار البيضاء.",
            "ملاحظة: وثيقة وهمية لاختبار LexHub فقط — ليست عقداً رسمياً.",
        ],
    )

    save_doc(
        "02_factures_Layla.docx",
        "فواتير مستحقة — ليلى بنعمر ضد إحسان التازي",
        [
            "فاتورة رقم F-2024/210 بتاريخ 05 أكتوبر 2024 — مبلغ 82.450 درهم — أجل الأداء: 04 نونبر 2024.",
            "فاتورة رقم F-2024/241 بتاريخ 02 نونبر 2024 — مبلغ 79.800 درهم — أجل الأداء: 02 دجنبر 2024.",
            "فاتورة رقم F-2024/268 بتاريخ 28 نونبر 2024 — مبلغ 85.200 درهم — أجل الأداء: 28 دجنبر 2024.",
            "المجموع غير المؤدى: مائتان وسبعة وأربعون ألفاً وأربعمائة وخمسون درهماً (247.450 درهم).",
            "لم يسجل أي أداء جزئي بعد تاريخ 15 شتنبر 2024.",
            "ملاحظة: وثائق اختبار LexHub.",
        ],
    )

    save_doc(
        "03_mise_en_demeure.docx",
        "إنذار رسمي بالأداء — عبر مفوض قضائي",
        [
            "بتاريخ 15 يناير 2025، وجهت السيدة ليلى بنعمر إنذاراً رسمياً بواسطة المفوض القضائي السيد رشيد العلمي "
            "(مكتب الدار البيضاء) إلى السيد إحسان التازي بمقر محله التجاري.",
            "مضمون الإنذار: أداء مبلغ 247.450 درهم داخل أجل ثمانية (8) أيام، تحت طائلة اللجوء إلى القضاء "
            "والمطالبة بالتعويض والشرط الجزائي والصائر.",
            "تم تبليغ الإنذار بتاريخ 16 يناير 2025 حسب شهادة التسليم المرفقة.",
            "انقضى الأجل دون أداء ودون جواب كتابي جدي.",
            "ملاحظة: وثيقة وهمية لاختبار LexHub.",
        ],
    )

    save_doc(
        "04_requete_introductive.docx",
        "مقال افتتاحي — أداء دين تجاري وتعويض",
        [
            "المملكة المغربية",
            "المحكمة التجارية بالدار البيضاء",
            "ملف تجاري عدد: 2025/8201/1547 — رقم الرائج / RG: 2025/1547",
            "الغرفة التجارية الأولى — كتابة الضبط: قسم القضايا التجارية",
            "القاضي المقرر: ذ. كريم المنصوري",
            "المدعية: ليلى بنعمر — ينوب عنها ذ. معاذ السنان",
            "المدعى عليه: إحسان التازي",
            "الموضوع: المطالبة بأداء دين تجاري مع التعويض والشرط الجزائي والنفاذ المعجل وتحميل الصائر",
            "الوقائع: أبرم الطرفان عقد توريد CT-2024/088 بتاريخ 12/03/2024. "
            "استمرت التوريدات إلى نهاية نونبر 2024. توقف المدعى عليه عن الأداء رغم الإنذار الرسمي "
            "المبلغ بتاريخ 16/01/2025. الدين الثابت بالفواتير يبلغ 247.450 درهم.",
            "الملتمسات: الحكم بأداء المبلغ الأصلي 247.450 درهم، والشرط الجزائي عن أشهر التأخير "
            "(تقديراً 25.000 درهم)، وتعويض عن الضرر التجاري قدره 15.000 درهم، مع النفاذ المعجل والصائر.",
            "الأسانيد: قانون الالتزامات والعقود، مدونة التجارة، العقد والوثائق المحاسبية.",
            "ملاحظة: وثيقة وهمية لاختبار LexHub.",
        ],
    )

    save_doc(
        "05_pv_constat.docx",
        "محضر معاينة محل المدعى عليه (اختبار)",
        [
            "بتاريخ 20 فبراير 2025، عاين المفوض القضائي استمرار نشاط محل «إحسان ماركت» "
            "بشارع الزرقطوني رقم 210 بالدار البيضاء، مع وجود بضائع معروضة للبيع وحركة زبناء، "
            "مما يدل على استمرار النشاط التجاري ووجود ملاءة ظاهرية.",
            "ملاحظة: وثيقة وهمية لاختبار LexHub.",
        ],
    )

    # --- Fiche LexHub (à recopier dans l’UI) ---
    fiche = """# فiche dossier LexHub — à remplir exactement

## Création dossier (Nouveau dossier)

| Champ LexHub | Valeur à saisir |
|---|---|
| Référence / N° dossier cabinet | WV-2026-COMM-1547 |
| Titre / objet | مرافعة تجارية — أداء دين ليلى ضد إحسان |
| Matière / domaine | Commercial / تجاري |
| Client (partie cabinet) | ليلى بنعمر |
| Adverse | إحسان التازي |
| Description | نزاع توريد: عدم أداء فواتير بعد إنذار. دين 247.450 درهم + شرط جزائي + تعويض. |

## Identité juridique (fiche dossier)

| Champ | Valeur |
|---|---|
| Degré de juridiction | ابتدائي (premier degré) |
| Tribunal | المحكمة التجارية / commerce |
| Ville du tribunal | الدار البيضاء |
| Rôle client | مدعية / demandeur |
| Nature client | شخص طبيعي / personne physique |
| Domicile client | حي المعاريف، زنقة 12 رقم 45، الدار البيضاء |
| Nature adverse | شخص طبيعي |
| Domicile adverse | شارع الزرقطوني رقم 210، الدار البيضاء (محل إحسان ماركت) |

## Dossier judiciaire vivant

| Champ | Valeur |
|---|---|
| N° RG / رقم الرائج | 2025/1547 |
| Chambre | الغرفة التجارية الأولى |
| Greffe | قسم القضايا التجارية — المحكمة التجارية بالدار البيضاء |
| Juge / مقرر | ذ. كريم المنصوري |
| Statut procédure | رائج / en cours (instruction) |
| Avocat plaidant (export) | معاذ السنان |

## Type plaidoirie dans LexHub

- Filtre domaine : **تجاري / Commercial**
- Type : **مرافعة تجارية** (`commercial` / libre si besoin)

## Checklist avant Rédaction IA

1. Créer le dossier avec TOUS les champs ci-dessus
2. Uploader les 5 DOCX dans Documents du dossier
3. Attendre indexation / OCR (statut prêt)
4. Plaidoirie → lier ce dossier
5. Dictée : lire `06_dictée_courte.txt` OU `07_dictée_longue.txt`
6. Corriger → Rédaction IA → vérifier que le PDF cite : المحكمة التجارية، رقم 2025/1547، المبالغ، الإنذار
"""
    (OUT / "00_FICHE_DOSSIER_LexHub.md").write_text(fiche.strip() + "\n", encoding="utf-8")

    dictation_short = """السيد الرئيس.
أتقدم بمرافعة لفائدة موكلتي ليلى بنعمر ضد إحسان التازي
في الملف التجاري عدد ألفين وخمسة وعشرين شرطة ألف وخمسمائة وسبعة وأربعين
أمام المحكمة التجارية بالدار البيضاء.
المدعى عليه لم يؤد الفواتير رغم الإنذار.
نلتمس الحكم بالأداء والتعويض والصائر.
"""
    (OUT / "06_dictée_courte.txt").write_text(dictation_short.strip() + "\n", encoding="utf-8")

    dictation_long = """بسم الله الرحمن الرحيم.
السيد رئيس المحكمة التجارية بالدار البيضاء المحترم،
السادة المستشارون الأجلاء.

أتشرف بأن أتقدم أمام محكمتكم الموقرة بهذه المرافعة
لفائدة موكلتي السيدة ليلى بنعمر،
ضد المدعى عليه السيد إحسان التازي،
في الملف التجاري عدد ألفين وخمسة وعشرين شرطة ألف وخمسمائة وسبعة وأربعين،
المعروض على الغرفة التجارية الأولى.

أولاً في تحديد الأطراف والاختصاص:
موكلتي مورّدة تمارس نشاط التوزيع تحت اسم ليلى فود،
والمدعى عليه يستغل محل إحسان ماركت بشارع الزرقطوني.
والاختصاص منعقد لمحكمتكم التجارية طبقاً للعقد وللطبيعة التجارية للنزاع.

ثانياً في الوقائع:
أبرم الطرفان عقد توريد مؤرخ في الثاني عشر من مارس سنة ألفين وأربعة وعشرين تحت عدد سي تي ألفين وأربعة وعشرين شرطة صفر ثمانية ثمانية،
يقضي بتوريد شهري وأداء داخل أجل ثلاثين يوماً من كل فاتورة،
مع شرط جزائي عند التأخير.
وقد أنجزت موكلتي التوريدات الثابتة بالفواتير:
فاتورة أكتوبر بمبلغ اثنين وثمانين ألفاً وأربعمائة وخمسين درهماً،
وفاتورة نونبر بمبلغ تسعة وسبعين ألفاً وثمانمائة درهم،
وفاتورة نهاية نونبر بمبلغ خمسة وثمانين ألفاً ومائتي درهم،
ليصل مجموع الدين غير المؤدى إلى مائتين وسبعة وأربعين ألفاً وأربعمائة وخمسين درهماً.
ثم وجهت إنذاراً رسمياً بواسطة مفوض قضائي بلغ بتاريخ السادس عشر من يناير سنة ألفين وخمسة وعشرين،
دون أداء ودون تسوية جدية.
ومحضر المعاينة يؤكد استمرار نشاط محل المدعى عليه.

ثالثاً في المناقشة القانونية:
وحيث إن الالتزام بالوفاء ثابت بالعقد والفواتير والإنذار،
وحيث إن عدم التنفيذ يرتب المسؤولية العقدية طبقاً لقواعد قانون الالتزامات والعقود ومدونة التجارة،
وحيث إن الشرط الجزائي المتفق عليه واجب التطبيق فضلاً عن التعويض عن الضرر التجاري اللاحق بموكلتي.

رابعاً في الملتمسات:
ولهذه الأسباب، ألتمس من محكمتكم الموقرة:
الحكم على المدعى عليه بأداء مبلغ مائتين وسبعة وأربعين ألفاً وأربعمائة وخمسين درهماً أصلاً،
والحكم بأداء الشرط الجزائي تقديراً خمسة وعشرين ألف درهم،
والتعويض عن الضرر التجاري قدره خمسة عشر ألف درهم،
مع شمول الحكم بالنفاذ المعجل،
وتحميل المدعى عليه الصائر.

والسلام عليكم ورحمة الله تعالى وبركاته.
"""
    (OUT / "07_dictée_longue.txt").write_text(dictation_long.strip() + "\n", encoding="utf-8")

    expected = """# ما الذي يجب أن apparaisse dans la plaidoirie IA

Si le compose fonctionne correctement, le document doit contenir au minimum :

1. **المحكمة التجارية بالدار البيضاء** + **رقم الملف / RG 2025/1547**
2. الأطراف : ليلى بنعمر (مدعية) / إحسان التازي (مدعى عليه)
3. العقد CT-2024/088 + dates + obligation d’paiement 30 jours
4. Les 3 factures et le total **247.450 درهم**
5. الإنذار المبلغ بتاريخ 16/01/2025
6. Discussion juridique (LOC / مدونة التجارة / شرط جزائي) — pas 2 phrases vides
7. ملتمسات chiffrés : 247.450 + 25.000 + 15.000 + نفاذ معجل + صائر
8. Structure complète : أطراف / وقائع / مناقشة / ملتمسات (pas un résumé de 10 lignes)

## Tests à faire

| Test | Dictée | Attendu |
|------|--------|---------|
| A — IA max | `06_dictée_courte.txt` | Texte long enrichi depuis les pièces |
| B — fidélité | `07_dictée_longue.txt` | Conserve montants + ajoute détails pièces |
| C — export | Word + PDF | En-tête cabinet + armoiries + corps complet |
"""
    (OUT / "08_ATTENDU_qualité_IA.md").write_text(expected.strip() + "\n", encoding="utf-8")

    readme = """# Kit test — Dossier commercial complet (arabe)

Dossier **fictif** prêt pour LexHub : fiche + 5 pièces + dictée courte + dictée longue.

## Contenu

| Fichier | Rôle |
|---------|------|
| `00_FICHE_DOSSIER_LexHub.md` | **Tous les champs** à remplir dans LexHub |
| `01_عقد_توريد_ليلى_إحسان.docx` | Contrat de fourniture |
| `02_فاتورة_وفاتورة_مذكرة.docx` | 3 factures / dette 247.450 MAD |
| `03_إنذار_رسمي.docx` | Mise en demeure |
| `04_مقال_افتتاحي.docx` | Requête + RG 2025/1547 |
| `05_محضر_معاينة.docx` | PV d’huissier |
| `06_dictée_courte.txt` | ~20 s — teste si l’IA développe depuis les pièces |
| `07_dictée_longue.txt` | ~90 s — dictée barreau complète |
| `08_ATTENDU_qualité_IA.md` | Critères de réussite |

## Parcours rapide (prod)

1. Connexion cabinet démo / admin
2. **Dossiers** → Nouveau → recopier `00_FICHE_DOSSIER_LexHub.md`
3. Uploader les 5 DOCX → attendre indexation
4. **Plaidoirie** → type commercial → lier le dossier
5. Micro : d’abord `06` (court), puis éventuellement `07` (long)
6. Rédaction IA → comparer avec `08_ATTENDU…`

Régénérer : `python docs/kit-test-plaidoirie-commercial-complet/generate_kit.py`
"""
    (OUT / "README.md").write_text(readme.strip() + "\n", encoding="utf-8")
    print("DONE", OUT)


if __name__ == "__main__":
    main()
