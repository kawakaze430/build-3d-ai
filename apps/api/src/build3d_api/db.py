"""SQLAlchemy Core schema and explicit Alembic migrations (PostgreSQL/SQLite)."""
from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine, make_url


metadata = sa.MetaData()

users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("active", sa.Boolean, nullable=False),
    sa.Column("active_jobs", sa.Integer, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.CheckConstraint("active_jobs >= 0", name="ck_users_active_jobs"),
)
api_keys = sa.Table(
    "api_keys", metadata,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id"), nullable=False),
    sa.Column("digest", sa.String(64), nullable=False, unique=True),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("revoked_at", sa.Float),
    sa.Column("window_start", sa.Float, nullable=False),
    sa.Column("request_count", sa.Integer, nullable=False),
)
projects = sa.Table(
    "projects", metadata,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id"), nullable=False, index=True),
    sa.Column("name", sa.String(120), nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.UniqueConstraint("id", "owner_id", name="uq_projects_owner"),
)
jobs = sa.Table(
    "jobs", metadata,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("owner_id", sa.String(32), sa.ForeignKey("users.id"), nullable=False, index=True),
    sa.Column("project_id", sa.String(32), nullable=False),
    sa.Column("kind", sa.String(10), nullable=False),
    sa.Column("status", sa.String(32), nullable=False, index=True),
    sa.Column("idempotency_key", sa.String(128), nullable=False),
    sa.Column("request_hash", sa.String(64), nullable=False),
    sa.Column("model_id", sa.String(128), nullable=False),
    sa.Column("model_approval", sa.JSON, nullable=False),
    sa.Column("prompt", sa.Text),
    sa.Column("input_sha256", sa.String(64)),
    sa.Column("input_image", sa.LargeBinary),
    sa.Column("upstream_job_id", sa.String(128)),
    sa.Column("lease_token", sa.String(32)),
    sa.Column("lease_until", sa.Float),
    sa.Column("poll_after", sa.Float, nullable=False),
    sa.Column("poll_failures", sa.Integer, nullable=False),
    sa.Column("error_code", sa.String(64)),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("updated_at", sa.Float, nullable=False),
    sa.Column("started_at", sa.Float),
    sa.UniqueConstraint("owner_id", "idempotency_key", name="uq_jobs_idempotency"),
    sa.UniqueConstraint("id", "owner_id", name="uq_jobs_owner"),
    sa.ForeignKeyConstraint(["project_id", "owner_id"], ["projects.id", "projects.owner_id"]),
    sa.CheckConstraint("kind IN ('text', 'image')", name="ck_jobs_kind"),
    sa.CheckConstraint(
        "status IN ('queued','dispatching','running','completed','failed','canceled',"
        "'submission_unknown','polling_paused','timed_out')", name="ck_jobs_status",
    ),
)
artifacts = sa.Table(
    "artifacts", metadata,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("job_id", sa.String(32), nullable=False, unique=True),
    sa.Column("owner_id", sa.String(32), nullable=False, index=True),
    sa.Column("sha256", sa.String(64), nullable=False),
    sa.Column("size_bytes", sa.BigInteger, nullable=False),
    sa.Column("mesh_count", sa.Integer, nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.ForeignKeyConstraint(["job_id", "owner_id"], ["jobs.id", "jobs.owner_id"]),
)


def create_database(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.get_backend_name() not in {"sqlite", "postgresql"}:
        raise ValueError("Only PostgreSQL and SQLite databases are supported")
    options = {"pool_pre_ping": True}
    if parsed.get_backend_name() == "sqlite":
        if not parsed.database or parsed.database == ":memory:":
            raise ValueError("Use a persistent SQLite file, not an in-memory database")
        Path(parsed.database).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    engine = sa.create_engine(url, **options)
    if engine.dialect.name == "sqlite":
        @sa.event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    return engine


def migrate(engine: Engine, revision: str = "head", *, downgrade: bool = False):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).with_name("migrations")))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        (command.downgrade if downgrade else command.upgrade)(config, revision)


def check_schema(engine: Engine):
    with engine.connect() as connection:
        version = connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()
    if version != "0001":
        raise RuntimeError("Database migration required: run build3d-admin migrate")
