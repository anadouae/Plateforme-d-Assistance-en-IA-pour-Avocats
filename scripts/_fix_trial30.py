from pathlib import Path
p = Path("backend/app/api/auth.py")
t = p.read_text(encoding="utf-8")
old = 'getattr(app_settings, "BILLING_TRIAL_DAYS", 14) or 14'
new = 'getattr(app_settings, "BILLING_TRIAL_DAYS", 30) or 30'
if old in t:
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("updated")
elif new in t:
    print("already 30")
else:
    print("pattern not found")
