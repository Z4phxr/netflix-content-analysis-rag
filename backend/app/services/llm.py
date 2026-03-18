from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def build_prompt(question: str, sources: list[dict]) -> list[dict]:
    context_lines = []
    for idx, source in enumerate(sources, start=1):
        context_lines.append(
            f"[{idx}] Title: {source['title']}\nDescription: {source['description']}\nScore: {source['score']}"
        )

    context_block = "\n\n".join(context_lines)

    system_msg = (
        "You are a Netflix catalog assistant. "
        "Answer using only the provided retrieved context. "
        "If context is insufficient, say so clearly and avoid hallucinations."
    )

    user_msg = (
        f"User question: {question}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        "Return a concise answer and mention relevant titles."
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


async def generate_answer(question: str, sources: list[dict]) -> str:
    messages = build_prompt(question=question, sources=sources)
    response = await _get_client().chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        temperature=0.2,
    )
    message = response.choices[0].message.content if response.choices else None
    return (message or "").strip() or "I could not generate an answer from the available context."
