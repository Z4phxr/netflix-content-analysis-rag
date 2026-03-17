from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


class SourceDocument(BaseModel):
    title: str
    description: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]


class IndexItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    genre: str | None = Field(default=None, max_length=120)


class IndexRequest(BaseModel):
    items: list[IndexItem]


class IndexResponse(BaseModel):
    indexed_count: int
