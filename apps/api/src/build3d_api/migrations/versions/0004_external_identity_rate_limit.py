"""Add durable rate-limit windows to external identity credentials.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "external_identities",
        sa.Column("window_start", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "external_identities",
        sa.Column("request_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade():
    op.drop_column("external_identities", "request_count")
    op.drop_column("external_identities", "window_start")
