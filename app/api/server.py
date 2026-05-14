from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load .env immediately at module import
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

from fastapi import FastAPI

from app.api.deps import get_settings
from app.api.middleware import setup_cors, setup_logging
from app.api.routes import health, conversations, documents, images, chat, tools
from app.services.rag.config import RAGConfig

app = FastAPI(title="ReAct Agent API", version="0.1.0")

# Middleware stack (order matters: CORS first, logging second)
settings = get_settings()
extra_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins else None
setup_cors(app, extra_origins=extra_origins)
setup_logging(app)

# Register routers
app.include_router(health.router)
app.include_router(tools.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(images.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup():
    get_settings()  # Load .env file
    RAGConfig.validate()  # Validate Qdrant configuration
