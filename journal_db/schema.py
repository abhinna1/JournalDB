from datetime import date
from typing import Optional, List

from pydantic import BaseModel, field_validator
from pydantic import ValidationError as PydanticValidationError

from journal_db.errors import ValidationError


class MetaDataSchema(BaseModel):
    title: str
    date: date
    body: str
    tags: Optional[List[str]] = []
    mood: Optional[str] = None
    location: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v

    @classmethod
    def from_dict(cls, data: dict) -> "MetaDataSchema":
        """Factory — build a MetaDataSchema from a raw dict, wrapping Pydantic errors."""
        try:
            return cls(**data)
        except PydanticValidationError as exc:
            first = exc.errors()[0]
            field = ".".join(str(f) for f in first["loc"])
            raise ValidationError(f"'{field}': {first['msg']}") from exc


class IndexRecord(BaseModel):
    id: str
    filename: str
    title: str
    date: str           # YYYY-MM-DD string
    tags: List[str] = []
    mood: Optional[str] = None
    location: Optional[str] = None
    word_count: int
    checksum: str       # SHA-256 of the source file — used for change detection
    indexed_at: str     # ISO 8601 datetime string

    @classmethod
    def from_dict(cls, data: dict) -> "IndexRecord":
        """Build an IndexRecord from a raw dict (e.g. loaded from JSON)."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON storage."""
        return self.model_dump()
