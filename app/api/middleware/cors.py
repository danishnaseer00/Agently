from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, extra_origins: list[str] | None = None) -> None:
    """Configure CORS middleware.

    Args:
        app: FastAPI application instance.
        extra_origins: Additional origins to allow (e.g. production frontend URLs).
            These are merged with localhost development origins.
    """
    local_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]
    origins = local_origins + (extra_origins or [])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
