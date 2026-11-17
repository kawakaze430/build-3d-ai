"""Validate and summarize one benchmark run without executing a model."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

VERSION = 1
EVIDENCE_KINDS = ("fixture", "measured")
OUTCOMES = ("failed", "rejected", "accepted")
COST_COMPONENTS = ("compute", "storage", "other")
SCORE_FIELDS = ("geometry", "materials", "hidden_view_consistency", "usability")
VIEWS = ("front", "side", "back")
SHA256 = re.compile(r"[0-9a-f]{64}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def reject_nonfinite(value):
    raise ValueError(f"invalid JSON number: {value}")


def finite_float(value: str) -> float:
    result = float(value)
    if not isfinite(result):
        reject_nonfinite(value)
    return result


def parse_record(raw: bytes, label: str) -> dict:
    record = json.loads(
        raw, object_pairs_hook=unique_object, parse_constant=reject_nonfinite, parse_float=finite_float
    )
    if not isinstance(record, dict) or type(record.get("schema_version")) is not int:
        raise ValueError(f"{label} must be a JSON object with an integer schema_version")
    if record["schema_version"] != VERSION:
        raise ValueError(f"{label} uses an unsupported schema_version")
    if record.get("evidence_kind") not in EVIDENCE_KINDS:
        raise ValueError(f"{label} evidence_kind must be fixture or measured")
    return record


def object_field(record: dict, key: str) -> dict:
    value = record.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def object_list(record: dict, key: str) -> list[dict]:
    value = record.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must be a nonempty list of records")
    return value


def text_field(record: dict, key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be nonempty text")
    return value


def integer_field(record: dict, key: str, *, minimum: int = 0) -> int:
    value = record.get(key)
    if type(value) is not int or value < minimum:
        raise ValueError(f"{key} must be an integer of at least {minimum}")
    return value


def hash_field(record: dict, key: str) -> str:
    value = text_field(record, key)
    if not SHA256.fullmatch(value):
        raise ValueError(f"{key} must be a lowercase SHA-256")
    return value


def manifest_samples(manifest: dict) -> dict[str, str]:
    samples = {}
    hashes = set()
    for sample in object_list(manifest, "samples"):
        sample_id = text_field(sample, "id")
        input_hash = hash_field(sample, "input_sha256")
        if sample_id in samples or input_hash in hashes:
            raise ValueError(f"duplicate manifest sample: {sample_id}")
        if sample.get("license_approved") is not True or sample.get("held_out") is not True:
            raise ValueError(f"sample {sample_id} requires approved input rights and held-out status")
        text_field(sample, "rights_reference")
        samples[sample_id] = text_field(sample, "category")
        hashes.add(input_hash)
    return samples


def validate_run(run: dict) -> None:
    for field in ("id", "source_revision", "model_revision", "hardware"):
        text_field(run, field)
    for field in ("checkpoint_sha256", "runtime_sha256"):
        hash_field(run, field)
    started_at = datetime.fromisoformat(text_field(run, "started_at"))
    if started_at.utcoffset() is None:
        raise ValueError("started_at requires a timezone")
    object_field(run, "parameters")


def validate_attempt(record: dict) -> None:
    for field in ("seed", "latency_ms", "gpu_ms", "peak_vram_mib", "artist_correction_seconds"):
        integer_field(record, field)
    cost = object_field(record, "cost_microusd")
    if cost.keys() != set(COST_COMPONENTS):
        raise ValueError("cost_microusd requires exactly compute, storage and other")
    for field in COST_COMPONENTS:
        integer_field(cost, field)
    outcome = record.get("outcome")
    if outcome not in OUTCOMES:
        raise ValueError("outcome must be failed, rejected or accepted")
    if outcome == "failed":
        text_field(record, "failure_stage")
        text_field(record, "reason")
        if "output_sha256" in record:
            hash_field(record, "output_sha256")
        return

    hash_field(record, "output_sha256")
    views = object_field(record, "view_sha256")
    for view in VIEWS:
        hash_field(views, view)
    scores = object_field(record, "quality_scores")
    if scores.keys() != set(SCORE_FIELDS):
        raise ValueError("quality_scores requires geometry, materials, hidden_view_consistency and usability")
    for field in SCORE_FIELDS:
        if integer_field(scores, field, minimum=1) > 5:
            raise ValueError(f"{field} score must be in the range 1–5")
    text_field(record, "rating_notes")
    for field in ("structural_glb_passed", "blender_import_passed"):
        if type(record.get(field)) is not bool:
            raise ValueError(f"{field} must be a boolean")
        if outcome == "accepted" and record[field] is not True:
            raise ValueError(f"accepted output requires {field}")
    if outcome == "rejected":
        text_field(record, "reason")


def run_attempts(results: dict, samples: dict[str, str]) -> dict[str, list[dict]]:
    by_sample = defaultdict(dict)
    for record in object_list(results, "attempts"):
        sample_id = text_field(record, "sample_id")
        attempt_index = integer_field(record, "attempt_index", minimum=1)
        if sample_id not in samples:
            raise ValueError(f"attempt for sample missing from manifest: {sample_id}")
        if attempt_index in by_sample[sample_id]:
            raise ValueError(f"duplicate attempt: {sample_id} #{attempt_index}")
        try:
            validate_attempt(record)
        except ValueError as exc:
            raise ValueError(f"{sample_id} attempt {attempt_index}: {exc}") from exc
        by_sample[sample_id][attempt_index] = record

    missing = sorted(samples.keys() - by_sample.keys())
    if missing:
        raise ValueError(f"missing attempts for: {', '.join(missing)}")
    ordered = {}
    for sample_id, attempts in by_sample.items():
        indices = sorted(attempts)
        if indices != list(range(1, len(indices) + 1)):
            raise ValueError(f"{sample_id} attempt indices must be consecutive starting at 1")
        ordered[sample_id] = [attempts[index] for index in indices]
        if any(record["outcome"] == "accepted" for record in ordered[sample_id][:-1]):
            raise ValueError(f"{sample_id} has additional attempts after acceptance")
    return ordered


def usd(microusd: int) -> str:
    units, remainder = divmod(microusd, 1_000_000)
    return f"{units}.{remainder:06d}"


def summarize(manifest_bytes: bytes, result_bytes: bytes) -> dict:
    manifest = parse_record(manifest_bytes, "manifest")
    results = parse_record(result_bytes, "result")
    manifest_hash = sha256(manifest_bytes).hexdigest()
    if hash_field(results, "input_manifest_sha256") != manifest_hash:
        raise ValueError("input_manifest_sha256 does not match the manifest bytes")
    if results["evidence_kind"] != manifest["evidence_kind"]:
        raise ValueError("manifest and result evidence kinds differ")
    samples = manifest_samples(manifest)
    run = object_field(results, "run")
    validate_run(run)
    by_sample = run_attempts(results, samples)

    attempts = [attempt for records in by_sample.values() for attempt in records]
    accepted = {
        sample_id for sample_id, records in by_sample.items()
        if records[-1]["outcome"] == "accepted"
    }
    by_category = defaultdict(Counter)
    for sample_id, category in samples.items():
        counts = by_category[category]
        counts["samples"] += 1
        counts["accepted"] += sample_id in accepted
    costs = {
        field: sum(attempt["cost_microusd"][field] for attempt in attempts)
        for field in COST_COMPONENTS
    }
    total_cost = sum(costs.values())
    average_cost = (total_cost * 2 + len(accepted)) // (2 * len(accepted)) if accepted else None
    retry_cost = sum(sum(a["cost_microusd"].values()) for a in attempts if a["attempt_index"] > 1)

    latency = sorted(a["latency_ms"] for a in attempts)
    rated = [a["quality_scores"] for a in attempts if a["outcome"] != "failed"]
    attempts_by_outcome = Counter(a["outcome"] for a in attempts)
    failures_by_stage = Counter(a["failure_stage"] for a in attempts if a["outcome"] == "failed")
    return {
        "schema_version": VERSION,
        "evidence_kind": results["evidence_kind"],
        "input_manifest_sha256": manifest_hash,
        "result_sha256": sha256(result_bytes).hexdigest(),
        "run": run,
        "samples": len(samples),
        "accepted_samples": len(accepted),
        "samples_by_category": dict(by_category),
        "attempts": len(attempts),
        "attempts_by_outcome": {status: attempts_by_outcome[status] for status in OUTCOMES},
        "failed_attempts_by_stage": dict(failures_by_stage),
        "latency_ms": {
            "p50": latency[(50 * len(latency) - 1) // 100],
            "p95": latency[(95 * len(latency) - 1) // 100],
        },
        "gpu_ms": sum(a["gpu_ms"] for a in attempts),
        "peak_vram_mib": max(a["peak_vram_mib"] for a in attempts),
        "artist_correction_seconds": sum(a["artist_correction_seconds"] for a in attempts),
        "rated_attempts": len(rated),
        "quality_score_sums": {field: sum(scores[field] for scores in rated) for field in SCORE_FIELDS},
        "cost_by_component_usd": {field: usd(value) for field, value in costs.items()},
        "cost_total_usd": usd(total_cost),
        "retry_cost_usd": usd(retry_cost),
        "cost_per_accepted_asset_usd": usd(average_cost) if average_cost is not None else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("results", type=Path)
    args = parser.parse_args(argv)
    try:
        summary = summarize(args.manifest.read_bytes(), args.results.read_bytes())
    except (OSError, ValueError) as exc:
        parser.exit(2, f"benchmark input error: {exc}\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
