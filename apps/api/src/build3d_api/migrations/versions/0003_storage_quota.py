"""Persist per-user artifact byte limits.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

DEFAULT_STORAGE_LIMIT_BYTES = 5 * 1024 * 1024 * 1024


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "storage_limit_bytes",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text(str(DEFAULT_STORAGE_LIMIT_BYTES)),
        ),
    )


def downgrade():
    op.drop_column("users", "storage_limit_bytes")
