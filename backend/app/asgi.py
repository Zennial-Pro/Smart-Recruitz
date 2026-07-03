"""ASGI entrypoint for Uvicorn."""

from app.main import create_app

app = create_app()
