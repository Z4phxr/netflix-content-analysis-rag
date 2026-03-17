from sqlalchemy.orm import Session

from app.models.netflix_content import NetflixContent
from app.services.embeddings import generate_embedding


def index_metadata(db: Session, items: list[dict]) -> int:
    for item in items:
        db.add(
            NetflixContent(
                title=item["title"],
                description=item["description"],
                genre=item.get("genre"),
                embedding=generate_embedding(item["description"]),
            )
        )

    db.commit()
    return len(items)
