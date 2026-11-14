from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/build3d.db"
    artifact_dir: Path = Path("./data/artifacts")
    max_active_jobs: int = 3
    requests_per_minute: int = 120
    lease_seconds: int = 600
    poll_seconds: int = 5
    max_poll_failures: int = 5
    job_timeout_seconds: int = 3600

    def __post_init__(self):
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
            max_active_jobs=int(os.getenv("MAX_ACTIVE_JOBS_PER_USER", "3")),
            requests_per_minute=int(os.getenv("API_REQUESTS_PER_MINUTE", "120")),
        )
