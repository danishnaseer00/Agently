from __future__ import annotations

from pathlib import Path
import hashlib
import warnings

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.services.rag.config import RAGConfig, QdrantConfig
from app.services.document_service import embed_texts


class VectorStore:
    """Vector database wrapper using Qdrant (local or remote)."""

    def __init__(self):
        """Initialize Qdrant client based on configuration."""
        self.config = QdrantConfig
        self.snapshot_dir = RAGConfig.get_snapshot_dir()
        self.collection_count = 0

        # Initialize Qdrant client
        if self.config.get_mode() == "remote":
            print(f"[VectorStore] Connecting to remote Qdrant: {self.config.get_url()}")
            # Suppress version mismatch warnings on older clients
            warnings.filterwarnings("ignore", message=".*Qdrant client version.*incompatible with server version.*")
            self.client = QdrantClient(
                url=self.config.get_url(),
                api_key=self.config.get_api_key(),
            )
        else:
            print("[VectorStore] Using local persistent Qdrant")
            # Use persistent local storage instead of in-memory
            db_path = self.snapshot_dir / "qdrant_db"
            db_path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(db_path))
            print(f"[VectorStore] Qdrant database at: {db_path}")

    def get_or_create_collection(self, collection_name: str) -> None:
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(collection_name)
            print(f"[VectorStore] Collection exists: {collection_name}")
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=RAGConfig.get_embedding_dimension(),
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
            point_id = int(hashlib.md5(f"{doc_id}:{i}".encode()).hexdigest(), 16) % (2**31 - 1)
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
            print(f"[VectorStore] Created point id={point_id} for chunk {i} (doc_id={doc_id})")

        self.client.upsert(collection_name=collection_name, points=points)
        self.collection_count += len(points)

        print(f"[VectorStore] Indexed {len(points)} chunks in collection: {collection_name}")

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

            search_result = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k * 2,
            )

            points = search_result.points if hasattr(search_result, "points") else search_result
            print(f"[VectorStore] Semantic search: looking for doc_ids={doc_ids}, found {len(points)} hits")

            results = []
            for hit in points:
                payload_doc_id = hit.payload.get("doc_id")
                print(f"[VectorStore] Hit payload doc_id={payload_doc_id}, matches={payload_doc_id in (doc_ids or [])}")

                if doc_ids is None or payload_doc_id in doc_ids:
                    results.append(
                        {
                            "content": hit.payload.get("content", ""),
                            "doc_id": payload_doc_id,
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

    def delete_by_doc_id(self, collection_name: str, doc_id: str) -> None:
        """Delete all chunks belonging to a document."""
        try:
            from qdrant_client import models
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="doc_id",
                                match=models.MatchValue(value=doc_id),
                            )
                        ]
                    )
                ),
            )
            print(f"[VectorStore] Deleted all chunks for doc_id: {doc_id}")
        except Exception as exc:
            print(f"[VectorStore] Delete by doc_id error: {exc}")

    def delete_collection(self, collection_name: str) -> None:
        """Delete entire collection."""
        try:
            self.client.delete_collection(collection_name)
            print(f"[VectorStore] Deleted collection: {collection_name}")
        except Exception as exc:
            print(f"[VectorStore] Delete collection error: {exc}")

    def _save_snapshot(self, collection_name: str) -> None:
        """Save snapshot of collection to disk."""
        if self.config.get_mode() == "remote":
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
        """Load snapshot from disk if it exists."""
        if self.config.get_mode() == "remote":
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
