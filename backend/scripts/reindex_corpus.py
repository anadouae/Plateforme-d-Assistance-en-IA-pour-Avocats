"""Force reindex of all legal corpora into ChromaDB.

Usage (from backend/):
  python scripts/reindex_corpus.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.rag import get_corpus_stats, reindex_all_corpus  # noqa: E402


def main() -> None:
    print("Reindexing legal corpora (force)...")
    stats = reindex_all_corpus()
    for name, info in stats.items():
        print(f"  {name}: {info['entries']} entries -> {info['chunks']} chunks")
    print("\nCorpus stats:")
    s = get_corpus_stats()
    for name, c in s.get("collections", {}).items():
        print(f"  {name}: {c['entries']} entries, {c['chunks_indexed']} chunks indexed")
    print("Done.")


if __name__ == "__main__":
    main()
