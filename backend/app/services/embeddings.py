import os
import time
import asyncio
import random
from typing import Iterable, List, Sequence, Union

import numpy as np
from openai import AsyncOpenAI, OpenAI

from app.core.config import settings

_sync_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def _ensure_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    os.environ.setdefault("OPENAI_API_KEY", api_key)
    return api_key


def _get_sync_client() -> OpenAI:
    global _sync_client
    if _sync_client is None:
        _ensure_api_key()
        _sync_client = OpenAI()
    return _sync_client


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _ensure_api_key()
        _async_client = AsyncOpenAI()
    return _async_client


def _normalize_text(text: str) -> str:
    if text is None:
        return ""
    return str(text).strip()


def _validate_texts(texts: Iterable[str]) -> list[str]:
    normalized = [_normalize_text(item) for item in texts]
    if not normalized:
        raise ValueError("No texts provided for embedding generation")
    if any(not text for text in normalized):
        raise ValueError("Empty text values are not allowed for embedding generation")
    return normalized


async def _with_retry(coro_factory):
    max_retries = settings.embedding_max_retries
    backoff = settings.embedding_initial_backoff_seconds
    for attempt in range(1, max_retries + 1):
        try:
            return await coro_factory()
        except Exception as exc:
            if attempt == max_retries:
                raise RuntimeError(f"embedding request failed after {max_retries} attempts: {exc}") from exc
            jitter = random.uniform(0.0, 0.25)
            await asyncio.sleep(backoff + jitter)
            backoff *= 2


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Generate embedding for a single text string using OpenAI.

    Raises RuntimeError on repeated failures.
    """
    model = model or settings.openai_embedding_model
    text = _normalize_text(text)
    if not text:
        raise ValueError("Text must be non-empty for embedding generation")

    max_retries = settings.embedding_max_retries
    backoff = settings.embedding_initial_backoff_seconds
    for attempt in range(1, max_retries + 1):
        try:
            resp = _get_sync_client().embeddings.create(model=model, input=text)
            return resp.data[0].embedding
        except Exception as exc:
            if attempt == max_retries:
                raise RuntimeError(f"embedding request failed: {exc}") from exc
            time.sleep(backoff)
            backoff *= 2


async def generate_embedding_async(text: str, model: str | None = None) -> List[float]:
    model = model or settings.openai_embedding_model
    normalized = _normalize_text(text)
    if not normalized:
        raise ValueError("Text must be non-empty for embedding generation")

    response = await _with_retry(
        lambda: _get_async_client().embeddings.create(model=model, input=normalized)
    )
    return response.data[0].embedding


async def batch_generate_embeddings_async(
    texts: Sequence[str],
    model: str | None = None,
    batch_size: int = 100,
    concurrency: int = 4,
) -> List[List[float]]:
    model = model or settings.openai_embedding_model
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    if concurrency <= 0:
        raise ValueError("concurrency must be > 0")

    normalized = _validate_texts(texts)
    indexed_batches = [
        (start, normalized[start : start + batch_size])
        for start in range(0, len(normalized), batch_size)
    ]
    semaphore = asyncio.Semaphore(concurrency)
    results: list[tuple[int, list[list[float]]]] = []

    async def run_batch(start: int, batch_texts: list[str]) -> tuple[int, list[list[float]]]:
        async with semaphore:
            response = await _with_retry(
                lambda: _get_async_client().embeddings.create(model=model, input=batch_texts)
            )
            return start, [item.embedding for item in response.data]

    tasks = [run_batch(start, batch) for start, batch in indexed_batches]
    for start, embeddings in await asyncio.gather(*tasks):
        results.append((start, embeddings))

    results.sort(key=lambda item: item[0])
    flattened: list[list[float]] = []
    for _, vectors in results:
        flattened.extend(vectors)
    return flattened


def batch_generate_embeddings(
    texts: List[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    pause: float = 0.0,
) -> List[List[float]]:
    """Generate embeddings for a list of texts in batches.

    Returns a list of embedding vectors in the same order as `texts`.
    """
    embeddings = asyncio.run(
        batch_generate_embeddings_async(
            texts=texts,
            model=model,
            batch_size=batch_size,
        )
    )
    if pause > 0:
        time.sleep(pause)
    return embeddings


def cosine_similarity(a: Union[List[float], np.ndarray], b: Union[List[float], np.ndarray]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    if a_arr.size == 0 or b_arr.size == 0 or a_arr.shape != b_arr.shape:
        return 0.0
    dot = float(np.dot(a_arr, b_arr))
    na = float(np.linalg.norm(a_arr))
    nb = float(np.linalg.norm(b_arr))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


__all__ = [
    "generate_embedding",
    "generate_embedding_async",
    "batch_generate_embeddings",
    "batch_generate_embeddings_async",
    "cosine_similarity",
]