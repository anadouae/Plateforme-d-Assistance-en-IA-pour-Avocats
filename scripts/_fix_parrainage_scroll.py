from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\app\settings\page.tsx")
t = p.read_text(encoding="utf-8")
old = """    const timer = window.setTimeout(() => {
      document.getElementById("parrainage")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);"""
new = """    const timer = window.setTimeout(() => {
      document.getElementById("parrainage")?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 600);"""
if old not in t:
    raise SystemExit("scroll pattern not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("ok")
