from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\app\redaction\page.tsx")
t = p.read_text(encoding="utf-8")

if "PLAIDOIRIE_TEMPLATES" not in t:
    t = t.replace(
        'from "@/lib/api";',
        'from "@/lib/api";\nimport { PLAIDOIRIE_TEMPLATES } from "@/lib/plaidoirie-templates";',
        1,
    )

old = """        <select
          className=\"rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm\"
          value={period}
          onChange={(e) => setPeriod(e.target.value as typeof period)}
        >
          <option value=\"all\">{labels.periodAll}</option>
          <option value=\"today\">{labels.periodToday}</option>
          <option value=\"7d\">{labels.period7}</option>
          <option value=\"30d\">{labels.period30}</option>
        </select>
      </div>
      <p className=\"text-xs text-[var(--ink-soft)]\">{labels.shortcuts}</p>"""

new = """        <select
          className=\"rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm\"
          value={period}
          onChange={(e) => setPeriod(e.target.value as typeof period)}
        >
          <option value=\"all\">{labels.periodAll}</option>
          <option value=\"today\">{labels.periodToday}</option>
          <option value=\"7d\">{labels.period7}</option>
          <option value=\"30d\">{labels.period30}</option>
        </select>
        <select
          className=\"rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm\"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          title={isAr ? \"نوع المرافعة\" : \"Type de plaidoirie\"}
        >
          <option value=\"all\">{isAr ? \"كل الأنواع\" : \"Tous les types\"}</option>
          {PLAIDOIRIE_TEMPLATES.map((tpl) => (
            <option key={tpl.id} value={tpl.id}>
              {isAr ? tpl.labelAr : tpl.labelFr}
            </option>
          ))}
        </select>
      </div>
      <p className=\"text-xs text-[var(--ink-soft)]\">{labels.shortcuts}</p>"""

if old not in t:
    raise SystemExit("select block not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("type filter ui ok")
