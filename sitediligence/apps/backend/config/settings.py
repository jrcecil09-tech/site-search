"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "SiteDiligence API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",  # Expo
    ]

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./sitediligence.db"

    # ── Redis / Celery ────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── Storage ───────────────────────────────────────────────────────────────
    storage_backend: Literal["local", "s3", "azure", "gcs", "hosted"] = "local"
    storage_local_path: str = "./data/storage"

    # S3 / Compatible
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str = ""

    # Azure
    azure_storage_connection_string: str = ""
    azure_storage_container: str = ""

    # GCS
    gcs_bucket: str = ""
    gcs_credentials_file: str = ""

    # Hosted service
    hosted_api_url: str = ""
    hosted_api_key: str = ""

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # ── Billing ───────────────────────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""
    stripe_price_id_enterprise: str = ""

    # ── External APIs ─────────────────────────────────────────────────────────
    procore_client_id: str = ""
    procore_client_secret: str = ""
    autodesk_client_id: str = ""
    autodesk_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    dropbox_app_key: str = ""
    dropbox_app_secret: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
