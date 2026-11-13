"""Owner-controlled admin gateway for a *real* 3DAIGC-API GPU installation.

SECURITY SCOPE: one trusted operator only. This is NOT a multi-tenant SaaS
authentication system. Put behind a private network; never expose upstream
anonymous mode to the internet. See docs/PHASE0_GATEWAY.md.
"""

from __future__ import annotations

import hmac
import os
import re

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from .upstream import UpstreamError, UpstreamGateway


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 250 * 1024 * 1024
JOB_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
MODEL_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

app = FastAPI(
    title="Build 3D AI — Integration Gateway",
    description="Owner-authenticated, real upstream model integration. Not yet a customer SaaS.",
    version="0.1.0",
)


class TextGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=2000)
    model_preference: str | None = Field(default=None, max_length=128)


def require_control_key(x_control_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("CONTROL_API_KEY", "")
    if len(expected) < 24:
        raise HTTPException(status_code=503, detail="Gateway key is not configured")
    if not x_control_key or not hmac.compare_digest(x_control_key, expected):
        raise HTTPException(status_code=401, detail="Invalid control key")


def get_gateway() -> UpstreamGateway:
    return UpstreamGateway(
        base_url=os.getenv("UPSTREAM_BASE_URL", "http://127.0.0.1:7842"),
        bearer_token=os.getenv("UPSTREAM_BEARER_TOKEN") or None,
    )


def clean_job_id(job_id: str) -> str:
    if not JOB_ID.fullmatch(job_id):
        raise HTTPException(status_code=422, detail="Invalid job identifier")
    return job_id


def clean_model_id(model_preference: str | None) -> str | None:
    if model_preference and not MODEL_ID.fullmatch(model_preference):
        raise HTTPException(status_code=422, detail="Invalid model identifier")
    return model_preference


def validate_image(data: bytes, content_type: str | None) -> None:
    valid = (
        (content_type == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
        or (content_type == "image/jpeg" and data.startswith(b"\xff\xd8\xff"))
        or (
            content_type == "image/webp"
            and len(data) >= 12
            and data[:4] == b"RIFF"
            and data[8:12] == b"WEBP"
        )
    )
    if not valid:
        raise HTTPException(status_code=415, detail="Only PNG, JPEG and WEBP images allowed")


@app.exception_handler(UpstreamError)
async def upstream_error_handler(_, exc: UpstreamError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/health")
async def health():
    # Process health only; upstream/GPU status is checked via authenticated route.
    return {"status": "ok", "service": "build3d-gateway", "gpu_verified": False}


@app.get("/v1/upstream/status", dependencies=[Depends(require_control_key)])
async def upstream_status(gateway: UpstreamGateway = Depends(get_gateway)):
    return await gateway.status()


@app.get("/v1/models", dependencies=[Depends(require_control_key)])
async def list_models(gateway: UpstreamGateway = Depends(get_gateway)):
    return await gateway.list_models()


@app.post("/v1/generations/text", dependencies=[Depends(require_control_key)])
async def text_to_3d(
    payload: TextGenerationRequest,
    gateway: UpstreamGateway = Depends(get_gateway),
):
    return await gateway.text_to_3d(
        prompt=payload.prompt, model_preference=clean_model_id(payload.model_preference)
    )


@app.post("/v1/generations/image", dependencies=[Depends(require_control_key)])
async def image_to_3d(
    file: UploadFile = File(...),
    model_preference: str | None = Form(default=None),
    gateway: UpstreamGateway = Depends(get_gateway),
):
    model = clean_model_id(model_preference)
    try:
        data = await file.read(MAX_IMAGE_BYTES + 1)
    finally:
        await file.close()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MiB")
    validate_image(data, file.content_type)
    return await gateway.image_to_3d(data, file.content_type or "", model)


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(require_control_key)])
async def job_status(job_id: str, gateway: UpstreamGateway = Depends(get_gateway)):
    return await gateway.job(clean_job_id(job_id))


@app.get("/v1/jobs/{job_id}/download", dependencies=[Depends(require_control_key)])
async def download(job_id: str, gateway: UpstreamGateway = Depends(get_gateway)):
    client, response = await gateway.open_download(clean_job_id(job_id))
    raw_length = response.headers.get("content-length")
    try:
        reported_size = int(raw_length) if raw_length else None
    except ValueError:
        reported_size = None
    if reported_size is not None and reported_size > MAX_DOWNLOAD_BYTES:
        await response.aclose()
        await client.aclose()
        raise HTTPException(status_code=413, detail="Artifact exceeds 250 MiB gateway limit")

    async def chunks():
        count = 0
        try:
            async for chunk in response.aiter_bytes(chunk_size=256 * 1024):
                count += len(chunk)
                if count > MAX_DOWNLOAD_BYTES:
                    # Prevent unbounded downloads; downstream stream terminates.
                    raise RuntimeError("Upstream artifact exceeds size limit")
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        chunks(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="generated-model.glb"'},
    )
