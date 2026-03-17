import os


class Settings:
    app_name: str = "Netflix Content Analysis RAG API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@db:5432/netflix_rag",
    )


settings = Settings()
