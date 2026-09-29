"""create jobs

Revision ID: c0747bb0f90e
Revises: 
Create Date: 2026-09-29 22:53:28.653258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0747bb0f90e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "done", "failed", name="jobstatus"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("jobs")
    # drop_table не видаляє Postgres-тип enum, тому прибираємо його окремо,
    # інакше наступний upgrade впаде з "type jobstatus already exists".
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
