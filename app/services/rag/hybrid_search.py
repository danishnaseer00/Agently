from __future__ import annotations

from rank_bm25 import BM25Okapi

from app.services.rag.config import RAGConfig
from app.services.rag.vector_db import VectorStore


class HybridSearcher:
    """Hybrid search combining BM25 keyword search and semantic vector search."""

    def __init__(self):
        """Initialize hybrid searcher."""
        self.bm25_index = {}  # Map of collection_name -> BM25 data

    def index_chunks_for_bm25(self, collection_name: str, chunks: list[str]) -> None:
        """Build BM25 index for chunks."""
        existing = self.bm25_index.get(collection_name, {})
        existing_chunks = existing.get("chunks", [])
        all_chunks = existing_chunks + chunks
        tokenized = [chunk.lower().split() for chunk in all_chunks]
        self.bm25_index[collection_name] = {
            "model": BM25Okapi(tokenized),
            "chunks": all_chunks,
        }
        print(f"[HybridSearcher] Indexed {len(chunks)} new chunks ({len(all_chunks)} total) for BM25 in {collection_name}")

    def bm25_search(self, collection_name: str, query: str, top_k: int = 10) -> list[dict]:
        """BM25 keyword search."""
        if collection_name not in self.bm25_index:
            return []

        bm25_data = self.bm25_index[collection_name]
        model = bm25_data["model"]
        chunks = bm25_data["chunks"]

        query_tokens = query.lower().split()
        scores = model.get_scores(query_tokens)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in ranked:
            results.append(
                {
                    "content": chunks[idx],
                    "chunk_index": idx,
                    "score": float(score),
                    "type": "bm25",
                }
            )

        print(f"[HybridSearcher] BM25 search returned {len(results)} results")
        return results

    def hybrid_search(
        self,
        vector_store: VectorStore,
        collection_name: str,
        query: str,
        doc_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[str]:
        """
        Hybrid search combining BM25 and semantic search.

        Returns top-k chunk contents.
        """
        if top_k is None:
            top_k = RAGConfig.TOP_K_RETRIEVAL

        print(f"[HybridSearcher] Starting hybrid search for query: {query[:50]}...")
        print(f"[HybridSearcher] Filtering by doc_ids: {doc_ids}")

        # Get results from both methods
        semantic_results = vector_store.semantic_search(
            collection_name, query, doc_ids, top_k=top_k
        )
        bm25_results = self.bm25_search(collection_name, query, top_k=top_k)

        # Merge results with weighted scoring
        merged = {}
        for result in semantic_results:
            content = result["content"]
            merged[content] = merged.get(content, 0) + result["score"]

        for result in bm25_results:
            content = result["content"]
            normalized_score = min(result["score"] / 10, 1.0)
            merged[content] = merged.get(content, 0) + normalized_score

        # Sort by combined score
        sorted_results = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        final_results = [content for content, _ in sorted_results[:top_k]]

        print(f"[HybridSearcher] Hybrid search returned {len(final_results)} results")
        return final_results
