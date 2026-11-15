"""Private artifact storage backends.

Generated assets are untrusted until the gateway has structurally validated them,
and downloads are revalidated against the database checksum before being served.
Storage implementations never create public URLs.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol
from urllib.parse import urlsplit

from build3d_gateway.glb_validation import MAX_GLB_BYTES

from .config import Settings


_ID = re.compile(r"^[0-9a-f]{32}$")


class ArtifactStorageError(OSError):
    """A storage operation failed without exposing provider credentials/details."""


@dataclass(frozen=True)
class MaterializedArtifact:
    path: Path
    cleanup: Callable[[], None]


@dataclass(frozen=True)
class StoredArtifactObject:
    key: str
    size_bytes: int
    owner_id: str | None
    artifact_id: str | None
    legacy: bool = False
    recognized: bool = True


@dataclass(frozen=True)
class StorageInventory:
    objects: tuple[StoredArtifactObject, ...]
    truncated: bool


class ArtifactStorage(Protocol):
    def prepare(self) -> None: ...

    def publish(
        self,
        *,
        artifact_id: str,
        owner_id: str,
        job_id: str,
        source: str | Path,
        sha256: str,
        size_bytes: int,
    ) -> None: ...

    def materialize(self, record: dict) -> MaterializedArtifact: ...

    def delete(self, *, artifact_id: str, owner_id: str) -> None: ...

    def inventory(self, *, limit: int) -> StorageInventory: ...


def _safe_id(value: str, field: str) -> str:
    if not _ID.fullmatch(value):
        raise ArtifactStorageError(f"Invalid {field}")
    return value


def artifact_object_key(owner_id: str, artifact_id: str, *, prefix: str = "build3d/v1/artifacts") -> str:
    owner_id = _safe_id(owner_id, "owner ID")
    artifact_id = _safe_id(artifact_id, "artifact ID")
    clean = prefix.strip("/")
    if not clean or "\\" in clean or any(part in {"", ".", ".."} for part in clean.split("/")):
        raise ArtifactStorageError("Invalid artifact storage prefix")
    return f"{clean}/{owner_id}/{artifact_id}.glb"


def _inventory_limit(limit: int) -> int:
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1_000_000:
        raise ArtifactStorageError("Artifact inventory limit must be between 1 and 1,000,000")
    return limit


def _parse_current_key(key: str, prefix: str) -> tuple[str, str] | None:
    clean = prefix.strip("/")
    pattern = re.compile(
        rf"^{re.escape(clean)}/(?P<owner>[0-9a-f]{{32}})/(?P<artifact>[0-9a-f]{{32}})\\.glb$"
    )
    match = pattern.fullmatch(key)
    if match is None:
        return None
    return match.group("owner"), match.group("artifact")


class FileSystemArtifactStorage:
    """Atomic local storage with a legacy flat-path read fallback."""

    def __init__(self, root: Path, *, prefix: str = "build3d/v1/artifacts"):
        self.root = Path(root)
        self.prefix = prefix

    def prepare(self) -> None:
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _path(self, owner_id: str, artifact_id: str) -> Path:
        return self.root / artifact_object_key(owner_id, artifact_id, prefix=self.prefix)

    def _legacy_path(self, artifact_id: str) -> Path:
        return self.root / f"{_safe_id(artifact_id, 'artifact ID')}.glb"

    def publish(
        self,
        *,
        artifact_id: str,
        owner_id: str,
        job_id: str,
        source: str | Path,
        sha256: str,
        size_bytes: int,
    ) -> None:
        _safe_id(job_id, "job ID")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256) or not 0 < size_bytes <= MAX_GLB_BYTES:
            raise ArtifactStorageError("Invalid verified artifact metadata")
        source_path = Path(source)
        try:
            if source_path.stat().st_size != size_bytes:
                raise ArtifactStorageError("Verified artifact size changed before publication")
            destination = self._path(owner_id, artifact_id)
            directory = destination.parent
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            staged: str | None = None
            try:
                with tempfile.NamedTemporaryFile(dir=directory, suffix=".part", delete=False) as output:
                    staged = output.name
                    with source_path.open("rb") as input_file:
                        shutil.copyfileobj(input_file, output)
                    output.flush()
                    os.fsync(output.fileno())
                if Path(staged).stat().st_size != size_bytes:
                    raise ArtifactStorageError("Artifact size changed while staging")
                os.replace(staged, destination)
                staged = None
                if hasattr(os, "O_DIRECTORY"):
                    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
            finally:
                if staged is not None:
                    Path(staged).unlink(missing_ok=True)
        except ArtifactStorageError:
            raise
        except OSError as exc:
            raise ArtifactStorageError("Filesystem artifact publication failed") from exc

    def materialize(self, record: dict) -> MaterializedArtifact:
        artifact_id = _safe_id(record["id"], "artifact ID")
        owner_id = _safe_id(record["owner_id"], "owner ID")
        path = self._path(owner_id, artifact_id)
        if not path.exists():
            # Files created before the storage abstraction used ARTIFACT_DIR/<id>.glb.
            path = self._legacy_path(artifact_id)
        try:
            if path.is_symlink() or not path.is_file():
                raise ArtifactStorageError("Stored artifact is unavailable")
        except OSError as exc:
            raise ArtifactStorageError("Stored artifact is unavailable") from exc
        return MaterializedArtifact(path=path, cleanup=lambda: None)

    def delete(self, *, artifact_id: str, owner_id: str) -> None:
        try:
            self._path(owner_id, artifact_id).unlink(missing_ok=True)
            self._legacy_path(artifact_id).unlink(missing_ok=True)
        except OSError as exc:
            raise ArtifactStorageError("Filesystem artifact cleanup failed") from exc

    def inventory(self, *, limit: int) -> StorageInventory:
        limit = _inventory_limit(limit)
        items: list[StoredArtifactObject] = []
        base = self.root / self.prefix.strip("/")
        try:
            candidates: list[Path] = []
            if base.exists():
                candidates.extend(path for path in base.rglob("*.glb"))
            candidates.extend(self.root.glob("*.glb"))
            for path in sorted(candidates, key=lambda item: item.as_posix()):
                key = path.relative_to(self.root).as_posix()
                is_symlink = path.is_symlink()
                try:
                    size = path.lstat().st_size
                    is_regular = not is_symlink and path.is_file()
                except OSError:
                    size = -1
                    is_regular = False
                parsed = _parse_current_key(key, self.prefix)
                legacy = path.parent == self.root
                artifact_id = path.stem if legacy and _ID.fullmatch(path.stem) else None
                if parsed is not None and is_regular and size >= 0:
                    owner_id, artifact_id = parsed
                    item = StoredArtifactObject(key, size, owner_id, artifact_id)
                elif legacy and artifact_id is not None and is_regular and size >= 0:
                    item = StoredArtifactObject(key, size, None, artifact_id, legacy=True)
                else:
                    item = StoredArtifactObject(
                        key, max(size, 0), None, artifact_id, legacy=legacy, recognized=False
                    )
                items.append(item)
                if len(items) > limit:
                    return StorageInventory(tuple(items[:limit]), truncated=True)
        except OSError as exc:
            raise ArtifactStorageError("Filesystem artifact inventory failed") from exc
        return StorageInventory(tuple(items), truncated=False)


class S3ArtifactStorage:
    """Private S3-compatible storage.

    The client is injectable so the backend is testable without network access.
    Production clients use boto3's standard credential chain (role/workload
    identity/environment) and credentials are never passed to browsers.
    """

    def __init__(
        self,
        *,
        bucket: str,
        client,
        prefix: str = "build3d/v1/artifacts",
        temp_dir: Path | None = None,
    ):
        if not re.fullmatch(r"[A-Za-z0-9.-]{3,255}", bucket):
            raise ArtifactStorageError("Invalid S3 artifact bucket")
        # Validate prefix eagerly.
        artifact_object_key("0" * 32, "0" * 32, prefix=prefix)
        self.bucket = bucket
        self.client = client
        self.prefix = prefix.strip("/")
        self.temp_dir = Path(temp_dir) if temp_dir is not None else None

    def prepare(self) -> None:
        if self.temp_dir is not None:
            self.temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        # Deliberately do not create/probe a paid or remote bucket at API startup.

    def _key(self, owner_id: str, artifact_id: str) -> str:
        return artifact_object_key(owner_id, artifact_id, prefix=self.prefix)

    def publish(
        self,
        *,
        artifact_id: str,
        owner_id: str,
        job_id: str,
        source: str | Path,
        sha256: str,
        size_bytes: int,
    ) -> None:
        _safe_id(job_id, "job ID")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256) or not 0 < size_bytes <= MAX_GLB_BYTES:
            raise ArtifactStorageError("Invalid verified artifact metadata")
        key = self._key(owner_id, artifact_id)
        source_path = Path(source)
        try:
            if source_path.stat().st_size != size_bytes:
                raise ArtifactStorageError("Verified artifact size changed before publication")
            metadata = {
                "sha256": sha256,
                "owner-id": owner_id,
                "job-id": job_id,
                "artifact-id": artifact_id,
            }
            with source_path.open("rb") as body:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=body,
                    ContentLength=size_bytes,
                    ContentType="model/gltf-binary",
                    Metadata=metadata,
                )
            head = self.client.head_object(Bucket=self.bucket, Key=key)
            remote_metadata = {str(k).lower(): str(v) for k, v in (head.get("Metadata") or {}).items()}
            if int(head.get("ContentLength", -1)) != size_bytes or remote_metadata.get("sha256") != sha256:
                try:
                    self.client.delete_object(Bucket=self.bucket, Key=key)
                except Exception:
                    pass
                raise ArtifactStorageError("Object storage publication verification failed")
        except ArtifactStorageError:
            raise
        except Exception as exc:
            # Do not bubble provider messages: endpoint URLs/credentials can appear in them.
            raise ArtifactStorageError("Object storage artifact publication failed") from exc

    def materialize(self, record: dict) -> MaterializedArtifact:
        artifact_id = _safe_id(record["id"], "artifact ID")
        owner_id = _safe_id(record["owner_id"], "owner ID")
        expected_sha = str(record["sha256"])
        expected_size = int(record["size_bytes"])
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or not 0 < expected_size <= MAX_GLB_BYTES:
            raise ArtifactStorageError("Invalid persisted artifact metadata")

        key = self._key(owner_id, artifact_id)
        path: Path | None = None
        body = None
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            if int(response.get("ContentLength", -1)) != expected_size:
                raise ArtifactStorageError("Stored object size does not match persisted metadata")
            metadata = {str(k).lower(): str(v) for k, v in (response.get("Metadata") or {}).items()}
            if metadata.get("sha256") != expected_sha:
                raise ArtifactStorageError("Stored object checksum metadata does not match")
            body = response["Body"]
            if self.temp_dir is not None:
                self.temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                suffix=".glb",
                prefix="build3d-",
                dir=self.temp_dir,
                delete=False,
            ) as output:
                path = Path(output.name)
                count = 0
                while True:
                    chunk = body.read(min(256 * 1024, expected_size - count + 1))
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > expected_size:
                        raise ArtifactStorageError("Stored object exceeded persisted size")
                    output.write(chunk)
                if count != expected_size:
                    raise ArtifactStorageError("Stored object ended before persisted size")
                output.flush()
                os.fsync(output.fileno())
            return MaterializedArtifact(path=path, cleanup=lambda: path.unlink(missing_ok=True))
        except ArtifactStorageError:
            if path is not None:
                path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            if path is not None:
                path.unlink(missing_ok=True)
            raise ArtifactStorageError("Object storage artifact retrieval failed") from exc
        finally:
            if body is not None:
                try:
                    body.close()
                except Exception:
                    pass

    def delete(self, *, artifact_id: str, owner_id: str) -> None:
        key = self._key(owner_id, artifact_id)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            raise ArtifactStorageError("Object storage artifact cleanup failed") from exc

    def inventory(self, *, limit: int) -> StorageInventory:
        limit = _inventory_limit(limit)
        objects: list[StoredArtifactObject] = []
        token: str | None = None
        try:
            while len(objects) <= limit:
                kwargs = {
                    "Bucket": self.bucket,
                    "Prefix": self.prefix + "/",
                    "MaxKeys": min(1000, limit + 1 - len(objects)),
                }
                if token is not None:
                    kwargs["ContinuationToken"] = token
                page = self.client.list_objects_v2(**kwargs)
                for entry in page.get("Contents") or []:
                    key = str(entry.get("Key", ""))
                    size = int(entry.get("Size", -1))
                    parsed = _parse_current_key(key, self.prefix)
                    if parsed is None or size < 0:
                        objects.append(StoredArtifactObject(
                            key=key,
                            size_bytes=max(size, 0),
                            owner_id=None,
                            artifact_id=None,
                            recognized=False,
                        ))
                    else:
                        owner_id, artifact_id = parsed
                        objects.append(StoredArtifactObject(
                            key=key,
                            size_bytes=size,
                            owner_id=owner_id,
                            artifact_id=artifact_id,
                        ))
                    if len(objects) > limit:
                        return StorageInventory(tuple(objects[:limit]), truncated=True)
                if not page.get("IsTruncated"):
                    break
                token = page.get("NextContinuationToken")
                if not isinstance(token, str) or not token:
                    raise ArtifactStorageError("Object storage inventory pagination is invalid")
        except ArtifactStorageError:
            raise
        except Exception as exc:
            raise ArtifactStorageError("Object storage artifact inventory failed") from exc
        return StorageInventory(tuple(objects), truncated=False)


def _boto_client(settings: Settings):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "S3 artifact storage requires the optional build3d-api[s3] dependency"
        ) from exc
    options = {}
    if settings.s3_endpoint_url:
        options["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_region:
        options["region_name"] = settings.s3_region
    return boto3.client("s3", **options)


def create_artifact_storage(settings: Settings, *, s3_client=None) -> ArtifactStorage:
    if settings.artifact_storage_backend == "filesystem":
        return FileSystemArtifactStorage(settings.artifact_dir, prefix=settings.artifact_storage_prefix)
    if settings.artifact_storage_backend == "s3":
        client = s3_client if s3_client is not None else _boto_client(settings)
        return S3ArtifactStorage(
            bucket=settings.s3_artifact_bucket or "",
            client=client,
            prefix=settings.artifact_storage_prefix,
        )
    raise RuntimeError("Unsupported artifact storage backend")
