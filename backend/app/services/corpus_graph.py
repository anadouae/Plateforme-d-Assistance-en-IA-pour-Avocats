"""Article cartography — graph of legal article relations (style Kanoun)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_graph_cache: dict | None = None


def _load_graph() -> dict:
    global _graph_cache
    if _graph_cache is None:
        path = DATA_DIR / "article_graph.json"
        _graph_cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"nodes": [], "edges": []}
    return _graph_cache


def get_article_graph(article_id: str | None = None, instrument: str | None = None) -> dict:
    graph = _load_graph()
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])

    if article_id:
        related_ids = set()
        for edge in edges:
            if edge["from"] == article_id:
                related_ids.add(edge["to"])
            elif edge["to"] == article_id:
                related_ids.add(edge["from"])
        related_nodes = [nodes[rid] for rid in related_ids if rid in nodes]
        related_edges = [e for e in edges if e["from"] == article_id or e["to"] == article_id]
        return {
            "center": nodes.get(article_id),
            "related": related_nodes,
            "edges": related_edges,
        }

    if instrument:
        filtered_nodes = [n for n in graph.get("nodes", []) if n.get("instrument") == instrument]
        node_ids = {n["id"] for n in filtered_nodes}
        filtered_edges = [e for e in edges if e["from"] in node_ids or e["to"] in node_ids]
        return {"nodes": filtered_nodes, "edges": filtered_edges, "instrument": instrument}

    return graph


def find_graph_for_hits(hits: list[dict]) -> list[dict]:
    """Enrich RAG hits with related articles from the graph."""
    enriched = []
    for hit in hits:
        entry_id = hit.get("entry_id", "")
        if entry_id:
            subgraph = get_article_graph(entry_id)
            hit["related_articles"] = [
                {"id": n["id"], "label": n["label"], "instrument": n.get("instrument")}
                for n in subgraph.get("related", [])
            ]
        enriched.append(hit)
    return enriched
