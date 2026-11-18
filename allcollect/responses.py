"""Public job and storage HTTP response contracts."""
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: str
    project_id: str
    kind: Literal["text", "image"]
    status: Literal[
        "queued",
        "dispatching",
        "running",
        "completed",
        "failed",
        "canceled",
        "submission_unknown",
        "polling_paused",
        "timed_out",
    ]
    model_id: str
    model_approval: dict[str, Any]
    prompt: str | None
    input_sha256: str | None
    error_code: str | None
    created_at: float
    updated_at: float
    started_at: float | None


class JobPageResponse(BaseModel):
    items: list[JobResponse]
    limit: int
    offset: int


class StorageUsageResponse(BaseModel):
    used_bytes: int = Field(ge=0)
    limit_bytes: int = Field(ge=0)
    remaining_bytes: int = Field(ge=0)
    over_quota: bool


class ErrorResponse(BaseModel):
    detail: str
