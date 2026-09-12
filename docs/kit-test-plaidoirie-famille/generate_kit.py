# -*- coding: utf-8 -*-
"""Génère le kit de test plaidoirie famille (pièces DOCX + script dictée)."""
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
    save_doc(
        "01_Acte_mariage_Fatima_Alami.docx",
        "صورة مطابقة — عقد زواج (وثيقة اختبار LexHub)",
        [
            "المملكة المغربية — وزارة العدل",
            "عقد زواج رقم 2020/م/1847",
            "بتاريخ 15 يونيو 2020 بمدينة الرباط.",
            "الزوج: السيد كريم بناني، مغربي، مزداد بتاريخ 12 مارس 1988 بالدار البيضاء، رقم البطاقة الوطنية AB123456.",
            "الزوجة: السيدة فاطمة العلوي، مغربية، مزدادة بتاريخ 03 شتنبر 1992 بالرباط، رقم البطاقة الوطنية CD789012.",
            "تم الزواج على سنة الله ورسوله، بصداق مسمى قدره عشرون ألف درهم (20.000 درهم).",
            "ملاحظة: وثيقة وهمية لأغراض اختبار منصة LexHub فقط — ليست وثيقة رسمية.",
        ],
    )
    save_doc(
        "02_Extrait_naissance_Youssef.docx",
        "شهادة ميلاد — يوسف بناني (وثيقة اختبار)",
        [
            "الاسم الكامل: يوسف بناني",
            "تاريخ الازدياد: 20 يناير 2021 — الرباط",
            "الأب: كريم بناني",
            "الأم: فاطمة العلوي",
            "رقم عقد الازدياد: 2021/ر/4521",
            "ملاحظة: وثيقة وهمية لاختبار LexHub.",
        ],
    )
    save_doc(
        "03_Requete_nafaka_hadana.docx",
        "مقال افتتاحي — نفقة وحضانة (وثيقة اختبار)",
        [
            "المحكمة الابتدائية بالرباط — قسم قضاء الأسرة",
            "ملف رقم: 2024/120",
            "المدعية: فاطمة العلوي — ينوب عنها ذ. [محامي الاختبار]",
            "المدعى عليه: كريم بناني",
            "الموضوع: المطالبة بالنفقة والحضانة",
            (
                "الوقائع باختصار: انعقد الزواج بتاريخ 15/06/2020؛ رزق الطرفان بالابن يوسف "
                "(مواليد 20/01/2021). توقفت المدعى عليها عن تلقي النفقة منذ فاتح يناير 2024. "
                "تطلب المدعية الحكم بنفقة شهرية قدرها 2000 درهم مع النفاذ المعجل، وإسناد الحضانة "
                "إليها مراعاة لمصلحة المحضون، وتحميل المدعى عليه الصائر."
            ),
            "الأسانيد: مدونة الأسرة — أحكام النفقة والحضانة.",
            "ملاحظة: وثيقة وهمية لاختبار LexHub.",
        ],
    )
    save_doc(
        "05_Mise_en_demeure.docx",
        "إنذار بأداء النفقة (وثيقة اختبار LexHub)",
        [
            "الرباط في 10 يناير 2024",
            "من: ذ. [محامي الاختبار] نيابة عن السيدة فاطمة العلوي",
            "إلى: السيد كريم بناني — شارع محمد الخامس رقم 45، سلا",
            "الموضوع: إنذار بأداء واجب النفقة للابن القاصر يوسف",
            (
                "يشرفني أن أنذركم، في أجل ثمانية أيام من توصلهم بهذا الإنذار، "
                "بأداء واجب النفقة المتخلد بذمتكم منذ فاتح يناير 2024، "
                "وقدره ألفا درهم شهرياً، طبقاً لأحكام مدونة الأسرة. "
                "وبانصرام الأجل دون أداء، سنلجأ إلى المحكمة الابتدائية بالرباط — قسم قضاء الأسرة."
            ),
            "ملاحظة: وثيقة وهمية لاختبار LexHub — ليست إنذاراً رسمياً.",
        ],
    )

    script = """بسم الله الرحمن الرحيم.
السيد الرئيس، السادة المستشارون المحترمون.

أتشرف بأن أتقدم أمام محكمتكم الموقرة بهذه المرافعة
لفائدة موكلتي السيدة فاطمة العلوي،
ضد المدعى عليه السيد كريم بناني،
في ملف النفقة والحضانة عدد 2024/120
المعروض على قسم قضاء الأسرة بالمحكمة الابتدائية بالرباط.

إن الوقائع ثابتة بموجب عقد الزواج المبرم بتاريخ
الخامس عشر من شهر يونيو سنة ألفين وعشرين،
وبموجب شهادة ميلاد الابن القاصر يوسف المزداد بتاريخ العشرين من يناير سنة ألفين وواحد وعشرين.

وحيث إن المدعى عليه توقف عن أداء واجب النفقة منذ فاتح يناير سنة ألفين وأربعة وعشرين،
رغم يساره وقدرته على الإنفاق.

وبناء على قواعد مدونة الأسرة،
فإن واجب النفقة يقع على عاتق الأب،
كما أن مصلحة المحضون تقتضي استقرار حضانته لدى والدته.

ولهذه الأسباب، ألتمس من محكمتكم الموقرة
الحكم على المدعى عليه بأداء نفقة شهرية قدرها ألفا درهم،
مع شمول الحكم بالنفاذ المعجل،
وإسناد حضانة الابن يوسف إلى والدته،
وتحميله الصائر.

والسلام عليكم ورحمة الله تعالى وبركاته.
"""
    (OUT / "04_Texte_dictée_à_lire_à_voix_haute.txt").write_text(
        script.strip() + "\n", encoding="utf-8"
    )

    readme = """# Kit test plaidoirie — Famille (nafaka / hadana)

## Type à choisir dans LexHub

- **Matière / domaine :** Famille (أسرة)
- **Type de plaidoirie :** `famille` — Famille (طلاق، نفقة، حضانة)
- **Tribunal typique :** المحكمة الابتدائية — قسم قضاء الأسرة (TPI, section famille)

## Fichiers

| Fichier | Usage |
|---------|--------|
| `00_FICHE_DOSSIER.txt` | Valeurs à recopier dans Nouveau dossier |
| `01_Acte_mariage_Fatima_Alami.docx` | Pièce 1 — contrat de mariage |
| `02_Extrait_naissance_Youssef.docx` | Pièce 2 — naissance enfant |
| `03_Requete_nafaka_hadana.docx` | Pièce 3 — résumé requête |
| `04_Texte_dictée_à_lire_à_voix_haute.txt` | Script micro (~45 s) |
| `05_Mise_en_demeure.docx` | Pièce 4 — mise en demeure |
| `06_Dictee_courte.txt` | Script micro court |
| `GUIDE_PAS_A_PAS.md` | Mode d’emploi écran par écran |

## Parcours test (prod)

1. Connexion `demo@sanad.ma` / `Sanad2026!`
2. **Dossiers** → créer dossier domaine **Famille**, n° `2024/120`, parties Fatima / Karim
3. Uploader les 3 DOCX dans **Documents** du dossier
4. **Plaidoirie** → Nouvelle → filtre **Famille** → type **Famille**
5. Étape 1 : lier le dossier (+ pièces indexées)
6. Étape 2 : micro → lire `04_…txt`
7. Transcription → Corriger → Rédaction IA → Export Word/PDF

Documents **fictifs** — test uniquement.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print("DONE", OUT)


if __name__ == "__main__":
    main()
