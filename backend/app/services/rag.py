from sqlalchemy.orm import Session

from app.services.retrieval import retrieve_context


def run_rag_pipeline(db: Session, question: str) -> dict:
    sources = retrieve_context(db, question)

    if not sources:
        return {
            "answer": "No indexed Netflix content is available yet. Load metadata and embeddings first.",
            "sources": [],
        }

    context_titles = ", ".join(item["title"] for item in sources)
    answer = (
        f"Based on related Netflix titles ({context_titles}), "
        f"the query '{question}' appears to align with similar themes in the retrieved context."
    )

    return {"answer": answer, "sources": sources}
