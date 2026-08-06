"""Multi-corpus RAG — MA, OHADA, jurisprudence + case documents."""

import json
import logging
import re
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_embedding_fn = None
_corpus_loaded: set[str] = set()
_chromadb_available: bool | None = None

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CHUNK_SIZE = 500
CORPUS_VERSION = "4.0"
SHARDS_DIR = DATA_DIR / "bo_shards"
MANIFEST_PATH = DATA_DIR / "corpus_manifest.json"


def _bo_shard_paths() -> list[Path]:
    if not SHARDS_DIR.exists():
        return []
    return sorted(SHARDS_DIR.glob("bo_*.json"))


CORPUS_SOURCES = {
    "legal_corpus_ma": [
        DATA_DIR / "legal_corpus.json",
        DATA_DIR / "legal_corpus_extended.json",
        *_bo_shard_paths(),
    ],
    "legal_corpus_ohada": [DATA_DIR / "ohada_corpus.json"],
    "legal_corpus_jurisprudence": [DATA_DIR / "jurisprudence_corpus.json"],
}

OHADA_KEYWORDS = {
    "ohada", "ccja", "acte uniforme", "sarl ohada", "arbitrage ohada",
    "traité ohada", "sûreté ohada", "insolvabilité ohada",
}


def _check_chromadb() -> bool:
    global _chromadb_available
    if _chromadb_available is None:
        try:
            import chromadb  # noqa: F401
            _chromadb_available = True
        except ImportError:
            logger.warning("ChromaDB not installed — using keyword fallback RAG")
            _chromadb_available = False
    return _chromadb_available


def _get_chromadb():
    import chromadb
    return chromadb


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions
        try:
            _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL,
            )
        except Exception as exc:
            logger.warning("BGE-M3 load failed (%s), fallback MiniLM", exc)
            _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2",
            )
    return _embedding_fn


def warmup_embeddings() -> None:
    """Pre-load embedding model so first chat query is not blocked ~60-90s."""
    ef = _get_embedding_fn()
    try:
        ef(["warmup"])
        logger.info("Embedding model ready (%s)", settings.EMBEDDING_MODEL)
    except Exception as exc:
        logger.warning("Embedding warmup failed: %s", exc)


def get_client():
    global _client
    if _client is None:
        chromadb = _get_chromadb()
        Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size // 5):
        chunk = " ".join(words[i : i + chunk_size // 5])
        if len(chunk) > 30:
            chunks.append(chunk)
    return chunks or [text[:chunk_size]]


def _case_collection_name(cabinet_id: str, case_id: str) -> str:
    return f"case_{cabinet_id}_{case_id}"


def _load_entries_from_files(paths: list[Path]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for path in paths:
        if not path.exists():
            continue
        for entry in json.loads(path.read_text(encoding="utf-8")):
            eid = entry.get("id")
            if not eid:
                continue
            existing = by_id.get(eid)
            if existing is None or len(entry.get("text", "")) > len(existing.get("text", "")):
                by_id[eid] = entry
    return list(by_id.values())


def _load_all_corpus_entries() -> list[dict]:
    entries = []
    for paths in CORPUS_SOURCES.values():
        entries.extend(_load_entries_from_files(paths))
    return entries


def _keyword_search(question: str, entries: list[dict], top_k: int = 5) -> list[dict]:
    q_words = {w.lower() for w in re.findall(r"\w{3,}", question)}
    hits = []
    for entry in entries:
        kw = set(k.lower() for k in entry.get("keywords", []))
        overlap = len(q_words & kw)
        if overlap > 0:
            score = min(95, 50 + overlap * 12)
            hits.append({
                "source": entry["source"],
                "text": entry["text"],
                "score": score,
                "entry_id": entry["id"],
                "corpus": entry.get("instrument", entry.get("code", "MA")),
            })
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:top_k]


def _index_collection(collection_name: str, entries: list[dict], force: bool = False) -> int:
    if not _check_chromadb():
        return 0

    client = get_client()
    ef = _get_embedding_fn()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine", "version": CORPUS_VERSION},
    )

    if collection.count() > 0 and not force:
        return collection.count()

    if force and collection.count() > 0:
        try:
            client.delete_collection(collection_name)
            collection = client.get_or_create_collection(
                name=collection_name, embedding_function=ef,
                metadata={"hnsw:space": "cosine", "version": CORPUS_VERSION},
            )
        except Exception:
            pass

    ids, documents, metadatas = [], [], []
    for entry in entries:
        chunks = _chunk_text(entry["text"])
        for i, chunk in enumerate(chunks):
            doc_id = f"{entry['id']}_{i}"
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "source": entry["source"],
                "entry_id": entry["id"],
                "keywords": ",".join(entry.get("keywords", [])),
                "corpus": entry.get("instrument", entry.get("code", "MA")),
            })

    if ids:
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
    return len(ids)


def ensure_corpus_collection(collection_name: str, force: bool = False) -> None:
    if collection_name in _corpus_loaded and not force:
        return
    paths = CORPUS_SOURCES.get(collection_name, [])
    entries = _load_entries_from_files(paths)
    count = _index_collection(collection_name, entries, force=force)
    logger.info("Corpus %s: %d chunks indexed", collection_name, count)
    _corpus_loaded.add(collection_name)


def ensure_legal_corpus(force: bool = False) -> None:
    """Index all corpus collections (MA, OHADA, jurisprudence)."""
    for name in CORPUS_SOURCES:
        ensure_corpus_collection(name, force=force)


def reindex_all_corpus() -> dict:
    global _corpus_loaded
    _corpus_loaded = set()
    stats = {}
    for name in CORPUS_SOURCES:
        entries = _load_entries_from_files(CORPUS_SOURCES[name])
        count = _index_collection(name, entries, force=True)
        _corpus_loaded.add(name)
        stats[name] = {"entries": len(entries), "chunks": count}
    return stats


def is_ohada_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in OHADA_KEYWORDS)


def _search_collection(collection_name: str, question: str, top_k: int = 5) -> list[dict]:
    ensure_corpus_collection(collection_name)
    if not _check_chromadb():
        entries = _load_entries_from_files(CORPUS_SOURCES.get(collection_name, []))
        return _keyword_search(question, entries, top_k)

    client = get_client()
    ef = _get_embedding_fn()
    try:
        collection = client.get_collection(name=collection_name, embedding_function=ef)
    except Exception:
        return []

    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
    hits = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 1.0
            score = max(0, min(95, int((1 - dist) * 100)))
            hits.append({
                "source": meta.get("source", collection_name),
                "text": doc,
                "score": score,
                "entry_id": meta.get("entry_id", ""),
                "corpus": meta.get("corpus", collection_name),
            })
    return hits


def search_legal_corpus(question: str, top_k: int = 5, corpus_filter: str | None = None) -> list[dict]:
    """Search legal corpora. Auto-routes OHADA questions."""
    if corpus_filter:
        return _search_collection(corpus_filter, question, top_k)

    if is_ohada_question(question):
        ohada_hits = _search_collection("legal_corpus_ohada", question, top_k)
        if ohada_hits and ohada_hits[0]["score"] >= 40:
            return ohada_hits

    all_hits = []
    for name in CORPUS_SOURCES:
        all_hits.extend(_search_collection(name, question, top_k))
    all_hits.sort(key=lambda h: h["score"], reverse=True)
    return all_hits[:top_k]


def search_legal_corpus_fast(question: str, top_k: int = 5) -> list[dict]:
    """Fast corpus search — MA first, autres collections seulement si nécessaire."""
    if is_ohada_question(question):
        ohada_hits = _search_collection("legal_corpus_ohada", question, top_k)
        if ohada_hits:
            return ohada_hits

    ma_hits = _search_collection("legal_corpus_ma", question, top_k)
    if ma_hits and ma_hits[0]["score"] >= 42:
        return ma_hits

    extra: list[dict] = list(ma_hits)
    for name in ("legal_corpus_ohada", "legal_corpus_jurisprudence"):
        extra.extend(_search_collection(name, question, 3))
    extra.sort(key=lambda h: h["score"], reverse=True)
    return extra[:top_k]


def get_corpus_stats() -> dict:
    stats = {"version": CORPUS_VERSION, "collections": {}}
    total_entries = 0
    for name, paths in CORPUS_SOURCES.items():
        entries = _load_entries_from_files(paths)
        total_entries += len(entries)
        chunks = 0
        if _check_chromadb():
            try:
                client = get_client()
                col = client.get_collection(name)
                chunks = col.count()
            except Exception:
                chunks = 0
        stats["collections"][name] = {
            "entries": len(entries),
            "chunks_indexed": chunks,
            "source_files": len(paths),
        }
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    target = manifest.get("target_entries", 130000)
    stats["total_entries"] = total_entries
    stats["target_adala"] = target
    stats["progress_pct"] = round(total_entries / target * 100, 2) if target else 0
    stats["manifest"] = {
        "scale": manifest.get("scale"),
        "built_at": manifest.get("built_at"),
        "shard_count": manifest.get("shard_count", 0),
        "instruments": manifest.get("instruments", 0),
    }
    return stats


def index_document(
    cabinet_id: str, case_id: str, document_id: str,
    document_name: str, text: str,
) -> int:
    if not text or len(text.strip()) < 20:
        return 0
    if not _check_chromadb():
        return len(_chunk_text(text))

    client = get_client()
    ef = _get_embedding_fn()
    col_name = _case_collection_name(cabinet_id, case_id)
    collection = client.get_or_create_collection(name=col_name, embedding_function=ef)

    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass

    chunks = _chunk_text(text)
    ids, documents, metadatas = [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(f"{document_id}_{i}")
        documents.append(chunk)
        metadatas.append({
            "document_id": document_id,
            "document_name": document_name,
            "chunk_index": i,
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def search_case_documents(cabinet_id: str, case_id: str, question: str, top_k: int = 5) -> list[dict]:
    if not _check_chromadb():
        return []
    client = get_client()
    ef = _get_embedding_fn()
    col_name = _case_collection_name(cabinet_id, case_id)
    try:
        collection = client.get_collection(name=col_name, embedding_function=ef)
    except Exception:
        return []
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
    hits = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 1.0
            score = max(0, min(95, int((1 - dist) * 100)))
            hits.append({
                "source": meta.get("document_name", "Document"),
                "text": doc,
                "score": score,
                "document_id": meta.get("document_id", ""),
            })
    return hits


def search_document_by_id(
    cabinet_id: str, case_id: str, document_id: str, question: str, top_k: int = 3,
) -> list[dict]:
    hits = search_case_documents(cabinet_id, case_id, question, top_k=top_k * 2)
    return [h for h in hits if h.get("document_id") == document_id][:top_k]


def delete_document_index(cabinet_id: str, case_id: str, document_id: str) -> None:
    if not _check_chromadb():
        return
    client = get_client()
    col_name = _case_collection_name(cabinet_id, case_id)
    try:
        collection = client.get_collection(name=col_name)
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass
