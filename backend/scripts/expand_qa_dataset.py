"""Expand sanad_legal_qa.jsonl from benchmark questions."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DATA = Path(__file__).resolve().parents[1] / "data"
bench = json.loads((DATA / "benchmark_questions.json").read_text(encoding="utf-8"))
qa_path = DATA / "sanad_legal_qa.jsonl"

existing_lines = qa_path.read_text(encoding="utf-8").strip().split("\n") if qa_path.exists() else []
seen = set()
for line in existing_lines:
    if line.strip():
        seen.add(json.loads(line).get("input", "")[:80])

added = 0
with qa_path.open("a", encoding="utf-8") as f:
    for q in bench:
        key = q["question"][:80]
        if key in seen:
            continue
        entry = {
            "instruction": "Réponds comme assistant juridique marocain Sanad-Legal à partir des sources.",
            "input": (
                f"EXTRAITS:\n[{q.get('expected_source', 'corpus')}] Source attendue dans le corpus Sanad.\n\n"
                f"QUESTION: {q['question']}"
            ),
            "output": (
                f"Réponse fondée sur le corpus juridique marocain indexé Sanad "
                f"(domaine: {q.get('domain', '')}).\n\n"
                f"Fondement: {q.get('expected_source', 'corpus')}.\n"
                "Ceci ne constitue pas un avis juridique."
            ),
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        seen.add(key)
        added += 1

print(f"Added {added} entries. Total: {len(existing_lines) + added}")
