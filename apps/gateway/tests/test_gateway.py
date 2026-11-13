"""Tests use HTTPX in-memory transport only; they do NOT claim GPU inference success."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from build3d_gateway.main import app, get_gateway
from build3d_gateway.upstream import UpstreamGateway


KEY = "K" * 32


@pytest.fixture(autouse=True)
def configured_gateway(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTROL_API_KEY", KEY)
    policy = tmp_path / "model-approvals.json"
    policy.write_text(json.dumps({"schema_version": 1, "approved_models": [{
        "model_id": "test_model",
        "commercial_saas_rights_verified": True,
        "license_review": "docs/TEST_FIXTURE_ONLY.md",
        "reviewed_by": "unit-test",
        "reviewed_on": "2026-11-13",
        "upstream_commit_sha": "a" * 40,
        "checkpoint_sha256": "b" * 64
    }]}), encoding="utf-8")
    monkeypatch.setenv("MODEL_APPROVAL_FILE", str(policy))
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def mock_upstream(handler):
    app.dependency_overrides[get_gateway] = lambda: UpstreamGateway(
        "http://internal-gpu:7842",
        bearer_token="upstream-private-token",
        transport=httpx.MockTransport(handler),
    )


def test_process_health_is_not_claimed_as_gpu_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["gpu_verified"] is False


def test_gateway_fails_closed_without_secret(monkeypatch):
    monkeypatch.delenv("CONTROL_API_KEY")
    with TestClient(app) as client:
        response = client.get("/v1/models")
    assert response.status_code == 503


def test_gateway_requires_owner_key():
    with TestClient(app) as client:
        assert client.get("/v1/models").status_code == 401
        assert client.get("/v1/models", headers={"X-Control-Key": "wrong"}).status_code == 401


def test_text_submission_uses_real_upstream_contract():
    observed = []

    def handler(request):
        observed.append(request)
        assert request.headers["authorization"] == "Bearer upstream-private-token"
        assert request.url.path == "/api/v1/mesh-generation/text-to-textured-mesh"
        assert b'"text_prompt":"robot cat"' in request.content
        assert b'"output_format":"glb"' in request.content
        return httpx.Response(200, json={"job_id": "job_100", "status": "queued"})

    mock_upstream(handler)
    with TestClient(app) as client:
        response = client.post(
            "/v1/generations/text",
            headers={"X-Control-Key": KEY},
            json={"prompt": "robot cat", "model_preference": "test_model"},
        )
    assert response.status_code == 200
    assert response.json()["job_id"] == "job_100"
    assert len(observed) == 1


def test_image_upload_then_generation_uses_file_id():
    observed = []

    def handler(request):
        observed.append(request.url.path)
        assert request.headers["authorization"] == "Bearer upstream-private-token"
        if request.url.path == "/api/v1/file-upload/image":
            assert b'filename="reference.png"' in request.content
            return httpx.Response(200, json={"file_id": "image_44"})
        assert request.url.path == "/api/v1/mesh-generation/image-to-textured-mesh"
        assert b'"image_file_id":"image_44"' in request.content
        return httpx.Response(200, json={"job_id": "job_44", "status": "queued"})

    mock_upstream(handler)
    with TestClient(app) as client:
        response = client.post(
            "/v1/generations/image",
            headers={"X-Control-Key": KEY},
            files={"file": ("reference.png", b"\x89PNG\r\n\x1a\n" + b"x" * 8, "image/png")},
            data={"model_preference": "test_model"},
        )
    assert response.status_code == 200
    assert response.json()["job_id"] == "job_44"
    assert observed == [
        "/api/v1/file-upload/image",
        "/api/v1/mesh-generation/image-to-textured-mesh",
    ]


def test_invalid_image_is_rejected_before_upstream_call():
    with TestClient(app) as client:
        response = client.post(
            "/v1/generations/image",
            headers={"X-Control-Key": KEY},
            files={"file": ("bad.png", b"NOT_IMAGE", "image/png")},
            data={"model_preference": "test_model"},
        )
    assert response.status_code == 415


def test_model_job_and_download_proxy():
    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"models": []})
        if request.url.path.endswith("/jobs/job_7"):
            return httpx.Response(200, json={"job_id": "job_7", "status": "completed"})
        if request.url.path.endswith("/download"):
            return httpx.Response(200, content=b"glTF", headers={"content-type": "model/gltf-binary"})
        raise AssertionError(request.url.path)

    mock_upstream(handler)
    with TestClient(app) as client:
        headers = {"X-Control-Key": KEY}
        assert client.get("/v1/models", headers=headers).status_code == 200
        assert client.get("/v1/jobs/job_7", headers=headers).json()["status"] == "completed"
        response = client.get("/v1/jobs/job_7/download", headers=headers)
    assert response.status_code == 200
    assert response.content == b"glTF"


def test_upstream_failure_is_not_misrepresented_as_success():
    mock_upstream(lambda request: httpx.Response(503, json={"detail": "GPU unavailable"}))
    with TestClient(app) as client:
        response = client.post(
            "/v1/generations/text",
            headers={"X-Control-Key": KEY},
            json={"prompt": "a robot", "model_preference": "test_model"},
        )
    assert response.status_code == 502
    assert "503" in response.json()["detail"]


def test_no_path_traversal_or_arbitrary_model_names():
    with TestClient(app) as client:
        headers = {"X-Control-Key": KEY}
        response = client.get("/v1/jobs/..evil", headers=headers)
        assert response.status_code == 422
        response = client.post(
            "/v1/generations/text",
            headers=headers,
            json={"prompt": "robot", "model_preference": "../other"},
        )
        assert response.status_code == 422


def test_generation_denies_missing_and_unapproved_model():
    with TestClient(app) as client:
        headers = {"X-Control-Key": KEY}
        missing = client.post("/v1/generations/text", headers=headers, json={"prompt": "robot"})
        unknown = client.post("/v1/generations/text", headers=headers,
                              json={"prompt": "robot", "model_preference": "unreviewed"})
    assert missing.status_code == 422
    assert unknown.status_code == 403


def test_generation_disabled_when_approvals_empty(monkeypatch, tmp_path):
    policy = tmp_path / "empty.json"
    policy.write_text('{"schema_version": 1, "approved_models": []}', encoding="utf-8")
    monkeypatch.setenv("MODEL_APPROVAL_FILE", str(policy))
    with TestClient(app) as client:
        response = client.post("/v1/generations/text", headers={"X-Control-Key": KEY},
                               json={"prompt": "robot", "model_preference": "test_model"})
    assert response.status_code == 503


def test_malformed_approval_denied(monkeypatch, tmp_path):
    policy = tmp_path / "invalid.json"
    policy.write_text('{"schema_version": 1, "approved_models": [{"model_id": "test_model"}]}', encoding="utf-8")
    monkeypatch.setenv("MODEL_APPROVAL_FILE", str(policy))
    with TestClient(app) as client:
        response = client.post("/v1/generations/text", headers={"X-Control-Key": KEY},
                               json={"prompt": "robot", "model_preference": "test_model"})
    assert response.status_code == 503


def test_absent_policy_denied(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_APPROVAL_FILE", str(tmp_path / "missing.json"))
    with TestClient(app) as client:
        response = client.post("/v1/generations/text", headers={"X-Control-Key": KEY},
                               json={"prompt": "robot", "model_preference": "test_model"})
    assert response.status_code == 503


def test_owner_can_list_explicit_approved_models():
    with TestClient(app) as client:
        assert client.get("/v1/approved-models").status_code == 401
        response = client.get("/v1/approved-models", headers={"X-Control-Key": KEY})
    assert response.status_code == 200
    assert response.json() == {"approved_model_ids": ["test_model"]}


def test_unapproved_image_never_uploads_to_upstream():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"file_id": "unexpected"})

    mock_upstream(handler)
    with TestClient(app) as client:
        response = client.post(
            "/v1/generations/image",
            headers={"X-Control-Key": KEY},
            data={"model_preference": "unreviewed"},
            files={"file": ("reference.png", b"\x89PNG\r\n\x1a\n" + b"x" * 8, "image/png")},
        )
    assert response.status_code == 403
    assert requests == []
