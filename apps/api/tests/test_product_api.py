import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from build3d_api.db import api_keys, check_schema, create_database, metadata as db_metadata, migrate, users
from build3d_api.images import normalize_image
from build3d_api.main import create_app
from build3d_api.store import Store, StoreError


def submit(env, project, key="one", prompt="a chair", auth=None):
    return env.client.post(f"/v1/projects/{project}/jobs/text",
                           headers={**(auth or env.auth), "Idempotency-Key": key},
                           json={"prompt": prompt, "model_id": "test_model"})


def test_health_does_not_claim_inference(env):
    response = env.client.get("/health")
    assert response.status_code == 200
    assert response.json()["gpu_verified"] is False


def test_job_contract_documents_and_preserves_the_public_projection(env, project):
    spec = env.client.get("/openapi.json").json()
    models = spec["components"]["schemas"]
    jobschema = {"$ref": "#/components/schemas/JobResponse"}
    submit_responses = spec["paths"]["/v1/projects/{project_id}/jobs/text"]["post"]["responses"]
    for code in ("200", "202"):
        assert submit_responses[code]["content"]["application/json"]["schema"] == jobschema
    assert submit_responses["409"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse",
    }
    assert models["JobResponse"]["properties"]["status"]["enum"] == [
        "queued", "dispatching", "running", "completed", "failed", "canceled",
        "submission_unknown", "polling_paused", "timed_out",
    ]

    created = submit(env, project)
    replay = submit(env, project)
    assert (created.status_code, replay.status_code) == (202, 200)
    job = created.json()
    assert created.headers["location"] == replay.headers["location"] == f"/v1/jobs/{job['id']}"
    assert set(job) == {
        "id", "project_id", "kind", "status", "model_id", "model_approval", "prompt",
        "input_sha256", "error_code", "created_at", "updated_at", "started_at",
    }
    assert job["model_approval"]["model_id"] == "test_model"
    assert job["input_sha256"] is job["started_at"] is job["error_code"] is None
    assert replay.json() == job
    assert env.client.get(f"/v1/jobs/{job['id']}", headers=env.auth).json() == job
    assert env.client.get(f"/v1/projects/{project}/jobs?limit=10", headers=env.auth).json() == {
        "items": [job], "limit": 10, "offset": 0,
    }
    foreign = env.client.get(f"/v1/jobs/{job['id']}", headers=env.other)
    assert foreign.status_code == 404 and foreign.json() == {"detail": "Job not found"}


def test_storage_contract_describes_zero_usage_without_internal_fields(env):
    spec = env.client.get("/openapi.json").json()
    response = spec["paths"]["/v1/storage"]["get"]["responses"]["200"]
    assert response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/StorageUsageResponse",
    }
    assert env.client.get("/v1/storage", headers=env.auth).json() == {
        "used_bytes": 0, "remaining_bytes": env.settings.default_storage_limit_bytes,
        "limit_bytes": env.settings.default_storage_limit_bytes, "over_quota": False,
    }


def test_authentication_is_per_user_and_no_plaintext_keys_stored(env):
    assert env.client.get("/v1/projects").status_code == 401
    assert env.client.get("/v1/projects", headers={"X-Control-Key": "x" * 32}).status_code == 401
    assert env.client.get("/v1/me", headers=env.auth).json()["user_id"] == env.alice["user_id"]
    with env.engine.connect() as conn:
        digest = conn.execute(sa.select(api_keys.c.digest).where(api_keys.c.id == env.alice["key_id"])).scalar_one()
    assert digest == hashlib.sha256(env.alice["api_key"].encode()).hexdigest()
    rotated = env.store.issue_key(env.alice["user_id"])
    env.store.revoke_key(env.alice["key_id"])
    assert env.client.get("/v1/me", headers=env.auth).status_code == 401
    assert env.client.get("/v1/me", headers={"Authorization": f"Bearer {rotated['api_key']}"}).status_code == 200


def test_disabled_user_is_rejected(env):
    with env.engine.begin() as conn:
        conn.execute(users.update().where(users.c.id == env.alice["user_id"]).values(active=False))
    assert env.client.get("/v1/projects", headers=env.auth).status_code == 401


def test_external_identity_mapping_is_immutable_and_not_email_based(env):
    issuer = "https://studio.example.com/"
    subject = "better-auth-user_01"
    linked = env.store.link_external_identity(env.alice["user_id"], issuer, subject)
    assert linked["issuer"] == "https://studio.example.com"
    assert linked["subject"] == subject
    assert env.store.resolve_external_identity("https://studio.example.com", subject) == env.alice["user_id"]

    repeated = env.store.link_external_identity(
        env.alice["user_id"], "https://studio.example.com", subject
    )
    assert repeated["id"] == linked["id"]

    with pytest.raises(StoreError) as conflict:
        env.store.link_external_identity(env.bob["user_id"], issuer, subject)
    assert conflict.value.status == 409

    with pytest.raises(StoreError) as replacement:
        env.store.link_external_identity(
            env.alice["user_id"], issuer, "different-provider-subject"
        )
    assert replacement.value.status == 409

    items = env.store.list_external_identities(env.alice["user_id"])
    assert [(item["issuer"], item["subject"]) for item in items] == [
        ("https://studio.example.com", subject)
    ]

    with env.engine.begin() as conn:
        conn.execute(users.update().where(
            users.c.id == env.alice["user_id"]
        ).values(active=False))
    with pytest.raises(StoreError) as disabled:
        env.store.resolve_external_identity(issuer, subject)
    assert disabled.value.status == 401

    with env.engine.begin() as conn:
        conn.execute(users.update().where(
            users.c.id == env.alice["user_id"]
        ).values(active=True))
    env.store.unlink_external_identity(issuer, subject)
    with pytest.raises(StoreError) as removed:
        env.store.resolve_external_identity(issuer, subject)
    assert removed.value.status == 401


@pytest.mark.parametrize("issuer", [
    "http://identity.example.com",
    "https://user:secret@identity.example.com",
    "https://identity.example.com?tenant=alice",
    "https://identity.example.com#fragment",
    "not-a-url",
])
def test_external_identity_rejects_ambiguous_or_insecure_issuers(env, issuer):
    with pytest.raises(StoreError) as exc:
        env.store.link_external_identity(env.alice["user_id"], issuer, "opaque-subject")
    assert exc.value.status == 422


def test_external_identity_allows_local_http_for_development(env):
    linked = env.store.link_external_identity(
        env.alice["user_id"], "http://localhost:3000/", "local-user"
    )
    assert linked["issuer"] == "http://localhost:3000"


@pytest.mark.parametrize("suffix,method", [
    ("", "get"), ("/cancel", "post"), ("/download", "get"), ("/artifact", "get"),
])
def test_cross_user_jobs_are_invisible(env, queued, suffix, method):
    response = getattr(env.client, method)(f"/v1/jobs/{queued}{suffix}", headers=env.other)
    assert response.status_code == 404


def test_cross_user_projects_cannot_be_listed_read_or_used(env, project):
    assert env.client.get("/v1/projects", headers=env.other).json()["items"] == []
    assert env.client.get(f"/v1/projects/{project}", headers=env.other).status_code == 404
    assert env.client.get(f"/v1/projects/{project}/jobs", headers=env.other).status_code == 404
    assert submit(env, project, auth=env.other).status_code == 404
    assert env.client.post(f"/v1/projects/{project}/jobs/image", headers={**env.other, "Idempotency-Key": "x"},
                           data={"model_id": "test_model"}, files={"file": ("x.png", b"bad")}).status_code == 404


def test_idempotency_replays_same_job_and_rejects_changed_request(env, project):
    first = submit(env, project)
    repeated = submit(env, project)
    assert first.status_code == 202
    assert repeated.status_code == 200
    assert repeated.json()["id"] == first.json()["id"]
    assert submit(env, project, prompt="different").status_code == 409
    assert first.headers["location"] == f"/v1/jobs/{first.json()['id']}"
    assert "input_image" not in first.json() and "lease_token" not in first.json()


def test_concurrent_identical_submissions_create_one_job_and_one_slot(env, project):
    def call(_):
        return env.store.submit(owner_id=env.alice["user_id"], project_id=project,
                                kind="text", model_id="test_model", approval=env.approval,
                                key="concurrent", prompt="a chair")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(call, range(8)))
    assert len({r[0]["id"] for r in results}) == 1
    assert sum(r[1] for r in results) == 1
    with env.engine.connect() as conn:
        assert conn.execute(sa.select(users.c.active_jobs).where(users.c.id == env.alice["user_id"])).scalar_one() == 1


def test_concurrent_different_requests_enforce_admission_quota(env, project):
    def call(index):
        try:
            env.store.submit(owner_id=env.alice["user_id"], project_id=project, kind="text",
                             model_id="test_model", approval=env.approval, key=f"parallel-{index}", prompt="chair")
            return 202
        except StoreError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(call, range(8)))
    assert statuses.count(202) == env.settings.max_active_jobs
    assert statuses.count(429) == 5


def test_quota_and_cancel_release_exactly_one_slot(env, project):
    ids = [submit(env, project, key=str(i)).json()["id"] for i in range(3)]
    assert submit(env, project, key="extra").status_code == 429
    for _ in range(2):
        assert env.client.post(f"/v1/jobs/{ids[0]}/cancel", headers=env.auth).status_code == 200
    assert submit(env, project, key="extra").status_code == 202
    assert submit(env, project, key="another").status_code == 429


def test_missing_policy_cannot_enqueue(env, project):
    env.policy.write_text(json.dumps({"schema_version": 1, "approved_models": []}))
    assert submit(env, project).status_code == 503
    assert env.client.get(f"/v1/projects/{project}/jobs", headers=env.auth).json()["items"] == []


def test_history_survives_new_engine_and_application(env, project, queued):
    second_engine = create_database(env.settings.database_url)
    try:
        with TestClient(create_app(env.settings, engine=second_engine)) as client:
            assert client.get(f"/v1/jobs/{queued}", headers=env.auth).json()["status"] == "queued"
            assert client.get("/v1/projects", headers=env.auth).json()["items"][0]["id"] == project
    finally:
        second_engine.dispose()


def test_rate_limit_is_atomic_and_resets_across_store_instances(env):
    settings = replace(env.settings, requests_per_minute=2)
    stores = [Store(env.engine, settings), Store(env.engine, settings)]
    for store in stores:
        store.authenticate(env.alice["api_key"], now=1000)
    with pytest.raises(StoreError) as exc:
        stores[0].authenticate(env.alice["api_key"], now=1001)
    assert exc.value.status == 429
    assert stores[1].authenticate(env.alice["api_key"], now=1060) == env.alice["user_id"]


def test_upload_is_decoded_persisted_and_keeps_original_hash(env, project, png):
    response = env.client.post(f"/v1/projects/{project}/jobs/image", headers={**env.auth, "Idempotency-Key": "image"},
                               data={"model_id": "test_model"}, files={"file": ("anything.txt", png, "text/plain")})
    assert response.status_code == 202, response.text
    row = env.store.job(env.alice["user_id"], response.json()["id"])
    assert row["input_sha256"] == hashlib.sha256(png).hexdigest()
    with Image.open(io.BytesIO(row["input_image"])) as saved:
        assert saved.format == "PNG" and saved.mode == "RGBA"


@pytest.mark.parametrize("data", [b"not image", b"\x89PNG\r\n\x1a\n", b"<svg></svg>"])
def test_fake_image_signature_is_not_enough(env, project, data):
    response = env.client.post(f"/v1/projects/{project}/jobs/image", headers={**env.auth, "Idempotency-Key": "bad"},
                               data={"model_id": "test_model"}, files={"file": ("x.png", data, "image/png")})
    assert response.status_code == 415


def test_image_metadata_removed():
    output = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("location", "private coordinates")
    exif = Image.Exif()
    exif[0x010E] = "private coordinates"
    Image.new("RGB", (2, 2)).save(output, format="PNG", pnginfo=metadata, exif=exif)
    with Image.open(io.BytesIO(normalize_image(output.getvalue()))) as image:
        assert image.info == {}


def test_malformed_exif_returns_validation_error_instead_of_crashing():
    output = io.BytesIO()
    Image.new("RGB", (2, 2)).save(output, format="PNG", exif=b"Exif\x00\x00private")
    with pytest.raises(ValueError, match="decoded"):
        normalize_image(output.getvalue())


def test_pixel_budget_enforced_before_full_decode(png, monkeypatch):
    monkeypatch.setattr("build3d_api.images.MAX_PIXELS", 4)
    with pytest.raises(ValueError, match="pixels"):
        normalize_image(png)


def test_request_size_limit_applies_before_parsing_and_to_chunked_body(env):
    response = env.client.post("/v1/projects", headers={**env.auth, "Content-Length": "999999999"}, content=b"{}")
    assert response.status_code == 413
    response = env.client.post("/v1/projects", headers={**env.auth, "Content-Type": "application/json"},
                               content=(b"x" * 1024 * 1024 for _ in range(12)))
    assert response.status_code == 413


@pytest.mark.parametrize("prompt", ["", "    ", "a" * 2001])
def test_invalid_prompts_rejected(env, project, prompt):
    assert submit(env, project, prompt=prompt).status_code == 422


def test_migrations_roundtrip_and_repeat_upgrade(env):
    migrate(env.engine)
    check_schema(env.engine)
    with env.engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), db_metadata) == []
    # Only this test's temporary file / random PostgreSQL schema is removed.
    migrate(env.engine, "base", downgrade=True)
    assert "jobs" not in sa.inspect(env.engine).get_table_names()
    migrate(env.engine)
    check_schema(env.engine)


def test_database_enforces_project_ownership_even_without_http(env, project):
    with pytest.raises(StoreError) as exc:
        env.store.submit(owner_id=env.bob["user_id"], project_id=project, kind="text", model_id="test_model",
                         approval=env.approval, key="other", prompt="chair")
    assert exc.value.status == 404


def test_cache_headers_and_pagination_bounds(env):
    response = env.client.get("/v1/projects", headers=env.auth)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert env.client.get("/v1/projects?limit=100000", headers=env.auth).status_code == 422


def test_storage_usage_is_owner_scoped_and_quota_is_persistent(env):
    initial = env.client.get("/v1/storage", headers=env.auth)
    assert initial.status_code == 200
    assert initial.json()["used_bytes"] == 0
    assert initial.json()["limit_bytes"] == env.settings.default_storage_limit_bytes

    updated = env.store.set_storage_quota(env.alice["user_id"], 12345)
    assert updated == {
        "used_bytes": 0,
        "limit_bytes": 12345,
        "remaining_bytes": 12345,
        "over_quota": False,
    }
    assert Store(env.engine, env.settings).storage_usage(env.alice["user_id"])["limit_bytes"] == 12345
    assert env.client.get("/v1/storage", headers=env.other).json()["limit_bytes"] == env.settings.default_storage_limit_bytes
