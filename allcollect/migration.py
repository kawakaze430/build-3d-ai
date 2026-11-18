"""Non-destructive migration of DB-referenced artifacts from filesystem to S3-compatible storage."""
from __future__ import annotations

from dataclasses import dataclass

from build3d_gateway.glb_validation import GLBValidationError, inspect_glb

from .maintenance import ArtifactInventoryLimit
from .storage import (
    ArtifactStorageError,
    FileSystemArtifactStorage,
    S3ArtifactStorage,
)
from .store import Store


class ArtifactMigrationError(RuntimeError):
    """The migration cannot safely proceed without operator investigation."""


@dataclass(frozen=True)
class MigrationItem:
    artifact_id: str
    owner_id: str
    job_id: str
    sha256: str
    size_bytes: int


def _verify_materialized(storage, row: dict) -> None:
    handle = None
    try:
        handle = storage.materialize(row)
        with handle.path.open("rb") as stream:
            report = inspect_glb(stream)
        if report.sha256 != row["sha256"] or report.size_bytes != row["size_bytes"]:
            raise ArtifactMigrationError(
                f"artifact {row['id']} failed checksum/size verification"
            )
    except ArtifactMigrationError:
        raise
    except (OSError, GLBValidationError, ArtifactStorageError) as exc:
        raise ArtifactMigrationError(
            f"artifact {row['id']} could not be safely verified"
        ) from exc
    finally:
        if handle is not None:
            handle.cleanup()


def migrate_filesystem_to_s3(
    store: Store,
    source: FileSystemArtifactStorage,
    target: S3ArtifactStorage,
    *,
    max_objects: int = 10_000,
    execute_copy: bool = False,
) -> dict:
    """Plan or execute a copy-only migration.

    Source files and database rows are never modified. The active storage
    configuration is never switched. Every DB-referenced source object is
    structurally validated and checksum-verified before any copy begins.

    When execute_copy=True, the target is re-downloaded and fully verified
    after every PUT. A failure may leave already-copied private target objects;
    rerunning the command is safe because verified existing targets are skipped.
    """
    if not 1 <= max_objects <= 1_000_000:
        raise ValueError("max_objects must be between 1 and 1,000,000")

    rows = store.artifact_records(limit=max_objects + 1)
    if len(rows) > max_objects:
        raise ArtifactInventoryLimit(
            "Database artifact count exceeds migration limit; rerun with a higher --max-objects"
        )

    target_inventory = target.inventory(limit=max_objects)
    if target_inventory.truncated:
        raise ArtifactInventoryLimit(
            "Target storage object count exceeds migration limit; rerun with a higher --max-objects"
        )

    target_by_artifact = {}
    conflicts: list[dict] = []
    for item in target_inventory.objects:
        if not item.recognized or item.artifact_id is None:
            conflicts.append({
                "key": item.key,
                "reason": "unrecognized_target_object",
            })
            continue
        if item.artifact_id in target_by_artifact:
            conflicts.append({
                "artifact_id": item.artifact_id,
                "key": item.key,
                "reason": "duplicate_target_artifact",
            })
            continue
        target_by_artifact[item.artifact_id] = item

    source.prepare()
    planned: list[MigrationItem] = []
    existing_verified: list[str] = []
    source_failures: list[dict] = []

    # Verify every source and every already-existing target before copying
    # anything. This makes --execute-copy fail closed on known inconsistencies.
    for row in rows:
        try:
            _verify_materialized(source, row)
        except ArtifactMigrationError as exc:
            source_failures.append({"artifact_id": row["id"], "reason": str(exc)})
            continue

        existing = target_by_artifact.get(row["id"])
        if existing is None:
            planned.append(MigrationItem(
                artifact_id=row["id"],
                owner_id=row["owner_id"],
                job_id=row["job_id"],
                sha256=row["sha256"],
                size_bytes=row["size_bytes"],
            ))
            continue

        if existing.owner_id != row["owner_id"] or existing.size_bytes != row["size_bytes"]:
            conflicts.append({
                "artifact_id": row["id"],
                "key": existing.key,
                "reason": "target_owner_or_size_mismatch",
            })
            continue
        try:
            _verify_materialized(target, row)
        except ArtifactMigrationError as exc:
            conflicts.append({
                "artifact_id": row["id"],
                "key": existing.key,
                "reason": str(exc),
            })
            continue
        existing_verified.append(row["id"])

    ready = not source_failures and not conflicts
    copied: list[str] = []
    copy_failures: list[dict] = []

    if execute_copy and ready:
        for item in planned:
            row = {
                "id": item.artifact_id,
                "owner_id": item.owner_id,
                "job_id": item.job_id,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            source_handle = source.materialize(row)
            try:
                target.publish(
                    artifact_id=item.artifact_id,
                    owner_id=item.owner_id,
                    job_id=item.job_id,
                    source=source_handle.path,
                    sha256=item.sha256,
                    size_bytes=item.size_bytes,
                )
                _verify_materialized(target, row)
                copied.append(item.artifact_id)
            except (ArtifactStorageError, ArtifactMigrationError, OSError) as exc:
                copy_failures.append({
                    "artifact_id": item.artifact_id,
                    "reason": "target_copy_or_verification_failed",
                })
                break
            finally:
                source_handle.cleanup()

    return {
        "mode": "execute-copy" if execute_copy else "dry-run",
        "complete_database_scan": True,
        "database_artifacts": len(rows),
        "source_verified": len(rows) - len(source_failures),
        "target_existing_verified": len(existing_verified),
        "planned_copy_count": len(planned),
        "planned_copy_bytes": sum(item.size_bytes for item in planned),
        "copied_count": len(copied),
        "copied_artifact_ids": copied,
        "source_failures": source_failures,
        "target_conflicts": conflicts,
        "copy_failures": copy_failures,
        "ready_to_copy": ready,
        "source_deleted": False,
        "database_modified": False,
        "configuration_switched": False,
    }
