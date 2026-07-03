"""Application settings driven by environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SmartRecruitz application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "SmartRecruitz"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://sr_user:sr_password@localhost:5432/smartrecruitz"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 60
    openai_max_retries: int = 3

    # Coresignal (LinkedIn profile lookup for cross-check)
    coresignal_api_key: SecretStr = SecretStr("")
    coresignal_base_url: str = "https://api.coresignal.com/cdapi/v2"
    coresignal_timeout_seconds: int = 30

    # Zingaro / CallWhiz voice-agent platform (outbound interview calls).
    # The prebuilt interview agent is reused for every call; per-candidate
    # questions are injected at call time via the pre-call webhook.
    zingaro_api_key: SecretStr = SecretStr("")  # cw_live_... API key (sent as X-API-Key)
    zingaro_base_url: str = "https://api.zingaro.ai"
    zingaro_agent_id: str = ""  # id of the prebuilt interview voice agent
    zingaro_caller_did: str = ""  # optional caller phone number (from GET /v1/phone-numbers)
    zingaro_webhook_secret: SecretStr = SecretStr("sr-dev-zingaro-secret-change-me")
    zingaro_timeout_seconds: int = 30
    zingaro_max_retries: int = 2
    # SmartRecruitz's externally reachable base URL, used to build the webhook_url
    # passed to Zingaro (ngrok / cloudflare tunnel in dev).
    public_base_url: str = "http://localhost:8000"

    # File Storage
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: Path = Path("./uploads")
    s3_bucket_name: str = ""
    s3_region: str = ""

    # Security
    api_key_secret: SecretStr = SecretStr("change-me")
    field_encryption_key: SecretStr = SecretStr("")

    # Standalone auth (SmartRecruitz's own login — hiring managers / admins)
    jwt_secret: SecretStr = SecretStr("sr-auth-dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12  # 12 hours

    # Google OAuth sign-in (same model as the LMS login)
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    # Where to send the user after a successful Google login (the frontend).
    frontend_url: str = "http://localhost:3002"

    # LMS integration — shared HS256 secret used to validate the short-lived
    # access tokens the LMS mints for the ported chatbot / hiring-manager iframe.
    sr_integration_secret: SecretStr = SecretStr("sr-dev-shared-secret-change-me")
    # Outbound approval webhook back into the LMS.
    lms_webhook_url: str = "http://localhost:2050/api/v1/recruitment/webhook"
    lms_webhook_secret: SecretStr = SecretStr("sr-dev-webhook-secret-change-me")

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 1000

    # CORS
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        r"|^https?://[\w-]+\.(ngrok-free\.app|ngrok\.io|ngrok\.dev|trycloudflare\.com|loca\.lt|vercel\.app)$"
    )

    # Feature Flags
    feature_lms_integration: bool = False
    feature_ats_push: bool = False
    feature_webhook_outbound: bool = False
    # Voice-call interview (Zingaro) replaces the in-browser video interview.
    feature_voice_interview: bool = True

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
