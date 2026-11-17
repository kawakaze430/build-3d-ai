from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from summarize import summarize

MANIFEST = {
    "schema_version": 1,
    "evidence_kind": "fixture",
    "samples": [
        {
            "id": f"fixture-{index}",
            "input_sha256": str(index) * 64,
            "category": "prop" if index < 3 else "character",
            "license_approved": True,
            "rights_reference": "synthetic unit fixture",
            "held_out": True,
        }
        for index in range(1, 4)
    ],
}
RUN = {
    "id": "fixture-run",
    "source_revision": "fixture-source",
    "model_revision": "fixture-model",
    "hardware": "CPU unit fixture",
    "checkpoint_sha256": "d" * 64,
    "runtime_sha256": "e" * 64,
    "started_at": "2026-11-18T00:00:00+00:00",
    "parameters": {"resolution": 256},
}
ATTEMPT = {
    "attempt_index": 1,
    "seed": 123,
    "latency_ms": 20,
    "gpu_ms": 10,
    "peak_vram_mib": 32,
    "artist_correction_seconds": 0,
    "cost_microusd": {"compute": 30, "storage": 20, "other": 0},
}
RATED = {
    "output_sha256": "a" * 64,
    "view_sha256": {"front": "7" * 64, "side": "8" * 64, "back": "9" * 64},
    "quality_scores": {"geometry": 5, "materials": 3, "hidden_view_consistency": 4, "usability": 4},
    "rating_notes": "Synthetic scoring fixture",
    "structural_glb_passed": True,
    "blender_import_passed": True,
}
ATTEMPTS = [
    dict(ATTEMPT, sample_id="fixture-1", outcome="failed", failure_stage="worker", reason="timeout"),
    dict(ATTEMPT, **RATED, sample_id="fixture-1", outcome="accepted"),
    dict(ATTEMPT, **RATED, sample_id="fixture-2", outcome="rejected", reason="visible seam"),
    dict(ATTEMPT, sample_id="fixture-3", outcome="failed", failure_stage="output", reason="missing"),
]
ATTEMPTS[1]["attempt_index"] = 2
ATTEMPTS[1]["latency_ms"] = 30


def records(manifest, attempts, **overrides):
    manifest_bytes = json.dumps(manifest).encode()
    results = {
        "schema_version": 1,
        "evidence_kind": "fixture",
        "input_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "run": RUN,
        "attempts": attempts,
        **overrides,
    }
    return manifest_bytes, json.dumps(results).encode()


def test_all_attempts_contribute_to_cost_latency_and_denominator():
    manifest, results = records(MANIFEST, ATTEMPTS)
    summary = summarize(manifest, results)
    assert summary["samples"] == 3
    assert summary["accepted_samples"] == 1
    assert summary["samples_by_category"] == {
        "prop": {"samples": 2, "accepted": 1},
        "character": {"samples": 1, "accepted": 0},
    }
    assert summary["attempts_by_outcome"] == {"accepted": 1, "rejected": 1, "failed": 2}
    assert summary["failed_attempts_by_stage"] == {"worker": 1, "output": 1}
    assert summary["latency_ms"] == {"p50": 20, "p95": 30}
    assert summary["cost_total_usd"] == "0.000200"
    assert summary["cost_per_accepted_asset_usd"] == "0.000200"
    assert summary["retry_cost_usd"] == "0.000050"
    assert summary["cost_by_component_usd"] == {"compute": "0.000120", "storage": "0.000080", "other": "0.000000"}
    assert summary["rated_attempts"] == 2
    assert summary["quality_score_sums"]["geometry"] == 10
    assert summary["gpu_ms"] == 40
    assert summary["peak_vram_mib"] == 32
    assert summary["input_manifest_sha256"] == sha256(manifest).hexdigest()
    assert summary["result_sha256"] == sha256(results).hexdigest()


def test_attempt_order_does_not_change_metrics_and_zero_accepted_cost_is_undefined():
    attempts = [ATTEMPTS[0], ATTEMPTS[2], ATTEMPTS[3]]
    original = summarize(*records(MANIFEST, attempts))
    reordered = summarize(*records(MANIFEST, list(reversed(attempts))))
    assert original.pop("result_sha256") != reordered.pop("result_sha256")
    assert original == reordered
    assert original["cost_per_accepted_asset_usd"] is None
    assert original["cost_total_usd"] == "0.000150"


def test_cost_uses_fixed_precision_even_with_fractional_average():
    attempts = [deepcopy(attempt) for attempt in ATTEMPTS]
    attempts[2]["outcome"] = "accepted"
    attempts[2]["cost_microusd"]["other"] = 1
    summary = summarize(*records(MANIFEST, attempts))
    assert summary["cost_total_usd"] == "0.000201"
    assert summary["cost_per_accepted_asset_usd"] == "0.000101"


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda samples: samples.pop(), "missing from manifest"),
        (lambda samples: samples.append(dict(samples[0])), "duplicate manifest sample"),
        (lambda samples: samples.append(dict(samples[0], id="alias")), "duplicate manifest sample"),
        (lambda samples: samples[0].update(license_approved=False), "approved input rights"),
        (lambda samples: samples[0].update(held_out=1), "held-out status"),
        (lambda samples: samples[0].update(rights_reference="  "), "rights_reference"),
    ],
)
def test_rejects_incomplete_duplicate_or_unapproved_manifest(change, match):
    manifest = deepcopy(MANIFEST)
    change(manifest["samples"])
    with pytest.raises(ValueError, match=match):
        summarize(*records(manifest, ATTEMPTS))


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda attempts: attempts.pop(), "missing attempts for: fixture-3"),
        (lambda attempts: attempts.append(dict(attempts[0])), "duplicate attempt"),
        (lambda attempts: attempts[1].update(attempt_index=3), "consecutive starting at 1"),
        (lambda attempts: attempts[1].update(attempt_index=True), "attempt_index must be an integer"),
        (lambda attempts: attempts.append(dict(attempts[1], attempt_index=3)), "after acceptance"),
        (lambda attempts: attempts[0].pop("failure_stage"), "failure_stage"),
        (lambda attempts: attempts[1]["view_sha256"].pop("back"), "back"),
        (lambda attempts: attempts[1].update(blender_import_passed=False), "blender_import_passed"),
        (lambda attempts: attempts[1]["quality_scores"].update(geometry=6), "range 1–5"),
        (lambda attempts: attempts[1]["cost_microusd"].update(other=-1), "other must be an integer"),
    ],
)
def test_rejects_incomplete_or_inconsistent_attempts(change, match):
    attempts = [deepcopy(attempt) for attempt in ATTEMPTS]
    change(attempts)
    with pytest.raises(ValueError, match=match):
        summarize(*records(MANIFEST, attempts))


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"schema_version": 2}, "unsupported schema_version"),
        ({"evidence_kind": "measured"}, "evidence kinds differ"),
        ({"input_manifest_sha256": "0" * 64}, "does not match the manifest bytes"),
        ({"run": dict(RUN, started_at="2026-11-18T00:00:00")}, "requires a timezone"),
        ({"run": dict(RUN, parameters={"bound": float("inf")})}, "invalid JSON number"),
    ],
)
def test_rejects_incomparable_results(overrides, match):
    with pytest.raises(ValueError, match=match):
        summarize(*records(MANIFEST, ATTEMPTS, **overrides))


def test_rejects_duplicate_keys_and_overflowing_numbers():
    manifest, results = records(MANIFEST, ATTEMPTS)
    duplicate = results.replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1')
    with pytest.raises(ValueError, match="duplicate JSON field"):
        summarize(manifest, duplicate)
    overflow = results.replace(b'"resolution": 256', b'"resolution": 1e1000')
    with pytest.raises(ValueError, match="invalid JSON number"):
        summarize(manifest, overflow)


def test_cli_is_repeatable_and_failed_validation_emits_no_report(tmp_path):
    manifest, results = records(MANIFEST, ATTEMPTS)
    manifest_file = tmp_path / "manifest.json"
    results_file = tmp_path / "results.json"
    manifest_file.write_bytes(manifest)
    results_file.write_bytes(results)
    command = [sys.executable, str(Path(__file__).with_name("summarize.py")), str(manifest_file), str(results_file)]
    first = subprocess.run(command, capture_output=True, text=True, check=True)
    assert first.stdout == subprocess.check_output(command, text=True)
    assert json.loads(first.stdout)["evidence_kind"] == "fixture"
    assert first.stderr == ""
    assert manifest_file.read_bytes() == manifest
    assert results_file.read_bytes() == results

    results_file.write_bytes(b"{}")
    failed = subprocess.run(command, capture_output=True, text=True)
    assert failed.returncode == 2
    assert failed.stdout == ""
    assert "schema_version" in failed.stderr
