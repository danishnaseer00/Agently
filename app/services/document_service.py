from __future__ import annotations

import re
from pathlib import Path
from functools import lru_cache

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


def parse_pdf(filepath: str) -> str:
    """Extract text from PDF file."""
    if not PdfReader:
        raise ImportError("pypdf is not installed. Install it with: pip install pypdf")

    try:
        reader = PdfReader(filepath)
        text = ""
        page_texts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            page_text = page_text or ""
            page_texts.append((i + 1, len(page_text)))
            text += page_text + "\n"
        result = text.strip()
        print(f"[PDF] Parsed {len(reader.pages)} pages, total {len(result)} chars")
        for pg_num, pg_len in page_texts:
            print(f"[PDF]   Page {pg_num}: {pg_len} chars")
        if len(result) < 200 and len(reader.pages) > 1:
            print("[PDF] WARNING: Very little text extracted. This PDF may be scanned/image-based.")
        return result
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


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split text into pieces of at most max_chars, breaking at word boundaries."""
    if len(text) <= max_chars:
        return [text]
    pieces = []
    while text:
        if len(text) <= max_chars:
            pieces.append(text)
            break
        # Try to break at last space before max_chars
        split_at = text.rfind(" ", 0, max_chars)
        if split_at <= 0:
            split_at = max_chars
        pieces.append(text[:split_at])
        text = text[split_at:].lstrip()
    return pieces


def recursive_chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 100,
) -> list[str]:
    """
    Split text into chunks using recursive strategy.
    Falls back to hard character split if no sentence boundaries exist.
    """
    if not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Split by paragraphs
    paragraphs = text.split('\n\n')

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0
    max_chars = chunk_size * 4  # ~tokens to chars

    def _flush() -> None:
        nonlocal current_chunk, current_size
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_size = 0

    def _add_piece(piece: str) -> None:
        nonlocal current_chunk, current_size
        piece_size = len(piece) // 4
        if current_size + piece_size > chunk_size and current_chunk:
            _flush()
        current_chunk.append(piece)
        current_size += piece_size

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para) // 4

        # If paragraph fits, add it directly
        if para_size <= chunk_size:
            _add_piece(para)
            continue

        # Paragraph is oversized — try sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', para)
        has_real_sentences = len(sentences) > 1

        if has_real_sentences:
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                sent_size = len(sent) // 4
                # If a single sentence is still too big, hard-split it
                if sent_size > chunk_size:
                    for piece in _hard_split(sent, max_chars):
                        _add_piece(piece)
                else:
                    _add_piece(sent)
        else:
            # No sentence boundaries — hard split by character count
            for piece in _hard_split(para, max_chars):
                _add_piece(piece)

    _flush()

    print(f"[Chunker] Input {len(text)} chars → {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    for i, c in enumerate(chunks):
        print(f"[Chunker]   Chunk {i}: {len(c)} chars, ~{len(c)//4} tokens")

    return chunks


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SentenceTransformer:
            raise ImportError("sentence-transformers is not installed. Install it with: pip install sentence-transformers")
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
@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Get or create global embedding model (singleton)."""
    return EmbeddingModel()


def embed_text(text: str) -> list[float]:
    """Embed a single text."""
    model = get_embedding_model()
    return model.embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts."""
    model = get_embedding_model()
    return model.embed_batch(texts)
