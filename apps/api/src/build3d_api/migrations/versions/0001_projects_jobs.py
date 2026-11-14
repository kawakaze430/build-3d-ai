"""Initial private product schema. Frozen; do not import current model metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('active_jobs', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.Float(), nullable=False),
    sa.CheckConstraint('active_jobs >= 0', name='ck_users_active_jobs'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('api_keys',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('owner_id', sa.String(length=32), nullable=False),
    sa.Column('digest', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.Float(), nullable=False),
    sa.Column('revoked_at', sa.Float(), nullable=True),
    sa.Column('window_start', sa.Float(), nullable=False),
    sa.Column('request_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('digest')
    )
    op.create_table('projects',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('owner_id', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('created_at', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'owner_id', name='uq_projects_owner')
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_table('jobs',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('owner_id', sa.String(length=32), nullable=False),
    sa.Column('project_id', sa.String(length=32), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('idempotency_key', sa.String(length=128), nullable=False),
    sa.Column('request_hash', sa.String(length=64), nullable=False),
    sa.Column('model_id', sa.String(length=128), nullable=False),
    sa.Column('model_approval', sa.JSON(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=True),
    sa.Column('input_sha256', sa.String(length=64), nullable=True),
    sa.Column('input_image', sa.LargeBinary(), nullable=True),
    sa.Column('upstream_job_id', sa.String(length=128), nullable=True),
    sa.Column('lease_token', sa.String(length=32), nullable=True),
    sa.Column('lease_until', sa.Float(), nullable=True),
    sa.Column('poll_after', sa.Float(), nullable=False),
    sa.Column('poll_failures', sa.Integer(), nullable=False),
    sa.Column('error_code', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.Float(), nullable=False),
    sa.Column('updated_at', sa.Float(), nullable=False),
    sa.Column('started_at', sa.Float(), nullable=True),
    sa.CheckConstraint("kind IN ('text', 'image')", name='ck_jobs_kind'),
    sa.CheckConstraint("status IN ('queued','dispatching','running','completed','failed','canceled','submission_unknown','polling_paused','timed_out')", name='ck_jobs_status'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['project_id', 'owner_id'], ['projects.id', 'projects.owner_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id', 'owner_id', name='uq_jobs_owner'),
    sa.UniqueConstraint('owner_id', 'idempotency_key', name='uq_jobs_idempotency')
    )
    op.create_index(op.f('ix_jobs_owner_id'), 'jobs', ['owner_id'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_table('artifacts',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('job_id', sa.String(length=32), nullable=False),
    sa.Column('owner_id', sa.String(length=32), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('mesh_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['job_id', 'owner_id'], ['jobs.id', 'jobs.owner_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_artifacts_owner_id'), 'artifacts', ['owner_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_artifacts_owner_id'), table_name='artifacts')
    op.drop_table('artifacts')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_owner_id'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_projects_owner_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_table('api_keys')
    op.drop_table('users')
