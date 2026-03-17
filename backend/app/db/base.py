from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Ensure models are imported so metadata is registered.
from app.models.netflix_content import NetflixContent  # noqa: E402,F401
