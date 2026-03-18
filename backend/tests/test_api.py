import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_query_endpoint_with_mode(monkeypatch):
    async def fake_pipeline(db, question, retrieval_mode):
        return {
            "answer": f"stub:{question}",
            "sources": [
                {
                    "title": "Title 1",
                    "description": "Description",
                    "score": 0.99,
                }
            ],
            "retrieval_mode_used": "faiss" if retrieval_mode == "auto" else retrieval_mode,
            "latency_ms": 12.3,
            "model": "gpt-4o-mini",
        }

    import app.routers.rag as rag_router

    monkeypatch.setattr(rag_router, "run_rag_pipeline", fake_pipeline)

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "best sci-fi", "retrieval_mode": "auto"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_mode_used"] in ["db", "faiss"]
    assert len(payload["sources"]) == 1
    assert payload["latency_ms"] == 12.3
    assert payload["model"] == "gpt-4o-mini"


def test_index_accepts_precomputed_embeddings(monkeypatch):
    async def fake_index(db, items):
        assert items[0]["embedding"] == [0.1, 0.2, 0.3]
        return {
            "indexed_count": len(items),
            "failed_count": 0,
            "total_received": len(items),
            "failed_items": [],
        }

    import app.routers.rag as rag_router

    monkeypatch.setattr(rag_router, "index_metadata", fake_index)

    response = client.post(
        "/api/v1/rag/index",
        json={
            "items": [
                {
                    "title": "Movie A",
                    "description": "Space adventure",
                    "embedding": [0.1, 0.2, 0.3],
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["indexed_count"] == 1
    assert response.json()["failed_count"] == 0


def test_index_partial_failure_report(monkeypatch):
    async def fake_index(db, items):
        return {
            "indexed_count": 1,
            "failed_count": 1,
            "total_received": 2,
            "failed_items": [{"index": 1, "reason": "missing title"}],
        }

    import app.routers.rag as rag_router

    monkeypatch.setattr(rag_router, "index_metadata", fake_index)

    response = client.post(
        "/api/v1/rag/index",
        json={
            "items": [
                {"title": "Movie A", "description": "Space adventure"},
                {"title": "Movie B", "description": "Drama"},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["indexed_count"] == 1
    assert payload["failed_count"] == 1
    assert payload["total_received"] == 2
    assert payload["failed_items"][0]["index"] == 1
