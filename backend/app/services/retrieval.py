import logging

from sqlalchemy.orm import Session

from app.models.netflix_content import NetflixContent
from app.core.config import settings
from app.services.embeddings import cosine_similarity, generate_embedding_async
from app.services.faiss_retrieval import faiss_store

logger = logging.getLogger(__name__)

def determine_top_k(query: str) -> int:
    """Determine a dynamic top_k based on the user's query.

    Rules:
    - If query contains an explicit number (e.g. "list 10 movies") -> return min(number*2, 50)
    - If query contains any of ("list", "show", "give me") -> 10
    - If query contains "compare" -> 8
    - If query contains "similar" -> 10
    - Otherwise -> 5

    The returned value is clamped to a maximum of 50 and a minimum of 10.
    """
    if not query:
        return 10

    q = query.lower()

    # detect explicit number in query
    import re

    # explicit 'all' -> return max (50)
    if re.search(r"\ball\b", q):
        return 50

    m = re.search(r"\b(\d{1,3})\b", q)
    if m:
        try:
            n = int(m.group(1))
            val = min(n * 2, 50)
            return max(10, val)
        except ValueError:
            pass

    if any(w in q for w in ("list", "show", "give me")):
        return 10

    if "compare" in q:
        return 10

    if "similar" in q:
        return 10

    return 10


async def retrieve_context_db(db: Session, question: str, top_k: int | None = None) -> list[dict]:
    question_embedding = await generate_embedding_async(question)
    rows = db.query(NetflixContent).all()

    scored = []
    for row in rows:
        embedding = row.embedding
        if not embedding:
            continue
        score = cosine_similarity(question_embedding, embedding)
        scored.append(
            {
                "title": row.title,
                "description": row.description,
                "score": round(score, 4),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    # safety: clamp and default
    use_k = int(top_k) if top_k is not None else 10
    use_k = max(10, min(use_k, 50))
    return scored[:use_k]


async def retrieve_context_faiss(question: str, top_k: int | None = None) -> list[dict]:
    question_embedding = await generate_embedding_async(question)
    use_k = int(top_k) if top_k is not None else 10
    use_k = max(10, min(use_k, 50))
    return faiss_store.search(question_embedding=question_embedding, top_k=use_k)


async def retrieve_context(
    db: Session,
    question: str,
    mode: str = "auto",
    top_k: int | None = None,
) -> tuple[list[dict], str]:
    # Determine dynamic top_k when not explicitly provided
    selected_mode = (mode or settings.retrieval_default_mode).lower()
    if top_k is not None:
        selected_top_k = max(10, min(int(top_k), 50))
    else:
        selected_top_k = determine_top_k(question)

    if selected_mode == "db":
        return await retrieve_context_db(db=db, question=question, top_k=selected_top_k), "db"

    if selected_mode == "faiss":
        return await retrieve_context_faiss(question=question, top_k=selected_top_k), "faiss"

    # Production-safe default: use FAISS first for speed, then DB fallback.
    try:
        sources = await retrieve_context_faiss(question=question, top_k=selected_top_k)
        if sources:
            return sources, "faiss"
    except Exception as exc:
        logger.warning("FAISS retrieval unavailable, falling back to DB: %s", exc)

    return await retrieve_context_db(db=db, question=question, top_k=selected_top_k), "db"
