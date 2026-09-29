"""add users and job owner

Revision ID: cdce3970432d
Revises: 6cfa8e815325
Create Date: 2026-09-30 00:23:33.894997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdce3970432d'
down_revision: Union[str, Sequence[str], None] = '6cfa8e815325'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_EMAIL = "legacy@example.com"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # 1. expand: колонка спочатку nullable, бо в jobs уже є рядки без власника
    op.add_column("jobs", sa.Column("user_id", sa.Integer(), nullable=True))

    # 2. backfill: старі jobs віддаємо технічному користувачу
    op.execute(f"INSERT INTO users (email) VALUES ('{LEGACY_EMAIL}')")
    op.execute(
        f"UPDATE jobs SET user_id = (SELECT id FROM users WHERE email = '{LEGACY_EMAIL}') "
        "WHERE user_id IS NULL"
    )

    # 3. contract: тепер у всіх рядків є власник, можна NOT NULL
    op.alter_column("jobs", "user_id", nullable=False)

    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_jobs_user_id_users", "jobs", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_jobs_user_id_users", "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_column("jobs", "user_id")
    op.drop_table("users")
