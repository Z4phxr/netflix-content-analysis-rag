from sqlalchemy.orm import Session

from app.models.netflix_content import NetflixContent
from app.services.embeddings import cosine_similarity, generate_embedding


def retrieve_context(db: Session, question: str, top_k: int = 3) -> list[dict]:
    question_embedding = generate_embedding(question)
    rows = db.query(NetflixContent).all()

    scored = []
    for row in rows:
        embedding = row.embedding or generate_embedding(row.description)
        score = cosine_similarity(question_embedding, embedding)
        scored.append(
            {
                "title": row.title,
                "description": row.description,
                "score": round(score, 4),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
