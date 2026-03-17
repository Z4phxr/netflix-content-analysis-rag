from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rag import IndexRequest, IndexResponse, QueryRequest, QueryResponse
from app.services.indexing import index_metadata
from app.services.rag import run_rag_pipeline

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_rag(payload: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    result = run_rag_pipeline(db=db, question=payload.question)
    return QueryResponse(**result)


@router.post("/index", response_model=IndexResponse)
def index_netflix_content(payload: IndexRequest, db: Session = Depends(get_db)) -> IndexResponse:
    indexed = index_metadata(db=db, items=[item.model_dump() for item in payload.items])
    return IndexResponse(indexed_count=indexed)
