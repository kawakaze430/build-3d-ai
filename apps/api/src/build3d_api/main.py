"""Private tenant API: persistent work is queued; HTTP handlers never run a GPU."""
from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError

from build3d_gateway.glb_validation import GLBValidationError, inspect_glb
from build3d_gateway.model_policy import approved_model_records

from .config import Settings
from .body_limit import BodyLimitMiddleware
from .db import check_schema, create_database
from .images import MAX_IMAGE_BYTES, normalize_image
from .store import Store, StoreError, public_job


class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()


class TextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=2000)
    model_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")

    @field_validator("prompt")
    @classmethod
    def nonblank_prompt(cls, value):
        if not value.strip():
            raise ValueError("Prompt cannot be blank")
        return value.strip()


def approval_for(model_id: str) -> dict:
    records = approved_model_records()
    if not records:
        raise HTTPException(503, "Generation disabled: no approved model is configured")
    if model_id not in records:
        raise HTTPException(403, "Requested model is not approved")
    return records[model_id]


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    settings = settings or Settings.from_env()
    owns_engine = engine is None
    engine = engine if engine is not None else create_database(settings.database_url)
    store = Store(engine, settings)

    @asynccontextmanager
    async def lifespan(_):
        try:
            check_schema(engine)
            settings.artifact_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            yield
        finally:
            if owns_engine:
                engine.dispose()

    app = FastAPI(title="Build 3D AI — Project API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(BodyLimitMiddleware)
    app.state.store = store
    bearer = HTTPBearer(auto_error=False)

    def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
        if credentials is None:
            raise StoreError(401, "A user API key is required")
        return store.authenticate(credentials.credentials)

    @app.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(StoreError)
    async def store_error(_, exc):
        headers = {"Retry-After": "60"} if exc.status == 429 else {}
        if exc.status == 401:
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail}, headers=headers)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_, exc):
        # SQL exceptions can include tokens, prompts, input bytes, or credentials.
        return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})

    @app.get("/health")
    def health():
        check_schema(engine)
        return {"status": "ok", "service": "build3d-api", "gpu_verified": False}

    @app.get("/v1/me")
    def me(owner: str = Depends(identity)):
        return {"user_id": owner}

    @app.get("/v1/models")
    def models(owner: str = Depends(identity)):
        return {"approved_model_ids": sorted(approved_model_records())}

    @app.post("/v1/projects", status_code=201)
    def create_project(body: ProjectRequest, owner: str = Depends(identity)):
        return store.create_project(owner, body.name)

    @app.get("/v1/projects")
    def list_projects(owner: str = Depends(identity), limit: int = Query(50, ge=1, le=100),
                      offset: int = Query(0, ge=0, le=100000)):
        return {"items": store.list_projects(owner, limit, offset), "limit": limit, "offset": offset}

    @app.get("/v1/projects/{project_id}")
    def get_project(project_id: str, owner: str = Depends(identity)):
        row = store.project(owner, project_id)
        return {key: row[key] for key in ("id", "name", "created_at")}

    @app.post("/v1/projects/{project_id}/jobs/text")
    def submit_text(project_id: str, body: TextRequest, owner: str = Depends(identity),
                    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128)):
        store.project(owner, project_id)
        row, created = store.submit(
            owner_id=owner, project_id=project_id, key=idempotency_key,
            kind="text", model_id=body.model_id, prompt=body.prompt,
            approval=approval_for(body.model_id),
        )
        return JSONResponse(public_job(row), status_code=202 if created else 200,
                            headers={"Location": f"/v1/jobs/{row['id']}"})

    @app.post("/v1/projects/{project_id}/jobs/image")
    def submit_image(project_id: str, file: UploadFile = File(...),
                     model_id: str = Form(..., pattern=r"^[A-Za-z0-9_-]{1,128}$"),
                     owner: str = Depends(identity),
                     idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128)):
        try:
            store.project(owner, project_id)
            approval = approval_for(model_id)
            data = file.file.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(413, "Image exceeds 10 MiB")
            try:
                normalized = normalize_image(data)
            except ValueError as exc:
                raise HTTPException(415, str(exc)) from exc
            row, created = store.submit(
                owner_id=owner, project_id=project_id, key=idempotency_key,
                kind="image", model_id=model_id, approval=approval, image=normalized,
                input_sha256=hashlib.sha256(data).hexdigest(),
            )
            return JSONResponse(public_job(row), status_code=202 if created else 200,
                                headers={"Location": f"/v1/jobs/{row['id']}"})
        finally:
            file.file.close()

    @app.get("/v1/projects/{project_id}/jobs")
    def list_jobs(project_id: str, owner: str = Depends(identity),
                  limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
        return {"items": store.list_jobs(owner, project_id, limit, offset), "limit": limit, "offset": offset}

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str, owner: str = Depends(identity)):
        return public_job(store.job(owner, job_id))

    @app.post("/v1/jobs/{job_id}/cancel")
    def cancel_job(job_id: str, owner: str = Depends(identity)):
        return public_job(store.cancel(owner, job_id))

    @app.get("/v1/jobs/{job_id}/artifact")
    def get_artifact(job_id: str, owner: str = Depends(identity)):
        record = store.artifact(owner, job_id)
        return {key: record[key] for key in ("id", "job_id", "sha256", "size_bytes", "mesh_count", "created_at")}

    @app.get("/v1/jobs/{job_id}/download")
    def download(job_id: str, owner: str = Depends(identity)):
        record = store.artifact(owner, job_id)
        path = settings.artifact_dir / (record["id"] + ".glb")
        try:
            if path.is_symlink():
                raise OSError("Unexpected artifact symlink")
            with path.open("rb") as handle:
                report = inspect_glb(handle)
            if report.sha256 != record["sha256"] or report.size_bytes != record["size_bytes"]:
                raise GLBValidationError("Stored checksum mismatch")
        except (OSError, GLBValidationError) as exc:
            raise HTTPException(503, "Stored artifact is unavailable or failed integrity validation") from exc
        return FileResponse(path, media_type="model/gltf-binary", filename=f"{job_id}.glb",
                            headers={"X-Artifact-SHA256": report.sha256})

    return app
