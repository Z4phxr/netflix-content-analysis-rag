import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.db.session import engine
from app.db.base import Base
from app.routers import health, rag

app = FastAPI(title="Netflix Content Analysis RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    max_attempts = 15
    delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
