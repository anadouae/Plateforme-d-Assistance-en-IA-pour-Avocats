from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\app\redaction\page.tsx")
t = p.read_text(encoding="utf-8")

old = '''    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          (i.case_reference || "").toLowerCase().includes(q) ||
          (i.assigned_to_name || "").toLowerCase().includes(q),
      );
    }
    return [...list].sort((a, b) => Number(!!b.pinned) - Number(!!a.pinned));
  }, [items, filter, search, period]);

  function openNew() {
    router.push("/redaction/libre");
  }

  function openEdit(d: PlaidoirieDraftItem) {
    try {
      sessionStorage.setItem(
        PLEA_DRAFT_RESTORE_KEY,
        JSON.stringify({
          title: d.title,
          body: d.body,
          case_id: d.case_id || "",
          checks: d.checks || [],
          template_id: d.template_id || "libre",
          resume_step: 3,
        }),
      );
    } catch {
      /* ignore */
    }
    router.push("/redaction/libre");
  }'''

new = '''    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          (i.case_reference || "").toLowerCase().includes(q) ||
          (i.assigned_to_name || "").toLowerCase().includes(q) ||
          (i.template_id || "").toLowerCase().includes(q),
      );
    }
    if (typeFilter !== "all") {
      list = list.filter((i) => (i.template_id || "libre") === typeFilter);
    }
    return [...list].sort((a, b) => Number(!!b.pinned) - Number(!!a.pinned));
  }, [items, filter, search, period, typeFilter]);

  function openNew() {
    router.push("/redaction/new");
  }

  function openEdit(d: PlaidoirieDraftItem) {
    try {
      sessionStorage.setItem(
        PLEA_DRAFT_RESTORE_KEY,
        JSON.stringify({
          title: d.title,
          body: d.body,
          case_id: d.case_id || "",
          checks: d.checks || [],
          template_id: d.template_id || "libre",
          resume_step: 3,
        }),
      );
    } catch {
      /* ignore */
    }
    router.push(`/redaction/${encodeURIComponent(d.template_id || "libre")}`);
  }'''

if old not in t:
    raise SystemExit("block not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("redaction page ok")
