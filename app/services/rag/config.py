from __future__ import annotations

import os
from pathlib import Path


class QdrantConfig:
    """Qdrant configuration from environment variables."""

    # Mode: "memory" (local) or "remote" (cloud/self-hosted)
    MODE: str = os.getenv("QDRANT_MODE", "memory")

    # Remote settings (only used if MODE=remote)
    URL: str | None = os.getenv("QDRANT_URL")
    API_KEY: str | None = os.getenv("QDRANT_API_KEY")

    @classmethod
    def validate(cls) -> None:
        """Validate Qdrant configuration."""
        if cls.MODE == "remote":
            if not cls.URL:
                raise ValueError("QDRANT_URL is required when QDRANT_MODE=remote")
            if not cls.API_KEY:
                raise ValueError("QDRANT_API_KEY is required when QDRANT_MODE=remote")
            print(f"[QdrantConfig] Remote mode: {cls.URL}")
        else:
            print("[QdrantConfig] Local in-memory mode")


class RAGConfig:
    """RAG configuration from environment variables."""

    # Embedding model
    EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("RAG_EMBEDDING_DIMENSION", "384"))

    # Reranker model
    RERANKER_MODEL: str = os.getenv("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Chunking settings
    CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

    # Retrieval settings
    TOP_K_RETRIEVAL: int = int(os.getenv("RAG_TOP_K_RETRIEVAL", "5"))
    TOP_K_RERANK: int = int(os.getenv("RAG_TOP_K_RERANK", "3"))

    # Snapshot settings
    SNAPSHOT_DIR: Path = Path.home() / os.getenv("RAG_SNAPSHOT_DIR", ".claude/qdrant_snapshots")
    SNAPSHOT_INTERVAL: int = int(os.getenv("RAG_SNAPSHOT_INTERVAL", "100"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        cls.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[RAGConfig] embedding_model={cls.EMBEDDING_MODEL}, reranker={cls.RERANKER_MODEL}")
        print(f"[RAGConfig] chunk_size={cls.CHUNK_SIZE}, overlap={cls.CHUNK_OVERLAP}")
        print(f"[RAGConfig] top_k_retrieval={cls.TOP_K_RETRIEVAL}, top_k_rerank={cls.TOP_K_RERANK}")
        QdrantConfig.validate()
