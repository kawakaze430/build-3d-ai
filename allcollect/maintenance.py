"""Bounded, non-destructive artifact storage maintenance helpers."""
from __future__ import annotations

from dataclasses import asdict

from .storage import ArtifactStorage, StoredArtifactObject
from .store import Store


class ArtifactInventoryLimit(RuntimeError):
    """A bounded scan could not inspect the entire database/storage set."""

def _inventory_snapshot(
    store: Store, storage: ArtifactStorage, max_objects: int,
) -> tuple[list[dict], tuple[StoredArtifactObject, ...]]:
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
            "Storage inventory exceeds scan limit; rerun with a higher --max-objects"
        )
    return rows, inventory.objects


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
    rows, objects = _inventory_snapshot(store, storage, max_objects)

    by_id = {row["id"]: row for row in rows}
    valid_matches: dict[str, StoredArtifactObject] = {}
    orphans: list[dict] = []
    duplicates: list[dict] = []
    mismatches: list[dict] = []
    unrecognized: list[dict] = []

    for item in objects:
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
        "storage_objects": len(objects),
        "matched_artifacts": len(valid_matches),
        "stored_database_bytes": sum(row["size_bytes"] for row in rows),
        "storage_inventory_bytes": sum(item.size_bytes for item in objects),
        "orphan_bytes": sum(item["size_bytes"] for item in orphans),
        "missing": missing,
        "orphans": orphans,
        "duplicates": duplicates,
        "mismatches": mismatches,
        "unrecognized": unrecognized,
        "destructive_action_taken": False,
    }


def plan_artifact_retention(
    store: Store, storage: ArtifactStorage, *, owner_id: str, max_objects: int = 10_000,
) -> dict:
    """Report one user's retained inputs and artifacts without authorizing removal."""
    rows, objects = _inventory_snapshot(store, storage, max_objects)
    inputs = store.retained_job_inputs(owner_id, limit=max_objects + 1)
    if len(inputs) > max_objects:
        raise ArtifactInventoryLimit(
            "Persisted job input count exceeds scan limit; rerun with a higher --max-objects"
        )

    all_refs = {row["id"]: row for row in rows}
    owned_refs = {
        item_id: {**row, "objects": []}
        for item_id, row in all_refs.items() if row["owner_id"] == owner_id
    }
    operator_review = []
    for item in objects:
        known_owner = item.owner_id == owner_id
        known_legacy = item.legacy and item.artifact_id in owned_refs
        if not (known_owner or known_legacy):
            continue
        row = owned_refs.get(item.artifact_id)
        if row is None:
            reason = "different_owner_reference" if item.artifact_id in all_refs else "no_database_reference"
            operator_review.append({"key": item.key, "size_bytes": item.size_bytes, "reason": reason})
            continue
        consistent = item.recognized and item.size_bytes == row["size_bytes"]
        row["objects"].append({
            "key": item.key, "layout": "legacy" if item.legacy else "current",
            "size_bytes": item.size_bytes, "metadata_matches": consistent,
        })

    for row in owned_refs.values():
        row["presence"] = (
            "present" if any(item["metadata_matches"] for item in row["objects"])
            else "metadata_mismatch" if row["objects"]
            else "missing"
        )
    return {
        "owner_id": owner_id,
        "complete": True,
        "referenced_artifacts": list(owned_refs.values()),
        "persisted_job_inputs": inputs,
        "objects_for_operator_review": operator_review,
        "content_checksums_verified": False,
        "deletion_candidates": [],
        "destructive_action_taken": False,
    }
