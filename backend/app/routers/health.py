from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine
from app.services.faiss_retrieval import faiss_store

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check() -> dict:
    db_ok = False
    faiss_ok = False

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        faiss_store.is_ready()
        faiss_ok = True
    except Exception:
        faiss_ok = False

    status = "ready" if db_ok and faiss_ok else "degraded"
    return {"status": status, "checks": {"db": db_ok, "faiss": faiss_ok}}
