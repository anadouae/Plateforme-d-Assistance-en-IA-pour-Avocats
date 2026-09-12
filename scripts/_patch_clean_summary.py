#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/services/agent.py"
t = p.read_text(encoding="utf-8")
if "def _clean_summary_md" not in t:
    helper = '''
def _clean_summary_md(summary: str) -> str:
    s = (summary or "").strip()
    if s.startswith("```"):
        s = s.split("\\n", 1)[-1]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
        s = s.strip()
        if s.lower().startswith("markdown"):
            s = s[8:].lstrip()
    return s.strip()

'''
    # fix the escaped newline - write real newlines
    helper = (
        "def _clean_summary_md(summary: str) -> str:\n"
        "    s = (summary or \"\").strip()\n"
        "    if s.startswith(\"```\"):\n"
        "        s = s.split(\"\\n\", 1)[-1]\n"
        "        if s.rstrip().endswith(\"```\"):\n"
        "            s = s.rstrip()[:-3]\n"
        "        s = s.strip()\n"
        "        if s.lower().startswith(\"markdown\"):\n"
        "            s = s[8:].lstrip()\n"
        "    return s.strip()\n\n\n"
    )
    anchor = 'def generate_synthesis(document_name: str, text: str, language: str = "ar") -> dict:'
    t = t.replace(anchor, helper + anchor, 1)

# Apply cleaner on successful LLM summary returns
t = t.replace(
    '"summary": summary,\n                "sources": [Citation(label=document_name, excerpt=preview[:300])],\n                "disclaimer": disclaimer,\n            }\n\n    # Secours LLM prose',
    '"summary": _clean_summary_md(summary),\n                "sources": [Citation(label=document_name, excerpt=preview[:300])],\n                "disclaimer": disclaimer,\n            }\n\n    # Secours LLM prose',
    1,
)
t = t.replace(
    '"summary": summary,\n            "sources": [Citation(label=document_name, excerpt=preview[:300])],\n            "disclaimer": disclaimer,\n        }\n\n    # Dernier recours',
    '"summary": _clean_summary_md(summary),\n            "sources": [Citation(label=document_name, excerpt=preview[:300])],\n            "disclaimer": disclaimer,\n        }\n\n    # Dernier recours',
    1,
)
p.write_text(t, encoding="utf-8")
print("ok", t.count("_clean_summary_md"))
