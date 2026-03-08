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
