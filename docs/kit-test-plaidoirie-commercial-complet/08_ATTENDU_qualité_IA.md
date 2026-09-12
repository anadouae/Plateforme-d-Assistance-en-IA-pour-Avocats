# ما الذي يجب أن apparaisse dans la plaidoirie IA

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
