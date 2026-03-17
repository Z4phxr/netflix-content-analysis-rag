from sqlalchemy import Column, Integer, String, Text, JSON

from app.db.base import Base


class NetflixContent(Base):
    __tablename__ = "netflix_content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    genre = Column(String(120), nullable=True)
    embedding = Column(JSON, nullable=True)
