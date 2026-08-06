"""Bulk import pipeline for legal corpus (BO, jurisprudence, OHADA).

Usage:
  python scripts/import_corpus.py --source bo --file data/bo_export.json
  python scripts/import_corpus.py --source jurisprudence --file data/jp.json
  python scripts/import_corpus.py --source ohada --file data/ohada.json

Expected JSON format: list of objects with keys:
  id, source, text, instrument (optional), domain (optional)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SOURCE_FILES = {
    "ma": Path(__file__).resolve().parents[1] / "data" / "legal_corpus_extended.json",
    "ohada": Path(__file__).resolve().parents[1] / "data" / "ohada_corpus.json",
    "jurisprudence": Path(__file__).resolve().parents[1] / "data" / "jurisprudence_corpus.json",
}


def load_existing(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def merge_entries(existing: list[dict], new_entries: list[dict]) -> tuple[list[dict], int]:
    seen = {e.get("id") for e in existing}
    added = 0
    merged = list(existing)
    for entry in new_entries:
        eid = entry.get("id")
        if not eid or eid in seen:
            continue
        merged.append(entry)
        seen.add(eid)
        added += 1
    return merged, added


def main():
    parser = argparse.ArgumentParser(description="Import legal corpus entries")
    parser.add_argument("--source", choices=["ma", "ohada", "jurisprudence", "bo"], required=True)
    parser.add_argument("--file", required=True, help="JSON file with entries to import")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = "ma" if args.source == "bo" else args.source
    target = SOURCE_FILES[source]
    new_entries = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if not isinstance(new_entries, list):
        print("Error: input must be a JSON array")
        sys.exit(1)

    existing = load_existing(target)
    merged, added = merge_entries(existing, new_entries)
    print(f"Source: {args.source} → {target.name}")
    print(f"Existing: {len(existing)}, New valid: {added}, Total after merge: {len(merged)}")

    if args.dry_run:
        print("Dry run — no files written")
        return

    target.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {added} new entries to {target}")
    print("Run: python scripts/reindex_corpus.py")


if __name__ == "__main__":
    main()
