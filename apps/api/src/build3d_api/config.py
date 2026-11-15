from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false")


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/build3d.db"
    artifact_dir: Path = Path("./data/artifacts")
    artifact_storage_backend: str = "filesystem"
    artifact_storage_prefix: str = "build3d/v1/artifacts"
    s3_artifact_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str | None = None
    default_storage_limit_bytes: int = 5 * 1024 * 1024 * 1024
    external_jwt_auth_enabled: bool = False
    identity_provider_file: Path | None = None
    max_active_jobs: int = 3
    requests_per_minute: int = 120
    lease_seconds: int = 600
    poll_seconds: int = 5
    max_poll_failures: int = 5
    job_timeout_seconds: int = 3600

    def __post_init__(self):
        if self.artifact_storage_backend not in {"filesystem", "s3"}:
            raise ValueError("ARTIFACT_STORAGE_BACKEND must be filesystem or s3")
        prefix = self.artifact_storage_prefix.strip("/")
        if not prefix or "\\" in prefix or any(part in {"", ".", ".."} for part in prefix.split("/")):
            raise ValueError("ARTIFACT_STORAGE_PREFIX is invalid")
        if self.artifact_storage_backend == "s3" and not self.s3_artifact_bucket:
            raise ValueError("S3_ARTIFACT_BUCKET is required when ARTIFACT_STORAGE_BACKEND=s3")
        if self.s3_endpoint_url:
            endpoint = urlsplit(self.s3_endpoint_url)
            if endpoint.scheme not in {"http", "https"} or not endpoint.netloc or endpoint.username or endpoint.password:
                raise ValueError("S3_ENDPOINT_URL must be an http(s) endpoint without embedded credentials")
        if not 0 <= self.default_storage_limit_bytes <= 10 * 1024 * 1024 * 1024 * 1024:
            raise ValueError("DEFAULT_STORAGE_LIMIT_BYTES must be between 0 and 10 TiB")
        if self.external_jwt_auth_enabled and self.identity_provider_file is None:
            raise ValueError(
                "IDENTITY_PROVIDER_FILE is required when EXTERNAL_JWT_AUTH_ENABLED=true"
            )
        for field in (
            "max_active_jobs", "requests_per_minute", "lease_seconds", "poll_seconds",
            "max_poll_failures", "job_timeout_seconds",
        ):
            if getattr(self, field) < 1:
                raise ValueError(f"{field} must be positive")

    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            artifact_dir=Path(os.getenv("ARTIFACT_DIR", "./data/artifacts")),
            artifact_storage_backend=os.getenv("ARTIFACT_STORAGE_BACKEND", "filesystem").strip().lower(),
            artifact_storage_prefix=os.getenv("ARTIFACT_STORAGE_PREFIX", "build3d/v1/artifacts"),
            s3_artifact_bucket=os.getenv("S3_ARTIFACT_BUCKET") or None,
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            s3_region=os.getenv("S3_REGION") or os.getenv("AWS_REGION") or None,
            default_storage_limit_bytes=int(
                os.getenv("DEFAULT_STORAGE_LIMIT_BYTES", str(5 * 1024 * 1024 * 1024))
            ),
            external_jwt_auth_enabled=_env_bool("EXTERNAL_JWT_AUTH_ENABLED"),
            identity_provider_file=(
                Path(os.environ["IDENTITY_PROVIDER_FILE"])
                if os.getenv("IDENTITY_PROVIDER_FILE")
                else None
            ),
            max_active_jobs=int(os.getenv("MAX_ACTIVE_JOBS_PER_USER", "3")),
            requests_per_minute=int(os.getenv("API_REQUESTS_PER_MINUTE", "120")),
        )
