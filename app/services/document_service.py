from __future__ import annotations

import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from sentence_transformers import SentenceTransformer


def parse_pdf(filepath: str) -> str:
    """Extract text from PDF file."""
    if not PdfReader:
        raise ImportError("pypdf is not installed. Install it with: pip install pypdf")

    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF: {exc}")


def parse_docx(filepath: str) -> str:
    """Extract text from DOCX file."""
    if not DocxDocument:
        raise ImportError("python-docx is not installed. Install it with: pip install python-docx")

    try:
        doc = DocxDocument(filepath)
        text = "\n".join(para.text for para in doc.paragraphs)
        return text.strip()
    except Exception as exc:
        raise ValueError(f"Failed to parse DOCX: {exc}")


def parse_text(filepath: str) -> str:
    """Read plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception as exc:
        raise ValueError(f"Failed to read text file: {exc}")


def parse_document(filepath: str, content_type: str) -> str:
    """Auto-parse document based on content type."""
    if content_type == "application/pdf":
        return parse_pdf(filepath)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(filepath)
    elif content_type in ("text/plain", "text/markdown"):
        return parse_text(filepath)
    else:
        # Try to detect from file extension
        ext = Path(filepath).suffix.lower()
        if ext == ".pdf":
            return parse_pdf(filepath)
        elif ext == ".docx":
            return parse_docx(filepath)
        else:
            return parse_text(filepath)


def recursive_chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 100,
) -> list[str]:
    """
    Split text into chunks using recursive strategy.

    Strategy:
    1. Split by paragraphs (double newline)
    2. If paragraph > chunk_size, split by sentences
    3. Combine sentences until chunk_size reached
    4. Add overlap between chunks
    """
    # Normalize whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Split by paragraphs
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para) // 4  # Approximate tokens (1 token ≈ 4 chars)

        if current_size + para_size > chunk_size and current_chunk:
            # Current chunk is full, save it
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)

            # Start overlap: keep last paragraph
            current_chunk = [para]
            current_size = para_size
        else:
            # Add paragraph to current chunk
            current_chunk.append(para)
            current_size += para_size

    # Add remaining chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    # Apply overlap between chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # Find overlap point (last N chars from previous chunk)
            overlap_chars = min(len(prev_chunk), overlap * 4)
            overlap_text = prev_chunk[-overlap_chars:]

            # Prepend overlap to current chunk
            combined = f"{overlap_text}\n\n{curr_chunk}"
            overlapped_chunks.append(combined)

        return overlapped_chunks

    return chunks


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        if isinstance(embeddings, list):
            return embeddings
        return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]


# Global embedding model instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create global embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def embed_text(text: str) -> list[float]:
    """Embed a single text."""
    model = get_embedding_model()
    return model.embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts."""
    model = get_embedding_model()
    return model.embed_batch(texts)
