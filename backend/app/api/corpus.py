from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.api.deps import get_current_user, require_roles
from app.core.rate_limit import check_rate_limit
from app.models import User, UserRole
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
def corpus_stats(
    request: Request,
    _user: User = Depends(get_current_user),
):
    check_rate_limit(request, key="corpus.stats", limit=60, window_sec=60)
    return get_corpus_stats()


@router.get("/graph")
def article_graph(
    request: Request,
    article_id: str | None = None,
    instrument: str | None = None,
    _user: User = Depends(get_current_user),
):
    check_rate_limit(request, key="corpus.graph", limit=60, window_sec=60)
    return get_article_graph(article_id=article_id, instrument=instrument)


@router.get("/templates")
def templates_list(
    request: Request,
    _user: User = Depends(get_current_user),
):
    check_rate_limit(request, key="corpus.templates", limit=60, window_sec=60)
    return {"templates": list_templates()}


@router.post("/templates/generate")
def templates_generate(
    body: TemplateGenerateRequest,
    request: Request,
    _user: User = Depends(get_current_user),
):
    check_rate_limit(request, key="corpus.templates.generate", limit=20, window_sec=60)
    result = generate_document(body.template_id, body.fields)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/benchmark/questions")
def benchmark_questions(
    request: Request,
    _user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE, UserRole.ADMIN_CABINET)),
):
    check_rate_limit(request, key="corpus.benchmark.q", limit=30, window_sec=60)
    return {"questions": load_questions(), "total": len(load_questions())}


@router.get("/benchmark/results")
def benchmark_results(
    request: Request,
    _user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE, UserRole.ADMIN_CABINET)),
):
    check_rate_limit(request, key="corpus.benchmark.r", limit=30, window_sec=60)
    results = get_last_results()
    if not results:
        return {"message": "Aucun benchmark exécuté", "results": None}
    return results


@router.post("/benchmark/run")
def benchmark_run(
    request: Request,
    body: BenchmarkRunRequest | None = None,
    _user=Depends(require_roles(UserRole.ADMIN_WEBVOICE, UserRole.ADMIN_CABINET)),
):
    check_rate_limit(request, key="corpus.benchmark.run", limit=5, window_sec=60)
    limit = body.limit if body else None
    return run_benchmark(limit=limit)


@router.get("/manifest")
def corpus_manifest(
    request: Request,
    _user: User = Depends(get_current_user),
):
    check_rate_limit(request, key="corpus.manifest", limit=60, window_sec=60)
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
