"""Smoke-runner tests use a fake local HTTP transport, NOT a GPU."""
from __future__ import annotations

import httpx
import pytest

from build3d_gateway.glb_validation import GLBValidationError
from build3d_gateway.smoke import SmokeError, run_smoke


KEY = "C" * 32
MODEL = "test_model"


def kwargs(tmp_path):
    return {
        "gateway_url": "http://127.0.0.1:8080",
        "control_key": KEY,
        "model_id": MODEL,
        "prompt": "a stylized robot",
        "output": tmp_path / "result.glb",
        "poll_seconds": 0.001,
        "timeout_seconds": 2.0,
        "confirm_spend": True,
    }


def test_real_job_flow_protocol_and_glb_integrity(tmp_path, glb_bytes):
    requests = []
    status_calls = 0

    def handler(req):
        nonlocal status_calls
        requests.append((req.method, req.url.path))
        assert req.headers["x-control-key"] == KEY
        if req.url.path == "/v1/approved-models":
            return httpx.Response(200, json={"approved_model_ids": [MODEL]})
        if req.url.path == "/v1/generations/text":
            assert req.method == "POST"
            assert req.read().decode().find('"model_preference":"test_model"') >= 0
            return httpx.Response(200, json={"job_id": "job_42", "status": "queued"})
        if req.url.path == "/v1/jobs/job_42" and req.method == "GET":
            status_calls += 1
            return httpx.Response(
                200,
                json={"job_id": "job_42", "status": "completed" if status_calls >= 2 else "running"},
            )
        if req.url.path == "/v1/jobs/job_42/download":
            import hashlib
            return httpx.Response(
                200,
                content=glb_bytes,
                headers={"X-Artifact-SHA256": hashlib.sha256(glb_bytes).hexdigest()},
            )
        raise AssertionError(req.url.path)

    report = run_smoke(**kwargs(tmp_path), transport=httpx.MockTransport(handler))
    assert report["status"] == "completed"
    assert report["mesh_count"] == 1
    assert report["size_bytes"] == len(glb_bytes)
    assert report["gpu_cost_usd"] is None
    assert (tmp_path / "result.glb").read_bytes() == glb_bytes
    assert not (tmp_path / "result.glb.part").exists()
    assert status_calls == 2
    assert requests[0] == ("GET", "/v1/approved-models")


def test_gpu_spend_must_be_explicit(tmp_path):
    options = kwargs(tmp_path)
    options["confirm_spend"] = False
    with pytest.raises(SmokeError, match="confirm"):
        run_smoke(**options)
    assert list(tmp_path.iterdir()) == []


def test_unapproved_models_cannot_create_jobs(tmp_path):
    requested = []

    def handler(req):
        requested.append(req.url.path)
        return httpx.Response(200, json={"approved_model_ids": []})

    with pytest.raises(SmokeError, match="approval"):
        run_smoke(**kwargs(tmp_path), transport=httpx.MockTransport(handler))
    assert requested == ["/v1/approved-models"]


def test_completed_job_cannot_hide_invalid_glb(tmp_path):
    def handler(req):
        if req.url.path == "/v1/approved-models":
            return httpx.Response(200, json={"approved_model_ids": [MODEL]})
        if req.url.path == "/v1/generations/text":
            return httpx.Response(200, json={"job_id": "job_42"})
        if req.url.path == "/v1/jobs/job_42":
            return httpx.Response(200, json={"status": "completed"})
        return httpx.Response(200, content=b"FAKE_GLTF_OUTPUT")

    with pytest.raises(GLBValidationError):
        run_smoke(**kwargs(tmp_path), transport=httpx.MockTransport(handler))
    assert not (tmp_path / "result.glb").exists()
    assert not (tmp_path / "result.glb.part").exists()


def test_failed_job_is_reported_and_not_downloaded(tmp_path):
    requests = []

    def handler(req):
        requests.append(req.url.path)
        if req.url.path == "/v1/approved-models":
            return httpx.Response(200, json={"approved_model_ids": [MODEL]})
        if req.url.path == "/v1/generations/text":
            return httpx.Response(200, json={"job_id": "job_42"})
        return httpx.Response(200, json={"status": "failed"})

    with pytest.raises(SmokeError, match="failed"):
        run_smoke(**kwargs(tmp_path), transport=httpx.MockTransport(handler))
    assert "/v1/jobs/job_42/download" not in requests


def test_nonlocal_cleartext_gateway_refused_before_secret_sent(tmp_path):
    options = kwargs(tmp_path)
    options["gateway_url"] = "http://public.example.com:8080"
    with pytest.raises(SmokeError, match="Insecure"):
        run_smoke(**options)


@pytest.mark.parametrize("disguised", [
    "http://localhost:8080@evil.example",
    "http://127.0.0.1:8080@attacker.example",
    "http://localhost.evil.example:8080",
    "https://admin:password@gateway.example",
])
def test_disguised_or_credentialed_gateway_urls_are_rejected(tmp_path, disguised):
    options = kwargs(tmp_path)
    options["gateway_url"] = disguised
    with pytest.raises(SmokeError):
        run_smoke(**options)
