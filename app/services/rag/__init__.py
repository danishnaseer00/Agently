"""
RAG (Retrieval-Augmented Generation) System

Modular RAG implementation with:
- Vector embeddings (Qdrant)
- Hybrid search (BM25 + semantic)
- Intelligent reranking (cross-encoder)
- Configurable parameters
"""

from __future__ import annotations

from app.services.rag.config import RAGConfig
from app.services.rag.vector_db import VectorStore
from app.services.rag.hybrid_search import HybridSearcher
from app.services.rag.reranker import Reranker
from app.services.rag.retrieval import RAGRetrieval, get_rag_retrieval

__all__ = [
    "RAGConfig",
    "VectorStore",
    "HybridSearcher",
    "Reranker",
    "RAGRetrieval",
    "get_rag_retrieval",
]
