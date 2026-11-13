"""Run a real, owner-approved GPU smoke test through the private gateway.

This command NEVER creates a GPU VM. It submits an actual generation job to an
existing backend and WILL consume that backend's resources if run with consent.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .glb_validation import GLBValidationError, MAX_GLB_BYTES, inspect_glb


JOB_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


class SmokeError(RuntimeError):
    """A real inference smoke test failed or could not be verified."""


def run_smoke(
    *,
    gateway_url: str,
    control_key: str,
    model_id: str,
    output: Path,
    image: Path | None = None,
    prompt: str | None = None,
    timeout_seconds: float = 900,
    poll_seconds: float = 5,
    confirm_spend: bool = False,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Submit, poll, download, structurally validate, and report a *real* job.

    The caller must explicitly accept possible GPU charges. The model must
    already have passed the gateway's approval policy and exist on the GPU.
    """
    if not confirm_spend:
        raise SmokeError("Explicit --confirm-gpu-spend approval is required")
    if not control_key or len(control_key) < 24:
        raise SmokeError("A private CONTROL_API_KEY of at least 24 characters is required")
    if (image is None) == (prompt is None):
        raise SmokeError("Choose exactly one of --image and --prompt")
    if image is not None and (not image.is_file() or image.stat().st_size > 10 * 1024 * 1024):
        raise SmokeError("Image missing or exceeds the 10 MiB input limit")
    if output.exists():
        raise SmokeError("Output already exists; refusing to overwrite")
    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise SmokeError("Timeout and polling interval must be positive")
    if not model_id or not JOB_ID.fullmatch(model_id):
        raise SmokeError("Invalid model ID")

    started = time.monotonic()
    headers = {"X-Control-Key": control_key}
    # The owner controls this URL; use loopback or HTTPS when passing the key.
    if gateway_url.startswith("http://") and not gateway_url.startswith(
        ("http://127.0.0.1:", "http://localhost:", "http://[::1]:")
    ):
        raise SmokeError("Insecure non-local HTTP URL would expose the owner key")

    with httpx.Client(
        base_url=gateway_url.rstrip("/") + "/",
        headers=headers,
        timeout=httpx.Timeout(120.0, connect=10.0),
        follow_redirects=False,
        transport=transport,
    ) as client:
        response = client.get("v1/approved-models")
        response.raise_for_status()
        approved = response.json()
        if not isinstance(approved, dict) or model_id not in approved.get("approved_model_ids", []):
            raise SmokeError("Selected model has not passed the gateway approval gate")

        if image is not None:
            suffixes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
            mime = suffixes.get(image.suffix.lower())
            if mime is None:
                raise SmokeError("Only PNG, JPEG, or WEBP input images are supported")
            with image.open("rb") as source:
                response = client.post(
                    "v1/generations/image",
                    data={"model_preference": model_id},
                    files={"file": (image.name, source, mime)},
                )
        else:
            response = client.post(
                "v1/generations/text",
                json={"prompt": prompt, "model_preference": model_id},
            )
        response.raise_for_status()
        created = response.json()
        if not isinstance(created, dict):
            raise SmokeError("Backend response did not contain a job")
        job_id = created.get("job_id")
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise SmokeError("Backend returned an invalid job ID")

        deadline = started + timeout_seconds
        last_status = "queued"
        while True:
            if time.monotonic() >= deadline:
                raise SmokeError(f"GPU job {job_id} timed out; last status: {last_status}")
            result = client.get(f"v1/jobs/{job_id}")
            result.raise_for_status()
            payload = result.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("status"), str):
                raise SmokeError("Backend job status was malformed")
            last_status = payload["status"].lower()
            if last_status == "completed":
                break
            if last_status in {"failed", "error", "canceled", "cancelled"}:
                raise SmokeError(f"GPU job {job_id} ended with {last_status}")
            time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))

        output.parent.mkdir(parents=True, exist_ok=True)
        partial = output.with_name(output.name + ".part")
        if partial.exists():
            raise SmokeError("Partial output already exists; refusing to delete another run")
        created_partial = False
        try:
            # The gateway checks the GLB before sending; revalidate downloaded
            # bytes independently to catch truncated transport or client writes.
            with client.stream("GET", f"v1/jobs/{job_id}/download") as response:
                response.raise_for_status()
                expected_hash = response.headers.get("X-Artifact-SHA256")
                total = 0
                with partial.open("xb") as destination:
                    created_partial = True
                    for chunk in response.iter_bytes(chunk_size=256 * 1024):
                        total += len(chunk)
                        if total > MAX_GLB_BYTES:
                            raise SmokeError("Artifact exceeds 250 MiB safety limit")
                        destination.write(chunk)

            with partial.open("rb") as destination:
                inspected = inspect_glb(destination)
            if expected_hash and expected_hash != inspected.sha256:
                raise SmokeError("Gateway checksum does not match downloaded GLB")
            os.replace(partial, output)
        finally:
            if created_partial and partial.exists():
                partial.unlink()

        report = {
            "job_id": job_id,
            "model_id": model_id,
            "status": "completed",
            "output_path": str(output),
            "sha256": inspected.sha256,
            "size_bytes": inspected.size_bytes,
            "mesh_count": inspected.mesh_count,
            "primitive_count": inspected.primitive_count,
            "material_count": inspected.material_count,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "gpu_vram_gb": None,
            "gpu_cost_usd": None,
            "gpu_hardware": None,
            "note": "Structural GLB check only; Blender visual QA, VRAM and cost must be recorded separately.",
        }
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Perform a genuine 3D GPU smoke test (owner approval required)")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:8080")
    parser.add_argument("--model", required=True, help="Exact approved upstream model ID")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--image", type=Path)
    inputs.add_argument("--prompt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=900)
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument(
        "--confirm-gpu-spend", action="store_true",
        help="Acknowledge this performs real inference and can spend GPU credits",
    )
    options = parser.parse_args()
    try:
        report = run_smoke(
            gateway_url=options.gateway_url,
            control_key=os.environ.get("CONTROL_API_KEY", ""),
            model_id=options.model,
            output=options.output,
            image=options.image,
            prompt=options.prompt,
            timeout_seconds=options.timeout_seconds,
            poll_seconds=options.poll_seconds,
            confirm_spend=options.confirm_gpu_spend,
        )
    except (SmokeError, GLBValidationError, httpx.HTTPError, ValueError, OSError) as exc:
        print(f"Smoke test FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
