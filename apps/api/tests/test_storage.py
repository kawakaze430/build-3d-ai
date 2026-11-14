import asyncio
import hashlib
import io
import time
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from build3d_api.config import Settings
from build3d_api.main import create_app
from build3d_api.storage import (
    ArtifactStorageError,
    FileSystemArtifactStorage,
    S3ArtifactStorage,
    artifact_object_key,
    create_artifact_storage,
)
from build3d_api.store import Store
from build3d_api.worker import Worker
from build3d_gateway.upstream import UpstreamGateway


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentLength, ContentType, Metadata):
        data = Body.read()
        assert len(data) == ContentLength
        self.objects[(Bucket, Key)] = {
            "data": data,
            "metadata": dict(Metadata),
            "content_type": ContentType,
        }
        return {"ETag": '"fixture"'}

    def head_object(self, *, Bucket, Key):
        item = self.objects[(Bucket, Key)]
        return {"ContentLength": len(item["data"]), "Metadata": item["metadata"]}

    def get_object(self, *, Bucket, Key):
        item = self.objects[(Bucket, Key)]
        return {
            "ContentLength": len(item["data"]),
            "Metadata": item["metadata"],
            "Body": io.BytesIO(item["data"]),
        }

    def delete_object(self, *, Bucket, Key):
        self.objects.pop((Bucket, Key), None)
        return {}


def test_filesystem_storage_uses_owner_scoped_key_and_legacy_read_fallback(tmp_path):
    source = tmp_path / "source.glb"
    data = b"verified-by-caller"
    source.write_bytes(data)
    owner = "1" * 32
    job = "2" * 32
    artifact = "3" * 32
    sha = hashlib.sha256(data).hexdigest()
    storage = FileSystemArtifactStorage(tmp_path / "artifacts")
    storage.prepare()
    storage.publish(
        artifact_id=artifact, owner_id=owner, job_id=job, source=source,
        sha256=sha, size_bytes=len(data),
    )
    record = {"id": artifact, "owner_id": owner, "sha256": sha, "size_bytes": len(data)}
    materialized = storage.materialize(record)
    assert materialized.path.read_bytes() == data
    assert materialized.path.relative_to(tmp_path / "artifacts").as_posix() == artifact_object_key(owner, artifact)
    storage.delete(artifact_id=artifact, owner_id=owner)
    assert not materialized.path.exists()

    legacy = tmp_path / "artifacts" / f"{artifact}.glb"
    legacy.write_bytes(data)
    assert storage.materialize(record).path == legacy


def test_s3_storage_round_trip_is_private_bounded_and_metadata_verified(tmp_path):
    client = FakeS3()
    storage = S3ArtifactStorage(
        bucket="private-artifacts",
        client=client,
        temp_dir=tmp_path / "materialized",
    )
    storage.prepare()
    source = tmp_path / "source.glb"
    data = b"object-data"
    source.write_bytes(data)
    owner = "a" * 32
    job = "b" * 32
    artifact = "c" * 32
    sha = hashlib.sha256(data).hexdigest()

    storage.publish(
        artifact_id=artifact, owner_id=owner, job_id=job, source=source,
        sha256=sha, size_bytes=len(data),
    )
    key = artifact_object_key(owner, artifact)
    assert ("private-artifacts", key) in client.objects
    assert client.objects[("private-artifacts", key)]["metadata"]["sha256"] == sha

    handle = storage.materialize(
        {"id": artifact, "owner_id": owner, "sha256": sha, "size_bytes": len(data)}
    )
    assert handle.path.read_bytes() == data
    handle.cleanup()
    assert not handle.path.exists()

    client.objects[("private-artifacts", key)]["metadata"]["sha256"] = "0" * 64
    with pytest.raises(ArtifactStorageError, match="checksum metadata"):
        storage.materialize(
            {"id": artifact, "owner_id": owner, "sha256": sha, "size_bytes": len(data)}
        )


def test_settings_gate_s3_and_factory_uses_injected_client(tmp_path):
    with pytest.raises(ValueError, match="S3_ARTIFACT_BUCKET"):
        Settings(
            database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
            artifact_storage_backend="s3",
        )
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
        artifact_storage_backend="s3",
        s3_artifact_bucket="private-artifacts",
    )
    assert isinstance(create_artifact_storage(settings, s3_client=FakeS3()), S3ArtifactStorage)


def test_s3_worker_to_api_download_keeps_glb_validation_and_tenant_boundary(
    env, queued, triangle, tmp_path
):
    client = FakeS3()
    storage = S3ArtifactStorage(
        bucket="private-artifacts",
        client=client,
        temp_dir=tmp_path / "materialized",
    )
    settings = replace(
        env.settings,
        artifact_storage_backend="s3",
        s3_artifact_bucket="private-artifacts",
    )
    clock = [time.time() + 10]

    def handler(request):
        assert request.headers["authorization"] == "Bearer private-upstream-token"
        if request.method == "POST":
            return httpx.Response(200, json={"job_id": "remote_1"})
        if request.url.path.endswith("/download"):
            return httpx.Response(200, content=triangle)
        return httpx.Response(200, json={"status": "completed"})

    upstream = UpstreamGateway(
        "http://fake-gpu",
        "private-upstream-token",
        transport=httpx.MockTransport(handler),
    )
    worker = Worker(
        Store(env.engine, settings),
        upstream,
        storage=storage,
        confirm_spend=True,
        clock=lambda: clock[0],
    )
    assert asyncio.run(worker.step())
    clock[0] += 10
    assert asyncio.run(worker.step())

    app = create_app(settings, engine=env.engine, storage=storage)
    with TestClient(app) as client_api:
        response = client_api.get(f"/v1/jobs/{queued}/download", headers=env.auth)
        assert response.status_code == 200
        assert response.content == triangle
        assert response.headers["x-artifact-sha256"] == hashlib.sha256(triangle).hexdigest()
        assert client_api.get(f"/v1/jobs/{queued}/download", headers=env.other).status_code == 404

        key = next(iter(client.objects))
        client.objects[key]["data"] = b"x" * len(triangle)
        corrupt = client_api.get(f"/v1/jobs/{queued}/download", headers=env.auth)
        assert corrupt.status_code == 503
        assert "checksum" not in corrupt.text.lower()
