from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "RAG Agent Platform"
    app_env: str = "development"
    debug: bool = True

    # Database - REQUIRED: No default, must be set via environment
    database_url: str

    # LiteLLM
    litellm_api_url: str = "http://localhost:4000"
    litellm_api_key: str = ""

    # JWT - REQUIRED: No default, must be set via environment
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key is secure."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        if v == "your-secret-key-min-32-chars-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be changed from the example value")
        return v

    # CORS
    cors_origins: str | list[str] = "http://localhost:5173,http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle JSON format
            if v.startswith("["):
                import json
                return json.loads(v)
            # Handle comma-separated format
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    # OpenTelemetry
    otel_enabled: bool = False  # Enable when OTEL Collector is running
    otel_service_name: str = "rag-agent-backend"
    otel_exporter_endpoint: str = "http://localhost:4317"  # OTLP gRPC
    otel_log_level: str = "INFO"
    otel_metrics_export_interval_ms: int = 60000  # 60 seconds

    # Redis (for rate limiting, shared with LiteLLM)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Storage
    storage_type: str = "local"
    storage_local_path: str = "./uploads"

    # Static files (frontend)
    static_files_path: str = "./static"
    serve_static_files: bool = False

    # Embedding (via LiteLLM)
    embedding_model: str = "text-embedding-004"
    embedding_dimension: int = 768

    # MinIO Storage
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "ragagent-images"
    minio_secure: bool = True

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
