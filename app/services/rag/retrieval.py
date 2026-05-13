from __future__ import annotations

import time
from app.services.rag.config import RAGConfig
from app.services.rag.vector_db import VectorStore
from app.services.rag.hybrid_search import HybridSearcher
from app.services.rag.reranker import Reranker


class RAGRetrieval:
    """Main RAG retrieval pipeline combining all components."""

    def __init__(self):
        """Initialize RAG components."""
        RAGConfig.validate()
        self.vector_store = VectorStore()
        self.hybrid_searcher = HybridSearcher()
        self.reranker = Reranker()
        print("[RAGRetrieval] Initialized all components")

    def index_document(
        self,
        collection_name: str,
        doc_id: str,
        chunks: list[str],
    ) -> None:
        """Index document chunks in both vector DB and BM25."""
        # Index in vector store
        self.vector_store.index_chunks(collection_name, chunks, doc_id)

        # Index in BM25
        self.hybrid_searcher.index_chunks_for_bm25(collection_name, chunks)

        print(f"[RAGRetrieval] Document {doc_id} indexed in collection {collection_name}")

    def retrieve(
        self,
        query: str,
        collection_name: str,
        doc_ids: list[str],
        top_k: int | None = None,
    ) -> list[str]:
        """
        Full retrieval pipeline: hybrid search + reranking.

        Returns top-k reranked chunks.
        """
        if top_k is None:
            top_k = RAGConfig.get_top_k_rerank()

        print(f"[RAGRetrieval] Starting retrieval for query: {query[:60]}...")
        print(f"[RAGRetrieval] Collection: {collection_name}, Doc IDs: {doc_ids}")

        # Step 1: Hybrid search with retry for background indexing
        chunks = self.hybrid_searcher.hybrid_search(
            self.vector_store,
            collection_name,
            query,
            doc_ids,
            top_k=RAGConfig.get_top_k_retrieval(),
        )

        # Retry once if no chunks found (background indexing may still be in progress)
        if not chunks:
            print("[RAGRetrieval] No chunks found on first attempt, waiting for background indexing...")
            time.sleep(1)
            chunks = self.hybrid_searcher.hybrid_search(
                self.vector_store,
                collection_name,
                query,
                doc_ids,
                top_k=RAGConfig.get_top_k_retrieval(),
            )

        if not chunks:
            print("[RAGRetrieval] No chunks found, returning empty list")
            return []

        # Step 2: Reranking
        reranked = self.reranker.rerank(query, chunks, top_k=top_k)

        print(f"[RAGRetrieval] Retrieved and reranked {len(reranked)} chunks")
        return reranked

    def format_context(self, chunks: list[str]) -> str:
        """Format chunks as context for the prompt."""
        if not chunks:
            return ""
        return "\n---\n".join(chunks)

    def delete_collection(self, collection_name: str) -> None:
        """Delete collection from vector store."""
        self.vector_store.delete_collection(collection_name)
        if collection_name in self.hybrid_searcher.bm25_index:
            del self.hybrid_searcher.bm25_index[collection_name]
        print(f"[RAGRetrieval] Deleted collection {collection_name}")


from functools import lru_cache

@lru_cache(maxsize=1)
def get_rag_retrieval() -> RAGRetrieval:
    """Get or create global RAG retrieval instance (singleton)."""
    return RAGRetrieval()
