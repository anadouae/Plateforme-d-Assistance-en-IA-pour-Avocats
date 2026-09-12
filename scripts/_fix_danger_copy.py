from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\lib\i18n\translations.ts")
t = p.read_text(encoding="utf-8")
old = (
    '        deleteAccountCabinetNote:\n'
    '          "Seul l\'avocat admin peut fermer le cabinet — y compris s\'il est le seul responsable.",\n'
    '        deleteAccountMemberNote:\n'
    '          "Avocats et assistants : compte personnel uniquement. Pour fermer tout le cabinet, l\'avocat admin doit le faire.",'
)
new = (
    '        deleteAccountCabinetNote:\n'
    '          "Seul l\'avocat admin du cabinet peut fermer tout l\'espace LexHub (tous les comptes de l\'équipe). '
    'Les autres membres ne peuvent supprimer que leur propre compte.",\n'
    '        deleteAccountMemberNote:\n'
    '          "Avocats et assistants : vous pouvez seulement supprimer votre compte personnel. '
    'Pour fermer tout le cabinet, demandez à l\'avocat admin.",'
)
if old not in t:
    raise SystemExit("pattern not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("ok")
