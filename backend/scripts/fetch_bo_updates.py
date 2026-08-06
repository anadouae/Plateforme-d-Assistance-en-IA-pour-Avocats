"""Sync corpus manifest and optional external BO imports."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_bo_corpus import build_entries, write_manifest, write_shards, SHARDS_DIR, MANIFEST, DATA

IMPORT_DIR = DATA / "bo_imports"


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def merge_imports(entries: list[dict]) -> tuple[list[dict], int]:
    by_id = {e["id"]: e for e in entries}
    added = 0
    if not IMPORT_DIR.exists():
        return list(by_id.values()), 0

    for path in sorted(IMPORT_DIR.glob("*.json")):
        for entry in json.loads(path.read_text(encoding="utf-8")):
            eid = entry.get("id")
            if not eid:
                continue
            if eid not in by_id:
                added += 1
            by_id[eid] = entry

    return list(by_id.values()), added


def sync(scale: str = "demo", rebuild: bool = False) -> dict:
    if rebuild or not SHARDS_DIR.exists() or not any(SHARDS_DIR.glob("bo_*.json")):
        entries = build_entries(scale)
    else:
        entries = []
        for shard in sorted(SHARDS_DIR.glob("bo_*.json")):
            entries.extend(json.loads(shard.read_text(encoding="utf-8")))

    entries, added = merge_imports(entries)
    shard_files = write_shards(entries)
    write_manifest(entries, scale, shard_files)

    report = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "scale": scale,
        "total_entries": len(entries),
        "imports_added": added,
        "shard_count": len(shard_files),
        "manifest": load_manifest(),
    }
    report_path = DATA / "corpus_sync_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", default="demo", choices=["demo", "production", "adala"])
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    result = sync(scale=args.scale, rebuild=args.rebuild)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
