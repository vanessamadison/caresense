"""Configuration management for CareSense."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Centralised application settings."""

    environment: str = "local"
    api_title: str = "CareSense Secure Triage API"
    api_version: str = "0.2.0"

    audit_log_path: Path = BASE_DIR / "data" / "audit_logs.jsonl"
    encrypted_storage_dir: Path = BASE_DIR / "data" / "encrypted"

    biometric_fhe_context: Path = BASE_DIR / "data" / "crypto" / "fhe_context.bin"
    biometric_fhe_secret: Path = BASE_DIR / "data" / "crypto" / "fhe_secret.bin"
    enable_fhe: bool = False

    workflow_queue_dir: Path = BASE_DIR / "data" / "queues"

    model_path: Path = BASE_DIR / "models" / "caresense_model.pkl"

    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"

    post_quantum_kem: str = "kyber768"
    audit_signing_algorithm: str = "ed25519"

    security_contact: Optional[str] = "mailto:security@caresense.app"

    model_config = {
        "env_prefix": "CARESENSE_",
        "case_sensitive": False,
    }

    def cors_origins(self) -> list[str]:
        raw_value = os.getenv(
            "CARESENSE_ALLOW_ORIGINS",
            "http://localhost:3000,http://localhost:5173,https://caresense.app",
        )
        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    settings.encrypted_storage_dir.mkdir(parents=True, exist_ok=True)
    settings.workflow_queue_dir.mkdir(parents=True, exist_ok=True)
    return settings
