"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

how_heard_enum = postgresql.ENUM(
    "google",
    "yelp",
    "facebook",
    "instagram",
    "family_friend",
    "home_depot",
    "drove_by",
    "previous_customer",
    "other",
    name="how_heard_enum",
)

reason_for_visit_enum = postgresql.ENUM(
    "new_project_estimate",
    "existing_project",
    "appointment",
    "employment",
    "other",
    name="reason_for_visit_enum",
)


def upgrade() -> None:
    bind = op.get_bind()
    how_heard_enum.create(bind, checkfirst=True)
    reason_for_visit_enum.create(bind, checkfirst=True)
    # Columns below reference the same Enum objects; without this, SQLAlchemy's
    # table-create DDL event tries to CREATE TYPE again and collides with the
    # explicit .create() calls above.
    how_heard_enum.create_type = False
    reason_for_visit_enum.create_type = False

    op.create_table(
        "visitor_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("how_heard", how_heard_enum, nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("reason_for_visit", reason_for_visit_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_visitor_entries_created_at", "visitor_entries", ["created_at"])

    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admin_users_username", "admin_users", ["username"], unique=True)

    op.create_table(
        "admin_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admin_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_admin_sessions_token", "admin_sessions", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_admin_sessions_token", table_name="admin_sessions")
    op.drop_table("admin_sessions")

    op.drop_index("ix_admin_users_username", table_name="admin_users")
    op.drop_table("admin_users")

    op.drop_index("ix_visitor_entries_created_at", table_name="visitor_entries")
    op.drop_table("visitor_entries")

    bind = op.get_bind()
    reason_for_visit_enum.drop(bind, checkfirst=True)
    how_heard_enum.drop(bind, checkfirst=True)
