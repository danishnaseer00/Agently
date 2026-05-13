from __future__ import annotations

from app.services.rag.config import RAGConfig


class Reranker:
    """Cross-encoder for reranking search results."""

    def __init__(self):
        """Initialize reranker model."""
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(RAGConfig.get_reranker_model())
            print(f"[Reranker] Loaded model: {RAGConfig.get_reranker_model()}")
        except ImportError:
            print("[Reranker] CrossEncoder not available, reranking disabled")
            self.model = None
        except Exception as exc:
            print(f"[Reranker] Error loading model: {exc}")
            self.model = None

    def rerank(self, query: str, documents: list[str], top_k: int | None = None) -> list[str]:
        """Rerank documents by relevance to query."""
        if not self.model or not documents:
            return documents[: top_k or RAGConfig.get_top_k_rerank()]

        if top_k is None:
            top_k = RAGConfig.get_top_k_rerank()

        try:
            print(f"[Reranker] Reranking {len(documents)} documents...")

            # Score pairs
            pairs = [[query, doc] for doc in documents]
            scores = self.model.predict(pairs)

            # Rank
            ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
            final_results = [doc for doc, _ in ranked[:top_k]]

            print(f"[Reranker] Reranking complete, returning top {len(final_results)} results")
            return final_results
        except Exception as exc:
            print(f"[Reranker] Error during reranking: {exc}")
            return documents[:top_k]
