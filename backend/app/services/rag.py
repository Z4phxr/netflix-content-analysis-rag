import time

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.llm import generate_answer
from app.services.retrieval import retrieve_context


async def run_rag_pipeline(db: Session, question: str, retrieval_mode: str = "auto") -> dict:
    started = time.perf_counter()
    sources, mode_used = await retrieve_context(db=db, question=question, mode=retrieval_mode)

    if not sources:
        return {
            "answer": "No indexed Netflix content is available yet. Load metadata and embeddings first.",
            "sources": [],
            "retrieval_mode_used": mode_used,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "model": settings.openai_chat_model,
        }

    answer = await generate_answer(question=question, sources=sources)

    return {
        "answer": answer,
        "sources": sources,
        "retrieval_mode_used": mode_used,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "model": settings.openai_chat_model,
    }
