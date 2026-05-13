from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., description="New conversation title")


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    content_type: str | None
    size_bytes: int
    upload_date: str
    chunk_count: int = 0
