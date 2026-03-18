from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.schemas.rag import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    BuildRequest,
    BuildResponse,
    JobStatusResponse,
)
from app.services.indexing import index_metadata
from app.services.build_manager import start_build, get_status
from app.services.rag import run_rag_pipeline

router = APIRouter()


def enforce_query_rate_limit(request: Request) -> None:
    rate_limiter.enforce(
        request=request,
        route_key="rag_query",
        max_per_minute=settings.rate_limit_query_per_minute,
    )


def enforce_index_rate_limit(request: Request) -> None:
    rate_limiter.enforce(
        request=request,
        route_key="rag_index",
        max_per_minute=settings.rate_limit_index_per_minute,
    )


def enforce_build_rate_limit(request: Request) -> None:
    rate_limiter.enforce(
        request=request,
        route_key="rag_build",
        max_per_minute=settings.rate_limit_build_per_minute,
    )


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_query_rate_limit),
) -> QueryResponse:
    result = await run_rag_pipeline(
        db=db,
        question=payload.question,
        retrieval_mode=payload.retrieval_mode,
    )
    return QueryResponse(**result)


@router.post("/index", response_model=IndexResponse)
async def index_netflix_content(
    payload: IndexRequest,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_index_rate_limit),
) -> IndexResponse:
    report = await index_metadata(db=db, items=[item.model_dump() for item in payload.items])
    return IndexResponse(**report)


@router.post("/build", response_model=BuildResponse)
def build_embeddings_endpoint(
    payload: BuildRequest,
    _: None = Depends(enforce_build_rate_limit),
):
    job_id = start_build(payload.input, payload.out_csv, payload.faiss_out, payload.batch)
    return BuildResponse(job_id=job_id, status="started")


@router.get("/build/{job_id}", response_model=JobStatusResponse)
def build_status(job_id: str):
    info = get_status(job_id)
    return JobStatusResponse(job_id=job_id, status=info.get("status"), detail=info.get("detail"))
