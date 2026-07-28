import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.visitor import HowHeard, ReasonForVisit

PHONE_REGEX = re.compile(r"^\+?[0-9()\-.\s]{7,20}$")


class VisitorEntryCreate(BaseModel):
    how_heard: HowHeard
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None
    reason_for_visit: ReasonForVisit

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not PHONE_REGEX.match(value):
            raise ValueError(
                "phone_number must be a valid phone number (digits, spaces, and + ( ) - . only, 7-20 characters)"
            )
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class VisitorEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    how_heard: HowHeard
    first_name: str
    last_name: str
    phone_number: str
    email: str | None
    reason_for_visit: ReasonForVisit
    created_at: datetime


class VisitorEntryListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[VisitorEntryOut]


class VisitorEntryFilters(BaseModel):
    """Shared query params for listing/exporting visitor entries."""

    date_from: datetime | None = None
    date_to: datetime | None = None
    reason_for_visit: ReasonForVisit | None = None
    how_heard: HowHeard | None = None
    sort: Literal["created_at_asc", "created_at_desc"] = "created_at_desc"
