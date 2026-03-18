from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.db.base import Base


class IndexJob(Base):
    __tablename__ = "index_jobs"

    id = Column(String(64), primary_key=True, index=True)
    status = Column(String(32), nullable=False, index=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    return_code = Column(Integer, nullable=True)
