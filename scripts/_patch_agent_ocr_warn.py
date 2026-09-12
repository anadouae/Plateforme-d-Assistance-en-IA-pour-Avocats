#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/services/agent.py"
t = p.read_text(encoding="utf-8")
t2 = t.replace(
    "if scrambled and not assume_native and not is_audio:",
    "if scrambled and not assume_native and not is_audio and len(text) < 12000:",
    1,
)
t2 = t2.replace(
    "        if scrambled and not assume_native:\n            attention.append(",
    "        if scrambled and not assume_native and len(text) < 12000:\n            attention.append(",
    1,
)
if t2 == t:
    raise SystemExit("no change")
p.write_text(t2, encoding="utf-8")
print("ok", t2.count("len(text) < 12000"))
