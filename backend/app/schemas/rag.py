from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    retrieval_mode: Literal["auto", "db", "faiss"] = Field(
        default="auto",
        description="Select retrieval backend. auto prefers FAISS and falls back to DB.",
    )


class SourceDocument(BaseModel):
    title: str
    description: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    retrieval_mode_used: Literal["db", "faiss"]
    latency_ms: float
    model: str


class IndexItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    content: str | None = Field(default=None)
    genre: str | None = Field(default=None, max_length=120)
    embedding: list[float] | None = Field(
        default=None,
        description="Optional precomputed embedding vector.",
    )

    @model_validator(mode="after")
    def validate_text_source(self):
        description = (self.description or "").strip()
        content = (self.content or "").strip()
        if not description and not content:
            raise ValueError("Either description or content must be provided")
        if self.embedding is not None and len(self.embedding) == 0:
            raise ValueError("embedding cannot be empty when provided")
        return self


class IndexRequest(BaseModel):
    items: list[IndexItem]


class IndexResponse(BaseModel):
    indexed_count: int
    failed_count: int = 0
    total_received: int = 0
    failed_items: list[dict] = Field(default_factory=list)


class BuildRequest(BaseModel):
    input: str = Field(..., description="Path to input CSV with 'content' column")
    out_csv: str = Field(..., description="Path to output CSV with embeddings")
    faiss_out: str = Field(..., description="Path to output FAISS index file")
    batch: int = Field(100, description="Batch size for embedding requests")


class BuildResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    detail: str | None = None
