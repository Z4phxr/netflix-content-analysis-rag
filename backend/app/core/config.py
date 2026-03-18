import os


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
        return parsed if parsed > 0 else default
    except ValueError:
        return default


class Settings:
    app_name: str = "Netflix Content Analysis RAG API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@db:5432/netflix_rag",
    )
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    # Retrieval configuration
    retrieval_default_mode: str = os.getenv("RETRIEVAL_DEFAULT_MODE", "auto")
    # Default number of retrieved items to return for RAG queries
    retrieval_top_k: int = _get_int_env("RETRIEVAL_TOP_K", 20)
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "data/netflix.faiss")
    faiss_metadata_csv_path: str = os.getenv("FAISS_METADATA_CSV_PATH", "data/netflix_with_embeddings.csv")

    # Indexing configuration
    indexing_batch_size: int = _get_int_env("INDEXING_BATCH_SIZE", 100)

    # API safeguards
    rate_limit_query_per_minute: int = _get_int_env("RATE_LIMIT_QUERY_PER_MINUTE", 60)
    rate_limit_index_per_minute: int = _get_int_env("RATE_LIMIT_INDEX_PER_MINUTE", 10)
    rate_limit_build_per_minute: int = _get_int_env("RATE_LIMIT_BUILD_PER_MINUTE", 6)

    # Embedding retries
    embedding_max_retries: int = _get_int_env("EMBEDDING_MAX_RETRIES", 5)
    embedding_initial_backoff_seconds: float = _get_float_env("EMBEDDING_INITIAL_BACKOFF_SECONDS", 1.0)

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
