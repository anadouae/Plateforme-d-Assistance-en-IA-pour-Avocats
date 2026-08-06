from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import require_roles
from app.models import UserRole
from app.services.benchmark import get_last_results, load_questions, run_benchmark
from app.services.corpus_graph import get_article_graph
from app.services.corpus_updater import get_manifest, sync_corpus
from app.services.rag import get_corpus_stats, reindex_all_corpus
from app.services.templates import generate_document, list_templates

router = APIRouter(prefix="/api/corpus", tags=["corpus"])


class TemplateGenerateRequest(BaseModel):
    template_id: str
    fields: dict[str, str]


class BenchmarkRunRequest(BaseModel):
    limit: int | None = None


@router.get("/stats")
def corpus_stats():
    return get_corpus_stats()


@router.get("/graph")
def article_graph(article_id: str | None = None, instrument: str | None = None):
    return get_article_graph(article_id=article_id, instrument=instrument)


@router.get("/templates")
def templates_list():
    return {"templates": list_templates()}


@router.post("/templates/generate")
def templates_generate(body: TemplateGenerateRequest):
    result = generate_document(body.template_id, body.fields)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/benchmark/questions")
def benchmark_questions():
    return {"questions": load_questions(), "total": len(load_questions())}


@router.get("/benchmark/results")
def benchmark_results():
    results = get_last_results()
    if not results:
        return {"message": "Aucun benchmark exécuté", "results": None}
    return results


@router.post("/benchmark/run")
def benchmark_run(
    body: BenchmarkRunRequest | None = None,
    _user=Depends(require_roles(UserRole.ADMIN_WEBVOICE, UserRole.ADMIN_CABINET)),
):
    limit = body.limit if body else None
    return run_benchmark(limit=limit)


@router.get("/manifest")
def corpus_manifest():
    return get_manifest()


class CorpusSyncRequest(BaseModel):
    scale: str = "demo"
    rebuild: bool = False


@router.post("/sync")
def corpus_sync(
    body: CorpusSyncRequest | None = None,
    _user=Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
):
    scale = body.scale if body else "demo"
    rebuild = body.rebuild if body else False
    return sync_corpus(scale=scale, rebuild=rebuild)


@router.post("/reindex")
def corpus_reindex(
    _user=Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
):
    return reindex_all_corpus()
