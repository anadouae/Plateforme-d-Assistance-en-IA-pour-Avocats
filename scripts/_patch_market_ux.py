from pathlib import Path

# Fix tarifs button + syntax
p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\app\tarifs\page.tsx")
t = p.read_text(encoding="utf-8")
t = t.replace(
    ''': "Démarrer l'essai Cabinet";              return (''',
    ''': "Démarrer l'essai Cabinet";
              return (''',
)
t = t.replace("{ctaLabel(plan.slug, ar, p)}", "{btn}")
p.write_text(t, encoding="utf-8")
print("tarifs ok")

# Fix roles
r = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\lib\roles.ts")
rt = r.read_text(encoding="utf-8")
rt = rt.replace('Stagiaire', 'Assistant')
rt = rt.replace('متدرّج', 'مساعد')
rt = rt.replace('Avocat admin', 'Admin cabinet')
rt = rt.replace('محامٍ مسؤول', 'مسؤول المكتب')
r.write_text(rt, encoding="utf-8")
print("roles ok", 'Assistant' in rt)

# Mobile dock labels - show under icons
css = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\styles\sanad-ui.css")
c = css.read_text(encoding="utf-8")
old = "    .dock-item::after{ display:none; }"
new = """    .dock-item::after{
      display:block !important;
      position: static;
      left: auto; right: auto; top: auto;
      transform: none;
      margin-top: 2px;
      font-size: 9px;
      font-weight: 600;
      letter-spacing: 0.01em;
      color: var(--ink-soft);
      white-space: nowrap;
      max-width: 64px;
      overflow: hidden;
      text-overflow: ellipsis;
      opacity: 1;
      pointer-events: none;
    }
    .dock-item{ flex-direction: column; height: auto; min-height: 48px; padding: 6px 4px; gap: 0; }"""
if old in c:
    css.write_text(c.replace(old, new), encoding="utf-8")
    print("css ok")
else:
    print("css pattern missing")
