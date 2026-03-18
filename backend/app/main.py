import time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.logging import configure_logging
from app.core.observability import metrics_middleware, metrics_router
from app.db.session import engine
from app.db.base import Base
from app.routers import health, rag
from app.services.faiss_retrieval import faiss_store

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Netflix Content Analysis RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)


@app.on_event("startup")
def on_startup() -> None:
    # Import models here so SQLAlchemy metadata is registered before create_all.
    import app.models  # noqa: F401

    max_attempts = 15
    delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            Base.metadata.create_all(bind=engine)
            try:
                faiss_store.is_ready()
                logger.info("FAISS artifacts loaded and ready")
            except Exception as exc:
                logger.warning("FAISS preload skipped: %s", exc)
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(metrics_router, prefix="/api/v1", tags=["metrics"])
