"""Bounded, non-destructive artifact storage maintenance helpers."""
from __future__ import annotations

from dataclasses import asdict

from .storage import ArtifactStorage, StoredArtifactObject
from .store import Store


class ArtifactInventoryLimit(RuntimeError):
    """A bounded scan could not inspect the entire database/storage set."""


def scan_artifact_storage(
    store: Store,
    storage: ArtifactStorage,
    *,
    max_objects: int = 10_000,
) -> dict:
    """Compare the complete bounded storage inventory with artifact DB rows.

    This function never deletes or mutates storage/database state. If either
    side exceeds max_objects, it fails instead of producing false orphan or
    missing classifications from a partial scan.
    """
    if not 1 <= max_objects <= 1_000_000:
        raise ValueError("max_objects must be between 1 and 1,000,000")

    rows = store.artifact_records(limit=max_objects + 1)
    if len(rows) > max_objects:
        raise ArtifactInventoryLimit(
            "Database artifact count exceeds scan limit; rerun with a higher --max-objects"
        )

    inventory = storage.inventory(limit=max_objects)
    if inventory.truncated:
        raise ArtifactInventoryLimit(
            "Storage object count exceeds scan limit; rerun with a higher --max-objects"
        )

    by_id = {row["id"]: row for row in rows}
    valid_matches: dict[str, StoredArtifactObject] = {}
    orphans: list[dict] = []
    duplicates: list[dict] = []
    mismatches: list[dict] = []
    unrecognized: list[dict] = []

    for item in inventory.objects:
        if not item.recognized or item.artifact_id is None:
            unrecognized.append(asdict(item))
            continue

        row = by_id.get(item.artifact_id)
        if row is None:
            orphans.append(asdict(item))
            continue

        reasons: list[str] = []
        if item.owner_id is not None and item.owner_id != row["owner_id"]:
            reasons.append("owner_mismatch")
        if item.size_bytes != row["size_bytes"]:
            reasons.append("size_mismatch")
        if reasons:
            mismatches.append({**asdict(item), "reasons": reasons})
            continue

        if item.artifact_id in valid_matches:
            duplicates.append(asdict(item))
            continue
        valid_matches[item.artifact_id] = item

    missing = [
        {
            "artifact_id": row["id"],
            "owner_id": row["owner_id"],
            "size_bytes": row["size_bytes"],
        }
        for row in rows
        if row["id"] not in valid_matches
    ]

    return {
        "complete": True,
        "database_artifacts": len(rows),
        "storage_objects": len(inventory.objects),
        "matched_artifacts": len(valid_matches),
        "stored_database_bytes": sum(row["size_bytes"] for row in rows),
        "storage_inventory_bytes": sum(item.size_bytes for item in inventory.objects),
        "orphan_bytes": sum(item["size_bytes"] for item in orphans),
        "missing": missing,
        "orphans": orphans,
        "duplicates": duplicates,
        "mismatches": mismatches,
        "unrecognized": unrecognized,
        "destructive_action_taken": False,
    }
