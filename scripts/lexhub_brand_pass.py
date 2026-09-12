#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOGO_SWAPS = [
    ("frontend/src/components/brand/sanad-logo.tsx", "/logo-sanad-cube.png?v=cube-1", "/logo-lexhub-cube.png?v=cube-2"),
    ("frontend/src/components/brand/sanad-page-loader.tsx", "/logo-sanad-cube.png?v=cube-1", "/logo-lexhub-cube.png?v=cube-2"),
    ("frontend/src/components/layout/app-sidebar.tsx", "/logo-sanad-cube.png?v=cube-1", "/logo-lexhub-cube.png?v=cube-2"),
    ("frontend/src/components/layout/admin-shell.tsx", "/logo-sanad-cube.png", "/logo-lexhub-cube.png"),
    ("frontend/src/app/layout.tsx", "/logo-sanad-cube.png", "/logo-lexhub-cube.png"),
    ("frontend/src/app/globals.css", "/logo-sanad-cube.png", "/logo-lexhub-cube.png"),
    ("frontend/src/components/brand/sanad-animated-logo.tsx", "/logo-sanad-cube.png?v=cube-1", "/logo-lexhub-cube.png?v=cube-2"),
    ("frontend/src/components/brand/sanad-logo-animated.tsx", "/logo-sanad-cube.png?v=cube-1", "/logo-lexhub-cube.png?v=cube-2"),
]

for rel, a, b in LOGO_SWAPS:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    if a in t:
        p.write_text(t.replace(a, b), encoding="utf-8")
        print("logo", rel)
    else:
        print("skip", rel)

for rel in (
    "frontend/src/hooks/use-cabinet-realtime.ts",
    "frontend/src/components/layout/app-shell.tsx",
):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    t2 = t.replace(
        'sessionStorage.getItem("sanad_token")',
        'sessionStorage.getItem("lexhub_token") || sessionStorage.getItem("sanad_token")',
    ).replace(
        'localStorage.getItem("sanad_token")',
        'localStorage.getItem("lexhub_token") || localStorage.getItem("sanad_token")',
    )
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print("token dual", rel)

g = ROOT / "frontend/src/app/globals.css"
gt = g.read_text(encoding="utf-8")
if "--lexhub-navy" not in gt:
    g.write_text(
        gt
        + """

/* LexHub aliases (Sanad tokens conservés pour compat) */
:root {
  --lexhub-navy: var(--sanad-navy);
  --lexhub-ivory: var(--sanad-ivory);
  --lexhub-gold: var(--sanad-gold);
  --lexhub-stone: var(--sanad-stone);
  --lexhub-cream: var(--sanad-cream);
  --lexhub-logo: var(--sanad-logo);
}
""",
        encoding="utf-8",
    )
    print("css aliases")

em = ROOT / "backend/app/services/email.py"
et = em.read_text(encoding="utf-8")
et2 = et.replace("logo-sanad-cube.png", "logo-lexhub-cube.png")
if et2 != et:
    em.write_text(et2, encoding="utf-8")
    print("email logo")

# remaining Sanad product strings
for rel in (
    "backend/app/services/agent.py",
    "backend/app/services/document_pipeline.py",
):
    p = ROOT / rel
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    t2 = t.replace("Sanad-Legal", "LexHub-Legal").replace("corpus Sanad", "corpus LexHub").replace(
        "administrateur Sanad", "administrateur LexHub"
    ).replace("Sanad", "LexHub")
    # undo false positives if any legal Arabic - unlikely in these files
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print("backend str", rel)

print("done")
