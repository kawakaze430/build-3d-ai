"""Fail-closed model approvals for owner-controlled 3D inference.

This file enforces operator-reviewed configuration. It does not perform legal
review of source code, trained weights, training data or GPU dependencies.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

from fastapi import HTTPException

MODEL_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")


def approved_model_records() -> dict[str, dict]:
    configured = os.getenv("MODEL_APPROVAL_FILE")
    policy_file = Path(configured) if configured else Path(__file__).with_name("model-approvals.json")
    try:
        document = json.loads(policy_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Model approval policy unavailable") from exc

    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or not isinstance(document.get("approved_models"), list)
    ):
        raise HTTPException(status_code=503, detail="Invalid model approval policy")

    identifiers: set[str] = set()
    records: dict[str, dict] = {}
    try:
        for entry in document["approved_models"]:
            if not isinstance(entry, dict):
                raise ValueError("Malformed approval entry")
            model_id = entry.get("model_id")
            if not isinstance(model_id, str) or not MODEL_NAME.fullmatch(model_id):
                raise ValueError("Invalid model ID")
            if model_id in identifiers:
                raise ValueError("Duplicate model ID")
            if entry.get("commercial_saas_rights_verified") is not True:
                raise ValueError("Commercial rights not verified")
            reference = entry.get("license_review")
            if not isinstance(reference, str) or not reference.startswith("docs/"):
                raise ValueError("Missing license review")
            reviewer = entry.get("reviewed_by")
            if not isinstance(reviewer, str) or not reviewer.strip():
                raise ValueError("Missing reviewer")
            reviewed_on = entry.get("reviewed_on")
            if not isinstance(reviewed_on, str):
                raise ValueError("Missing review date")
            date.fromisoformat(reviewed_on)
            upstream_sha = entry.get("upstream_commit_sha")
            checkpoint_sha = entry.get("checkpoint_sha256")
            if not isinstance(upstream_sha, str) or not SHA1.fullmatch(upstream_sha):
                raise ValueError("Invalid source hash")
            if not isinstance(checkpoint_sha, str) or not SHA256.fullmatch(checkpoint_sha):
                raise ValueError("Invalid weight hash")
            identifiers.add(model_id)
            records[model_id] = entry.copy()
    except (TypeError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Invalid model approval policy") from exc

    return records


def approved_model_ids() -> frozenset[str]:
    return frozenset(approved_model_records())


def require_model_approval(model_preference: str | None) -> str:
    if model_preference is None or not model_preference.strip():
        raise HTTPException(status_code=422, detail="Explicit model_preference is required")
    if not MODEL_NAME.fullmatch(model_preference):
        raise HTTPException(status_code=422, detail="Invalid model identifier")

    approvals = approved_model_ids()
    if not approvals:
        raise HTTPException(
            status_code=503,
            detail="Generation disabled: no model has passed deployment approval",
        )
    if model_preference not in approvals:
        raise HTTPException(status_code=403, detail="Requested model is not approved")
    return model_preference
