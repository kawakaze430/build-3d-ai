"""Atomic job admission, ownership, leases, and persistence.

Non-idempotent upstream POSTs are never retried automatically. A lost response
cannot prove that no GPU work was accepted. Those jobs retain their quota slot
until an operator reconciles them with the actual upstream service.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
import uuid

import sqlalchemy as sa

from .config import Settings
from .db import api_keys, artifacts, jobs, projects, users


TERMINAL = {"completed", "failed", "canceled"}
ATTENTION = {"submission_unknown", "polling_paused", "timed_out"}
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
UPSTREAM_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
PUBLIC_JOB_FIELDS = (
    "id", "project_id", "kind", "status", "model_id", "model_approval", "prompt",
    "input_sha256", "error_code", "created_at", "updated_at", "started_at",
)


class StoreError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(detail)


def new_id() -> str:
    return uuid.uuid4().hex


def public_job(row: dict) -> dict:
    return {key: row[key] for key in PUBLIC_JOB_FIELDS}


def fingerprint(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Store:
    def __init__(self, engine, settings: Settings):
        self.engine = engine
        self.settings = settings

    def create_user(self, name: str) -> dict:
        name = name.strip()
        if not 1 <= len(name) <= 120:
            raise StoreError(422, "Name must contain 1–120 characters")
        owner_id, key_id, token = new_id(), new_id(), "b3d_" + secrets.token_urlsafe(32)
        now = time.time()
        with self.engine.begin() as conn:
            conn.execute(users.insert().values(id=owner_id, name=name, active=True, active_jobs=0, created_at=now))
            conn.execute(api_keys.insert().values(
                id=key_id, owner_id=owner_id, digest=hashlib.sha256(token.encode()).hexdigest(),
                created_at=now, window_start=0, request_count=0,
            ))
        return {"user_id": owner_id, "key_id": key_id, "api_key": token}

    def issue_key(self, owner_id: str) -> dict:
        token, key_id = "b3d_" + secrets.token_urlsafe(32), new_id()
        with self.engine.begin() as conn:
            if not conn.execute(sa.select(users.c.id).where(users.c.id == owner_id, users.c.active.is_(True))).first():
                raise StoreError(404, "Active user not found")
            conn.execute(api_keys.insert().values(
                id=key_id, owner_id=owner_id, digest=hashlib.sha256(token.encode()).hexdigest(),
                created_at=time.time(), window_start=0, request_count=0,
            ))
        return {"user_id": owner_id, "key_id": key_id, "api_key": token}

    def revoke_key(self, key_id: str):
        with self.engine.begin() as conn:
            result = conn.execute(api_keys.update().where(api_keys.c.id == key_id).values(revoked_at=time.time()))
            if result.rowcount != 1:
                raise StoreError(404, "Key not found")

    def authenticate(self, token: str, *, now: float | None = None) -> str:
        if not re.fullmatch(r"b3d_[A-Za-z0-9_-]{43}", token):
            raise StoreError(401, "Invalid API key")
        now = time.time() if now is None else now
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.engine.begin() as conn:
            row = conn.execute(sa.select(api_keys.c.id, api_keys.c.owner_id).join(users).where(
                api_keys.c.digest == digest, api_keys.c.revoked_at.is_(None), users.c.active.is_(True),
            )).mappings().first()
            if row is None:
                raise StoreError(401, "Invalid API key")
            expired = api_keys.c.window_start <= now - 60
            result = conn.execute(api_keys.update().where(
                api_keys.c.id == row["id"], api_keys.c.revoked_at.is_(None),
                sa.or_(expired, api_keys.c.request_count < self.settings.requests_per_minute),
            ).values(
                request_count=sa.case((expired, 1), else_=api_keys.c.request_count + 1),
                window_start=sa.case((expired, now), else_=api_keys.c.window_start),
            ))
            if result.rowcount != 1:
                raise StoreError(429, "API request limit reached; retry in 60 seconds")
            return row["owner_id"]

    def create_project(self, owner_id: str, name: str) -> dict:
        row = {"id": new_id(), "owner_id": owner_id, "name": name, "created_at": time.time()}
        with self.engine.begin() as conn:
            conn.execute(projects.insert().values(**row))
        return {key: value for key, value in row.items() if key != "owner_id"}

    def list_projects(self, owner_id: str, limit: int, offset: int) -> list[dict]:
        with self.engine.connect() as conn:
            return [dict(r) for r in conn.execute(sa.select(
                projects.c.id, projects.c.name, projects.c.created_at,
            ).where(projects.c.owner_id == owner_id).order_by(
                projects.c.created_at.desc(), projects.c.id,
            ).limit(limit).offset(offset)).mappings()]

    def project(self, owner_id: str, project_id: str) -> dict:
        with self.engine.connect() as conn:
            row = conn.execute(sa.select(projects).where(
                projects.c.id == project_id, projects.c.owner_id == owner_id,
            )).mappings().first()
        if row is None:
            raise StoreError(404, "Project not found")
        return dict(row)

    @staticmethod
    def _existing(conn, owner_id: str, key: str, request_hash: str):
        row = conn.execute(sa.select(jobs).where(
            jobs.c.owner_id == owner_id, jobs.c.idempotency_key == key,
        )).mappings().first()
        if row is not None and row["request_hash"] != request_hash:
            raise StoreError(409, "Idempotency-Key was already used for a different request")
        return dict(row) if row else None

    def submit(self, *, owner_id: str, project_id: str, kind: str, model_id: str,
               key: str, approval: dict, prompt: str | None = None,
               image: bytes | None = None, input_sha256: str | None = None) -> tuple[dict, bool]:
        if not KEY_PATTERN.fullmatch(key):
            raise StoreError(422, "Idempotency-Key must contain 1–128 letters, digits, _, ., : or -")
        request_hash = fingerprint({
            "project": project_id, "kind": kind, "model": model_id,
            "prompt": prompt, "input_sha256": input_sha256,
        })
        now = time.time()
        with self.engine.begin() as conn:
            if not conn.execute(sa.select(projects.c.id).where(
                projects.c.id == project_id, projects.c.owner_id == owner_id,
            )).first():
                raise StoreError(404, "Project not found")
            existing = self._existing(conn, owner_id, key, request_hash)
            if existing:
                return existing, False
            # This row update serializes admission for one owner across processes.
            admitted = conn.execute(users.update().where(
                users.c.id == owner_id, users.c.active.is_(True),
                users.c.active_jobs < self.settings.max_active_jobs,
            ).values(active_jobs=users.c.active_jobs + 1)).rowcount == 1
            existing = self._existing(conn, owner_id, key, request_hash)
            if existing:
                if admitted:
                    conn.execute(users.update().where(users.c.id == owner_id).values(active_jobs=users.c.active_jobs - 1))
                return existing, False
            if not admitted:
                raise StoreError(429, "Active job limit reached; complete or cancel queued jobs first")
            job_id = new_id()
            conn.execute(jobs.insert().values(
                id=job_id, owner_id=owner_id, project_id=project_id, kind=kind,
                status="queued", idempotency_key=key, request_hash=request_hash,
                model_id=model_id, model_approval=approval, prompt=prompt,
                input_image=image, input_sha256=input_sha256, poll_after=now,
                poll_failures=0, created_at=now, updated_at=now,
            ))
            return dict(conn.execute(sa.select(jobs).where(jobs.c.id == job_id)).mappings().one()), True

    def job(self, owner_id: str, job_id: str) -> dict:
        with self.engine.connect() as conn:
            row = conn.execute(sa.select(jobs).where(jobs.c.id == job_id, jobs.c.owner_id == owner_id)).mappings().first()
        if row is None:
            raise StoreError(404, "Job not found")
        return dict(row)

    def list_jobs(self, owner_id: str, project_id: str, limit: int, offset: int) -> list[dict]:
        self.project(owner_id, project_id)
        with self.engine.connect() as conn:
            return [public_job(dict(row)) for row in conn.execute(sa.select(jobs).where(
                jobs.c.owner_id == owner_id, jobs.c.project_id == project_id,
            ).order_by(jobs.c.created_at.desc(), jobs.c.id).limit(limit).offset(offset)).mappings()]

    def cancel(self, owner_id: str, job_id: str) -> dict:
        with self.engine.begin() as conn:
            changed = conn.execute(jobs.update().where(
                jobs.c.id == job_id, jobs.c.owner_id == owner_id, jobs.c.status == "queued",
            ).values(status="canceled", updated_at=time.time(), input_image=None)).rowcount
            if changed:
                conn.execute(users.update().where(users.c.id == owner_id).values(active_jobs=users.c.active_jobs - 1))
            row = conn.execute(sa.select(jobs).where(jobs.c.id == job_id, jobs.c.owner_id == owner_id)).mappings().first()
            if row is None:
                raise StoreError(404, "Job not found")
            if row["status"] != "canceled":
                raise StoreError(409, "Only queued jobs can be canceled; upstream cancellation is not supported")
            return dict(row)

    def claim(self, *, now: float | None = None) -> dict | None:
        now = time.time() if now is None else now
        with self.engine.begin() as conn:
            # A worker lost mid-POST may have created a paid job. Never resubmit it.
            conn.execute(jobs.update().where(
                jobs.c.status == "dispatching", jobs.c.lease_until <= now,
            ).values(status="submission_unknown", error_code="submission_outcome_unknown",
                     updated_at=now, lease_token=None, lease_until=None))
            available = sa.and_(
                jobs.c.status.in_(["queued", "running"]), jobs.c.poll_after <= now,
                sa.or_(jobs.c.lease_until.is_(None), jobs.c.lease_until <= now),
            )
            candidates = conn.execute(sa.select(jobs.c.id).where(available).order_by(
                sa.case((jobs.c.status == "running", 0), else_=1), jobs.c.created_at,
            ).limit(16)).scalars().all()
            for job_id in candidates:
                token = new_id()
                changed = conn.execute(jobs.update().where(jobs.c.id == job_id, available).values(
                    status=sa.case((jobs.c.status == "queued", "dispatching"), else_=jobs.c.status),
                    started_at=sa.func.coalesce(jobs.c.started_at, now),
                    lease_token=token, lease_until=now + self.settings.lease_seconds, updated_at=now,
                )).rowcount
                if changed:
                    return dict(conn.execute(sa.select(jobs).where(jobs.c.id == job_id)).mappings().one())
        return None

    def transition(self, job: dict, status: str, *, now: float | None = None,
                   artifact: dict | None = None, **values) -> bool:
        now = time.time() if now is None else now
        with self.engine.begin() as conn:
            changed = conn.execute(jobs.update().where(
                jobs.c.id == job["id"], jobs.c.status == job["status"],
                jobs.c.lease_token == job["lease_token"], jobs.c.lease_until > now,
            ).values(
                status=status, lease_token=None, lease_until=None, updated_at=now,
                **({"input_image": None} if status in TERMINAL else {}), **values,
            )).rowcount
            if not changed:
                return False
            if artifact is not None:
                conn.execute(artifacts.insert().values(**artifact))
            if status in TERMINAL:
                conn.execute(users.update().where(users.c.id == job["owner_id"]).values(active_jobs=users.c.active_jobs - 1))
            return True

    def artifact(self, owner_id: str, job_id: str) -> dict:
        self.job(owner_id, job_id)
        with self.engine.connect() as conn:
            row = conn.execute(sa.select(artifacts).where(
                artifacts.c.owner_id == owner_id, artifacts.c.job_id == job_id,
            )).mappings().first()
        if row is None:
            raise StoreError(409, "No verified artifact is available for this job")
        return dict(row)

    def reconcile(self, job_id: str, upstream_id: str | None, *, confirm_stopped: bool = False):
        if upstream_id is not None and not UPSTREAM_ID.fullmatch(upstream_id):
            raise StoreError(422, "Invalid upstream job ID")
        if upstream_id is None and not confirm_stopped:
            raise StoreError(409, "Confirm the upstream is stopped before releasing a job slot")
        now = time.time()
        with self.engine.begin() as conn:
            row = conn.execute(sa.select(jobs).where(jobs.c.id == job_id)).mappings().first()
            if row is None:
                raise StoreError(404, "Job not found")
            if row["status"] not in ATTENTION:
                raise StoreError(409, "Only jobs requiring operator attention can be reconciled")
            changed = conn.execute(jobs.update().where(
                jobs.c.id == job_id, jobs.c.status == row["status"],
            ).values(
                status="running" if upstream_id else "failed",
                upstream_job_id=upstream_id or row["upstream_job_id"], error_code=None if upstream_id else "operator_resolved",
                poll_after=now, poll_failures=0, started_at=now, updated_at=now,
                input_image=None, lease_token=None, lease_until=None,
            )).rowcount
            if changed != 1:
                raise StoreError(409, "Job changed; reload before reconciling")
            if upstream_id is None:
                conn.execute(users.update().where(users.c.id == row["owner_id"]).values(active_jobs=users.c.active_jobs - 1))
