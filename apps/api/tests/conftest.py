"""Real database tests; upstream HTTP and mesh are explicitly synthetic fixtures."""
import io
import json
import os
import struct
import uuid
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.engine import make_url

from build3d_api.config import Settings
from build3d_api.db import create_database, migrate
from build3d_api.main import create_app
from build3d_api.store import Store


@pytest.fixture
def env(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    approval = {
        "model_id": "test_model", "commercial_saas_rights_verified": True,
        "license_review": "docs/TEST_FIXTURE_ONLY.md", "reviewed_by": "unit-test",
        "reviewed_on": "2026-11-14", "upstream_commit_sha": "a" * 40,
        "checkpoint_sha256": "b" * 64,
    }
    policy.write_text(json.dumps({"schema_version": 1, "approved_models": [approval]}))
    monkeypatch.setenv("MODEL_APPROVAL_FILE", str(policy))
    external = os.getenv("TEST_DATABASE_URL")
    admin = None
    if external:
        # Only a fresh randomly named schema is created/dropped, never public data.
        assert make_url(external).get_backend_name() == "postgresql"
        schema = "test_" + uuid.uuid4().hex
        admin = sa.create_engine(external)
        with admin.begin() as connection:
            connection.execute(sa.schema.CreateSchema(schema))
        url = make_url(external).update_query_dict({"options": f"-csearch_path={schema}"})
        url = url.render_as_string(hide_password=False)
    else:
        url = f"sqlite:///{tmp_path / 'test.db'}"
    settings = Settings(database_url=url, artifact_dir=tmp_path / "artifacts")
    engine = create_database(url)
    migrate(engine)
    store = Store(engine, settings)
    alice = store.create_user("Alice")
    bob = store.create_user("Bob")
    app = create_app(settings, engine=engine)
    with TestClient(app) as client:
        yield SimpleNamespace(
            settings=settings, engine=engine, store=store, client=client,
            alice=alice, bob=bob, approval=approval, policy=policy,
            auth={"Authorization": f"Bearer {alice['api_key']}"},
            other={"Authorization": f"Bearer {bob['api_key']}"},
        )
    engine.dispose()
    if admin is not None:
        with admin.begin() as connection:
            connection.execute(sa.schema.DropSchema(schema, cascade=True))
        admin.dispose()


@pytest.fixture
def project(env):
    return env.client.post("/v1/projects", headers=env.auth, json={"name": "Film assets"}).json()["id"]


@pytest.fixture
def queued(env, project):
    response = env.client.post(f"/v1/projects/{project}/jobs/text", headers={**env.auth, "Idempotency-Key": "first"},
                               json={"prompt": "a wooden chair", "model_id": "test_model"})
    assert response.status_code == 202, response.text
    return response.json()["id"]


@pytest.fixture
def png():
    output = io.BytesIO()
    image = Image.new("RGB", (8, 8), "blue")
    image.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def triangle():
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    document = {
        "asset": {"version": "2.0"}, "buffers": [{"byteLength": len(positions)}],
        "bufferViews": [{"buffer": 0, "byteLength": len(positions)}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "type": "VEC3", "count": 3,
                       "min": [0, 0, 0], "max": [1, 1, 0]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0,
    }
    data = json.dumps(document).encode()
    data += b" " * (-len(data) % 4)
    chunks = struct.pack("<I4s", len(data), b"JSON") + data
    chunks += struct.pack("<I4s", len(positions), b"BIN\x00") + positions
    return struct.pack("<4sII", b"glTF", 2, len(chunks) + 12) + chunks
