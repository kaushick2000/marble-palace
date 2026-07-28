import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class HowHeard(str, enum.Enum):
    google = "google"
    yelp = "yelp"
    facebook = "facebook"
    instagram = "instagram"
    family_friend = "family_friend"
    home_depot = "home_depot"
    drove_by = "drove_by"
    previous_customer = "previous_customer"
    other = "other"


class ReasonForVisit(str, enum.Enum):
    new_project_estimate = "new_project_estimate"
    existing_project = "existing_project"
    appointment = "appointment"
    employment = "employment"
    other = "other"


class VisitorEntry(Base):
    __tablename__ = "visitor_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    how_heard: Mapped[HowHeard] = mapped_column(
        Enum(HowHeard, name="how_heard_enum", native_enum=True), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_for_visit: Mapped[ReasonForVisit] = mapped_column(
        Enum(ReasonForVisit, name="reason_for_visit_enum", native_enum=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
