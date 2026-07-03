"""SmartRecruitz FastAPI Application Factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="SmartRecruitz API",
        description="Verified Talent Infrastructure Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS — accepts localhost, ngrok, cloudflare tunnel, vercel, plus any explicit origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup() -> None:
        # Ensure upload directories exist
        base = Path(settings.local_storage_path)
        for sub in ("resumes", "id_documents"):
            (base / sub).mkdir(parents=True, exist_ok=True)

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app
