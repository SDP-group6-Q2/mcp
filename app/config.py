from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = "http://localhost:8000"
    api_timeout_seconds: float = 30

    # The manuals RAG lives in its own database on the shared Postgres instance (created on first ingest).
    rag_database_url: str = "postgresql://postgres:postgres@localhost:5432/rag"
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    model_cache_dir: str | None = None

    # Source of the manual PDFs for ingestion ("<serial>_manual_EN.pdf" in the bucket).
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    manuals_bucket: str = "manuals"

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 9000


settings = Settings()
