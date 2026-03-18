from typing import Any, List
from sqlalchemy.orm import Session

from app.models.netflix_content import NetflixContent
from app.core.config import settings
from app.services.embeddings import batch_generate_embeddings_async


def _to_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_embedding(value: Any) -> list[float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        return None
    try:
        parsed = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    return parsed if parsed else None


async def index_metadata(db: Session, items: List[dict]) -> dict:
    """Index a list of metadata items into the PostgreSQL table.

    Each item can include title, description/content, genre (optional), and precomputed embedding (optional).
    Missing embeddings are generated in async batches.
    """
    if not items:
        return {
            "indexed_count": 0,
            "failed_count": 0,
            "total_received": 0,
            "failed_items": [],
        }

    normalized_rows: list[dict] = []
    failed_items: list[dict] = []
    missing_embedding_texts: list[str] = []
    missing_embedding_positions: list[int] = []

    for idx, item in enumerate(items):
        try:
            title = _to_text(item.get("title"))
            description = _to_text(item.get("description"))
            content = _to_text(item.get("content"))
            source_text = content or description
            if not title:
                raise ValueError("missing title")
            if not source_text:
                raise ValueError("missing description/content")

            row = {
                "title": title,
                "description": description or source_text,
                "genre": _to_text(item.get("genre")) or None,
                "embedding": _normalize_embedding(item.get("embedding")),
                "source_text": source_text,
            }
            if row["embedding"] is None:
                missing_embedding_positions.append(len(normalized_rows))
                missing_embedding_texts.append(source_text)

            normalized_rows.append(row)
        except Exception as exc:
            failed_items.append({"index": idx, "reason": str(exc)})
            continue

    if missing_embedding_texts:
        generated = await batch_generate_embeddings_async(
            texts=missing_embedding_texts,
            batch_size=settings.indexing_batch_size,
        )
        for generated_idx, row_pos in enumerate(missing_embedding_positions):
            normalized_rows[row_pos]["embedding"] = generated[generated_idx]

    for row in normalized_rows:
        db.add(
            NetflixContent(
                title=row["title"],
                description=row["description"],
                genre=row["genre"],
                embedding=row["embedding"],
            )
        )

    db.commit()
    return {
        "indexed_count": len(normalized_rows),
        "failed_count": len(failed_items),
        "total_received": len(items),
        "failed_items": failed_items,
    }
