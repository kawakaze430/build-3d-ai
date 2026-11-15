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
from build3d_api.maintenance import ArtifactInventoryLimit, scan_artifact_storage
from build3d_api.migration import migrate_filesystem_to_s3
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
        self.put_calls = 0

    def put_object(self, *, Bucket, Key, Body, ContentLength, ContentType, Metadata):
        self.put_calls += 1
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

    def list_objects_v2(self, *, Bucket, Prefix, MaxKeys, ContinuationToken=None):
        keys = sorted(
            key for (bucket, key) in self.objects
            if bucket == Bucket and key.startswith(Prefix)
        )
        start = int(ContinuationToken or "0")
        selected = keys[start:start + MaxKeys]
        next_index = start + len(selected)
        truncated = next_index < len(keys)
        return {
            "Contents": [
                {"Key": key, "Size": len(self.objects[(Bucket, key)]["data"])}
                for key in selected
            ],
            "IsTruncated": truncated,
            **({"NextContinuationToken": str(next_index)} if truncated else {}),
        }


class StaticArtifactRows:
    def __init__(self, rows):
        self.rows = rows

    def artifact_records(self, *, limit):
        return self.rows[:limit]


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


def test_filesystem_inventory_and_scanner_are_bounded_and_non_destructive(tmp_path):
    root = tmp_path / "artifacts"
    storage = FileSystemArtifactStorage(root)
    storage.prepare()
    owner = "1" * 32
    other_owner = "2" * 32
    current = "a" * 32
    orphan = "b" * 32
    missing = "c" * 32
    mismatch = "d" * 32
    data = b"12345678"
    source = tmp_path / "source.glb"
    source.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()

    for artifact_id, artifact_owner in ((current, owner), (orphan, owner), (mismatch, other_owner)):
        storage.publish(
            artifact_id=artifact_id,
            owner_id=artifact_owner,
            job_id="9" * 32,
            source=source,
            sha256=sha,
            size_bytes=len(data),
        )

    # A legacy duplicate and malformed key are reported, never deleted.
    (root / f"{current}.glb").write_bytes(data)
    malformed = root / "build3d" / "v1" / "artifacts" / "bad-owner" / "not-an-id.glb"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_bytes(b"x")

    rows = [
        {"id": current, "owner_id": owner, "size_bytes": len(data)},
        {"id": missing, "owner_id": owner, "size_bytes": len(data)},
        {"id": mismatch, "owner_id": owner, "size_bytes": len(data)},
    ]
    report = scan_artifact_storage(StaticArtifactRows(rows), storage, max_objects=20)
    assert report["complete"] is True
    assert report["destructive_action_taken"] is False
    assert len(report["orphans"]) == 1
    assert report["orphans"][0]["artifact_id"] == orphan
    assert len(report["duplicates"]) == 1
    assert len(report["mismatches"]) == 1
    assert "owner_mismatch" in report["mismatches"][0]["reasons"]
    assert len(report["unrecognized"]) == 1
    assert {item["artifact_id"] for item in report["missing"]} == {missing, mismatch}
    assert (root / f"{current}.glb").exists()
    assert malformed.exists()

    with pytest.raises(ArtifactInventoryLimit, match="Database artifact count"):
        scan_artifact_storage(StaticArtifactRows(rows), storage, max_objects=1)
    with pytest.raises(ArtifactInventoryLimit, match="Storage object count"):
        scan_artifact_storage(StaticArtifactRows(rows[:1]), storage, max_objects=1)


def test_s3_inventory_paginates_and_respects_hard_scan_limit(tmp_path):
    client = FakeS3()
    storage = S3ArtifactStorage(bucket="private-artifacts", client=client)
    source = tmp_path / "source.glb"
    source.write_bytes(b"1234")
    sha = hashlib.sha256(b"1234").hexdigest()
    owner = "a" * 32
    for index in range(3):
        storage.publish(
            artifact_id=f"{index + 1:032x}",
            owner_id=owner,
            job_id="f" * 32,
            source=source,
            sha256=sha,
            size_bytes=4,
        )

    limited = storage.inventory(limit=2)
    assert limited.truncated is True
    assert len(limited.objects) == 2
    full = storage.inventory(limit=3)
    assert full.truncated is False
    assert len(full.objects) == 3
    assert all(item.recognized for item in full.objects)


def test_filesystem_to_s3_migration_is_dry_run_by_default_and_copy_only(
    env, queued, triangle, tmp_path
):
    artifact_id = "e" * 32
    owner_id = env.alice["user_id"]
    sha = hashlib.sha256(triangle).hexdigest()
    source_root = tmp_path / "legacy-artifacts"
    source_root.mkdir()
    # Exercise the pre-abstraction flat path; migration must still find it.
    legacy = source_root / f"{artifact_id}.glb"
    legacy.write_bytes(triangle)
    with env.engine.begin() as conn:
        from build3d_api.db import artifacts
        conn.execute(artifacts.insert().values(
            id=artifact_id,
            job_id=queued,
            owner_id=owner_id,
            sha256=sha,
            size_bytes=len(triangle),
            mesh_count=1,
            created_at=time.time(),
        ))

    s3_client = FakeS3()
    source = FileSystemArtifactStorage(source_root)
    target = S3ArtifactStorage(bucket="migration-target", client=s3_client)

    dry = migrate_filesystem_to_s3(env.store, source, target, max_objects=10)
    assert dry["mode"] == "dry-run"
    assert dry["ready_to_copy"] is True
    assert dry["planned_copy_count"] == 1
    assert dry["copied_count"] == 0
    assert dry["source_deleted"] is False
    assert dry["database_modified"] is False
    assert s3_client.put_calls == 0
    assert legacy.exists()

    copied = migrate_filesystem_to_s3(
        env.store, source, target, max_objects=10, execute_copy=True
    )
    assert copied["ready_to_copy"] is True
    assert copied["copied_count"] == 1
    assert copied["copied_artifact_ids"] == [artifact_id]
    assert s3_client.put_calls == 1
    assert legacy.exists()

    # Idempotent rerun verifies the existing target and performs no second PUT.
    rerun = migrate_filesystem_to_s3(
        env.store, source, target, max_objects=10, execute_copy=True
    )
    assert rerun["planned_copy_count"] == 0
    assert rerun["target_existing_verified"] == 1
    assert rerun["copied_count"] == 0
    assert s3_client.put_calls == 1
    assert legacy.exists()


def test_filesystem_to_s3_migration_fails_closed_on_corrupt_source_or_target(
    env, queued, triangle, tmp_path
):
    artifact_id = "d" * 32
    owner_id = env.alice["user_id"]
    sha = hashlib.sha256(triangle).hexdigest()
    source_root = tmp_path / "source-artifacts"
    source = FileSystemArtifactStorage(source_root)
    source.prepare()
    source_path = source_root / f"{artifact_id}.glb"
    source_path.write_bytes(triangle)
    with env.engine.begin() as conn:
        from build3d_api.db import artifacts
        conn.execute(artifacts.insert().values(
            id=artifact_id,
            job_id=queued,
            owner_id=owner_id,
            sha256=sha,
            size_bytes=len(triangle),
            mesh_count=1,
            created_at=time.time(),
        ))

    s3_client = FakeS3()
    target = S3ArtifactStorage(bucket="migration-target", client=s3_client)

    source_path.write_bytes(b"x" * len(triangle))
    source_bad = migrate_filesystem_to_s3(
        env.store, source, target, max_objects=10, execute_copy=True
    )
    assert source_bad["ready_to_copy"] is False
    assert source_bad["source_failures"]
    assert s3_client.put_calls == 0

    source_path.write_bytes(triangle)
    initial = migrate_filesystem_to_s3(
        env.store, source, target, max_objects=10, execute_copy=True
    )
    assert initial["copied_count"] == 1

    key = artifact_object_key(owner_id, artifact_id)
    s3_client.objects[("migration-target", key)]["data"] = b"x" * len(triangle)
    target_bad = migrate_filesystem_to_s3(
        env.store, source, target, max_objects=10, execute_copy=True
    )
    assert target_bad["ready_to_copy"] is False
    assert target_bad["target_conflicts"]
    assert s3_client.put_calls == 1
    assert source_path.read_bytes() == triangle
