"""Lease-based polling worker; GPU submissions require explicit operator consent."""
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from fastapi import HTTPException

from build3d_gateway.download import ArtifactTooLarge, fetch_verified_glb
from build3d_gateway.model_policy import approved_model_records
from build3d_gateway.upstream import UpstreamError, UpstreamGateway

from .config import Settings
from .db import check_schema, create_database
from .store import Store, UPSTREAM_ID, new_id


class Worker:
    def __init__(self, store: Store, upstream: UpstreamGateway, *, confirm_spend: bool = False,
                 clock=time.time):
        self.store = store
        self.settings = store.settings
        self.upstream = upstream
        self.confirm_spend = confirm_spend
        self.clock = clock

    def transition(self, job, status, **values):
        return self.store.transition(job, status, now=self.clock(), **values)

    async def step(self) -> bool:
        if not self.confirm_spend:
            raise RuntimeError("Worker requires --confirm-gpu-spend before it can submit jobs")
        job = self.store.claim(now=self.clock())
        if job is None:
            return False
        if job["status"] == "dispatching":
            await self.submit(job)
        else:
            await self.poll(job)
        return True

    async def submit(self, job):
        try:
            approval = approved_model_records().get(job["model_id"])
        except HTTPException:
            approval = None
        # Compare the complete approval snapshot: never silently swap a checkpoint.
        if approval is None or approval != job["model_approval"]:
            self.transition(job, "failed", error_code="model_approval_changed")
            return
        try:
            if job["kind"] == "text":
                response = await self.upstream.text_to_3d(job["prompt"], job["model_id"])
            else:
                response = await self.upstream.image_to_3d(job["input_image"], "image/png", job["model_id"])
            remote_id = response.get("job_id") if isinstance(response, dict) else None
            if not isinstance(remote_id, str) or not UPSTREAM_ID.fullmatch(remote_id):
                raise UpstreamError("Missing valid upstream job id")
        except UpstreamError:
            self.transition(job, "submission_unknown", error_code="submission_outcome_unknown")
            return
        self.transition(job, "running", upstream_job_id=remote_id,
                        poll_after=self.clock() + self.settings.poll_seconds, error_code=None)

    async def poll(self, job):
        if self.clock() - job["started_at"] >= self.settings.job_timeout_seconds:
            self.transition(job, "timed_out", error_code="upstream_completion_timeout")
            return
        try:
            response = await self.upstream.job(job["upstream_job_id"])
            status = response.get("status") if isinstance(response, dict) else None
            if status in {"failed", "cancelled", "canceled"}:
                self.transition(job, "failed", error_code="upstream_job_failed")
            elif status == "completed":
                await self.save_artifact(job)
            elif status in {"pending", "queued", "running", "processing"}:
                self.transition(job, "running", poll_failures=0, error_code=None,
                                poll_after=self.clock() + self.settings.poll_seconds)
            else:
                raise UpstreamError("Unknown upstream job state")
        except ArtifactTooLarge:
            self.transition(job, "failed", error_code="artifact_too_large")
        except (UpstreamError, OSError):
            failures = job["poll_failures"] + 1
            paused = failures >= self.settings.max_poll_failures
            self.transition(job, "polling_paused" if paused else "running",
                            poll_failures=failures, error_code="upstream_read_failed",
                            poll_after=self.clock() + min(300, self.settings.poll_seconds * 2 ** failures))

    async def save_artifact(self, job):
        source, report = await fetch_verified_glb(self.upstream, job["upstream_job_id"])
        artifact_id = new_id()
        directory = self.settings.artifact_dir
        destination = directory / f"{artifact_id}.glb"
        staged: str | None = None
        committed = False
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            # Stage on the destination filesystem, then atomically publish it.
            with tempfile.NamedTemporaryFile(dir=directory, suffix=".part", delete=False) as output:
                staged = output.name
                with open(source, "rb") as input_file:
                    shutil.copyfileobj(input_file, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(staged, destination)
            # Persist directory metadata before recording a completed job.
            if hasattr(os, "O_DIRECTORY"):
                fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            committed = self.transition(job, "completed", error_code=None, artifact={
                "id": artifact_id, "job_id": job["id"], "owner_id": job["owner_id"],
                "sha256": report.sha256, "size_bytes": report.size_bytes,
                "mesh_count": report.mesh_count, "created_at": self.clock(),
            })
        finally:
            Path(source).unlink(missing_ok=True)
            if staged is not None:
                Path(staged).unlink(missing_ok=True)
            if not committed:
                destination.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-gpu-spend", action="store_true")
    parser.add_argument("--max-steps", type=int, default=1, help="Finite work cycles; default 1")
    parser.add_argument("--interval-seconds", type=float, default=5)
    args = parser.parse_args(argv)
    if not args.confirm_gpu_spend:
        parser.error("--confirm-gpu-spend is required; API queueing alone never launches inference")
    if not 1 <= args.max_steps <= 10000 or not 0 < args.interval_seconds <= 60:
        parser.error("max-steps must be 1–10000 and interval-seconds must be >0 and <=60")
    settings = Settings.from_env()
    engine = create_database(settings.database_url)
    try:
        check_schema(engine)
        upstream = UpstreamGateway(os.getenv("UPSTREAM_BASE_URL", "http://127.0.0.1:7842"),
                                   os.getenv("UPSTREAM_BEARER_TOKEN") or None)
        worker = Worker(Store(engine, settings), upstream, confirm_spend=True)

        async def run():
            for index in range(args.max_steps):
                await worker.step()
                if index + 1 < args.max_steps:
                    await asyncio.sleep(args.interval_seconds)

        asyncio.run(run())
        return 0
    except Exception:
        # Do not print DB exceptions containing bound input data or credentials.
        print("Worker stopped; inspect database availability and job states before restarting.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
