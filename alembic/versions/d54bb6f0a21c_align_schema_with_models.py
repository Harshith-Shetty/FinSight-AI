"""Align the database schema with the current ORM models.

Revision ID: d54bb6f0a21c
Revises: b3e7f0b435e2
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d54bb6f0a21c"
down_revision: Union[str, None] = "b3e7f0b435e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_enum_value(enum_name: str, old_value: str, new_value: str) -> None:
    """Rename a legacy enum label when its canonical label is absent."""
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_enum e ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_name}' AND e.enumlabel = '{old_value}'
                ) AND NOT EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_enum e ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_name}' AND e.enumlabel = '{new_value}'
                ) THEN
                    ALTER TYPE {enum_name} RENAME VALUE '{old_value}' TO '{new_value}';
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    # SQLAlchemy persists Python Enum member names for these model columns.
    for old, new in (("hybrid", "HYBRID"), ("private", "PRIVATE")):
        _rename_enum_value("chatmode", old, new)

    for value in ("pending", "processing", "completed", "failed"):
        _rename_enum_value("taskstatus", value, value.upper())

    # SafeUserRole intentionally stores role names in a VARCHAR column.
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) "
        "USING UPPER(role::text)"
    )
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")

    # Existing accounts predate verification and should remain usable. New
    # accounts inherit FALSE after this migration.
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column(
        "users",
        "is_verified",
        existing_type=sa.Boolean(),
        server_default=sa.false(),
    )

    op.execute("UPDATE chats SET is_deleted = FALSE WHERE is_deleted IS NULL")
    op.alter_column(
        "chats",
        "is_deleted",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )

    # Create the PostgreSQL type once, then tell the table definition to reuse it.
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE otppurpose AS ENUM ('EMAIL_VERIFICATION', 'PASSWORD_RESET');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    otp_purpose = postgresql.ENUM(
        "EMAIL_VERIFICATION",
        "PASSWORD_RESET",
        name="otppurpose",
        create_type=False,
    )
    op.create_table(
        "otp_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("purpose", otp_purpose, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_otp_user_purpose", "otp_tokens", ["user_id", "purpose"])
    op.create_index(op.f("ix_otp_tokens_user_id"), "otp_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_otp_tokens_user_id"), table_name="otp_tokens")
    op.drop_index("idx_otp_user_purpose", table_name="otp_tokens")
    op.drop_table("otp_tokens")
    op.execute("DROP TYPE IF EXISTS otppurpose")

    op.alter_column(
        "chats",
        "is_deleted",
        existing_type=sa.Boolean(),
        server_default=None,
    )
    op.drop_column("users", "is_verified")
