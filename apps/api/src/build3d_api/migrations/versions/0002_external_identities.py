"""Add immutable external identity mappings for future browser identity.

This table links one issuer-local external subject to exactly one product user.
It intentionally stores no email address, password, reset token, or session.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_identities",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("issuer", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuer", "subject", name="uq_external_identity_subject"),
        sa.UniqueConstraint("owner_id", "issuer", name="uq_external_identity_owner_issuer"),
    )
    op.create_index(
        op.f("ix_external_identities_owner_id"),
        "external_identities",
        ["owner_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_external_identities_owner_id"), table_name="external_identities")
    op.drop_table("external_identities")
