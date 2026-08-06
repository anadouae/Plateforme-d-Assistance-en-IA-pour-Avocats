"""Corpus auto-update service — manifest, sync, reindex."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MANIFEST_PATH = DATA_DIR / "corpus_manifest.json"
SHARDS_DIR = DATA_DIR / "bo_shards"


def get_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"total_entries": 0, "target_entries": 130000, "progress_pct": 0}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def list_shard_paths() -> list[Path]:
    if not SHARDS_DIR.exists():
        return []
    return sorted(SHARDS_DIR.glob("bo_*.json"))


def sync_corpus(scale: str = "demo", rebuild: bool = False) -> dict:
    """Run fetch_bo_updates sync and reindex ChromaDB."""
    import sys
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from scripts.fetch_bo_updates import sync

    report = sync(scale=scale, rebuild=rebuild)

    try:
        from app.services.rag import reindex_all_corpus

        index_stats = reindex_all_corpus()
        report["reindex"] = index_stats
    except Exception as exc:
        logger.warning("Reindex after sync failed: %s", exc)
        report["reindex_error"] = str(exc)

    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    return report
