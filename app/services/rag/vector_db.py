from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.services.rag.config import RAGConfig, QdrantConfig
from app.services.document_service import embed_texts


class VectorStore:
    """Vector database wrapper using Qdrant (local or remote)."""

    def __init__(self):
        """Initialize Qdrant client based on configuration."""
        self.config = QdrantConfig
        self.snapshot_dir = RAGConfig.SNAPSHOT_DIR
        self.collection_count = 0

        # Initialize Qdrant client
        if self.config.MODE == "remote":
            print(f"[VectorStore] Connecting to remote Qdrant: {self.config.URL}")
            self.client = QdrantClient(
                url=self.config.URL,
                api_key=self.config.API_KEY,
            )
        else:
            print("[VectorStore] Using local in-memory Qdrant")
            self.client = QdrantClient(":memory:")

    def get_or_create_collection(self, collection_name: str) -> None:
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(collection_name)
            print(f"[VectorStore] Collection exists: {collection_name}")
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=RAGConfig.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            print(f"[VectorStore] Created collection: {collection_name}")

    def index_chunks(
        self,
        collection_name: str,
        chunks: list[str],
        doc_id: str,
        start_idx: int = 0,
    ) -> None:
        """Index document chunks with embeddings."""
        self.get_or_create_collection(collection_name)

        print(f"[VectorStore] Generating embeddings for {len(chunks)} chunks...")
        embeddings = embed_texts(chunks)

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = hash(f"{doc_id}:{i}") & 0x7FFFFFFF
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "doc_id": doc_id,
                        "chunk_index": start_idx + i,
                        "content": chunk,
                    },
                )
            )

        self.client.upsert(collection_name=collection_name, points=points)
        self.collection_count += len(points)

        print(f"[VectorStore] Indexed {len(points)} chunks in collection: {collection_name}")

        # Save snapshot periodically (only for local mode)
        if self.config.MODE == "memory" and self.collection_count % RAGConfig.SNAPSHOT_INTERVAL == 0:
            self._save_snapshot(collection_name)

    def semantic_search(
        self,
        collection_name: str,
        query: str,
        doc_ids: list[str] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Semantic vector search."""
        try:
            query_vector = embed_texts([query])[0]

            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k * 2,
            )

            results = []
            for hit in search_result:
                if doc_ids is None or hit.payload.get("doc_id") in doc_ids:
                    results.append(
                        {
                            "content": hit.payload.get("content", ""),
                            "doc_id": hit.payload.get("doc_id"),
                            "chunk_index": hit.payload.get("chunk_index"),
                            "score": hit.score,
                            "type": "semantic",
                        }
                    )
                    if len(results) >= top_k:
                        break

            print(f"[VectorStore] Semantic search returned {len(results)} results")
            return results
        except Exception as exc:
            print(f"[VectorStore] Semantic search error: {exc}")
            return []

    def delete_collection(self, collection_name: str) -> None:
        """Delete entire collection."""
        try:
            self.client.delete_collection(collection_name)
            print(f"[VectorStore] Deleted collection: {collection_name}")
        except Exception as exc:
            print(f"[VectorStore] Delete collection error: {exc}")

    def _save_snapshot(self, collection_name: str) -> None:
        """Save snapshot of collection to disk (local mode only)."""
        if self.config.MODE != "memory":
            return

        try:
            snapshot_path = self.snapshot_dir / f"{collection_name}.snapshot"
            self.client.snapshot(
                collection_name=collection_name,
                snapshot_path=snapshot_path,
            )
            print(f"[VectorStore] Saved snapshot: {snapshot_path}")
        except Exception as exc:
            print(f"[VectorStore] Snapshot save error: {exc}")

    def _load_snapshot(self, collection_name: str) -> None:
        """Load snapshot from disk if it exists (local mode only)."""
        if self.config.MODE != "memory":
            return

        try:
            snapshot_path = self.snapshot_dir / f"{collection_name}.snapshot"
            if snapshot_path.exists():
                self.client.recover(
                    collection_name=collection_name,
                    snapshot_path=snapshot_path,
                )
                print(f"[VectorStore] Loaded snapshot: {snapshot_path}")
        except Exception as exc:
            print(f"[VectorStore] Snapshot load error: {exc}")
