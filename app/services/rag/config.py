from __future__ import annotations

import os
from pathlib import Path


class QdrantConfig:
    """Qdrant configuration from environment variables.

    All values are read lazily from the environment on every access,
    so they always reflect the current .env state regardless of import timing.
    """

    @classmethod
    def get_mode(cls) -> str:
        """Qdrant mode: 'memory' (local) or 'remote' (cloud/self-hosted)."""
        return os.getenv("QDRANT_MODE", "memory")

    @classmethod
    def get_url(cls) -> str | None:
        """Remote Qdrant URL (only used if mode=remote)."""
        return os.getenv("QDRANT_URL")

    @classmethod
    def get_api_key(cls) -> str | None:
        """Remote Qdrant API key (only used if mode=remote)."""
        return os.getenv("QDRANT_API_KEY")

    @classmethod
    def validate(cls) -> None:
        """Validate Qdrant configuration."""
        mode = cls.get_mode()
        if mode == "remote":
            url = cls.get_url()
            api_key = cls.get_api_key()
            if not url:
                raise ValueError("QDRANT_URL is required when QDRANT_MODE=remote")
            if not api_key:
                raise ValueError("QDRANT_API_KEY is required when QDRANT_MODE=remote")
            print(f"[QdrantConfig] Remote mode: {url}")
        else:
            print("[QdrantConfig] Local in-memory mode")


class RAGConfig:
    """RAG configuration from environment variables.

    All values are read lazily from the environment on every access.
    """

    @classmethod
    def get_embedding_model(cls) -> str:
        return os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    @classmethod
    def get_embedding_dimension(cls) -> int:
        return int(os.getenv("RAG_EMBEDDING_DIMENSION", "384"))

    @classmethod
    def get_reranker_model(cls) -> str:
        return os.getenv("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    @classmethod
    def get_chunk_size(cls) -> int:
        return int(os.getenv("RAG_CHUNK_SIZE", "512"))

    @classmethod
    def get_chunk_overlap(cls) -> int:
        return int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

    @classmethod
    def get_top_k_retrieval(cls) -> int:
        return int(os.getenv("RAG_TOP_K_RETRIEVAL", "5"))

    @classmethod
    def get_top_k_rerank(cls) -> int:
        return int(os.getenv("RAG_TOP_K_RERANK", "3"))

    @classmethod
    def get_snapshot_dir(cls) -> Path:
        return Path.home() / os.getenv("RAG_SNAPSHOT_DIR", ".claude/qdrant_snapshots")

    @classmethod
    def get_snapshot_interval(cls) -> int:
        return int(os.getenv("RAG_SNAPSHOT_INTERVAL", "100"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration."""
        snapshot_dir = cls.get_snapshot_dir()
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        print(f"[RAGConfig] embedding_model={cls.get_embedding_model()}, reranker={cls.get_reranker_model()}")
        print(f"[RAGConfig] chunk_size={cls.get_chunk_size()}, overlap={cls.get_chunk_overlap()}")
        print(f"[RAGConfig] top_k_retrieval={cls.get_top_k_retrieval()}, top_k_rerank={cls.get_top_k_rerank()}")
        QdrantConfig.validate()
