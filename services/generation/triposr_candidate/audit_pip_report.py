#!/usr/bin/env python3
"""Fail-closed CPU audit of a pip dry-run resolution for TripoSR qualification.

This is an *index metadata* inventory, not a hash-verified wheelhouse or an
approval to use the model. No package is installed or downloaded by this tool.
The input is generated separately with ``pip install --dry-run --ignore-installed
--report ... -r requirements-build3d.txt`` for one recorded Python platform.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_PACKAGES = 256
TRUSTED_INDEX_HOSTS = frozenset({"files.pythonhosted.org", "pypi.org"})
PIN_PATTERN = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.+!-]*)")
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
VERSION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+!-]*")
SHA256_PATTERN = re.compile(r"[a-fA-F0-9]{64}")


class AuditError(ValueError):
    """A resolution report did not meet the qualification inventory contract."""


def normalize_name(name: str) -> str:
    if not NAME_PATTERN.fullmatch(name):
        raise AuditError(f"invalid distribution name: {name!r}")
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pins(contents: str) -> dict[str, str]:
    """Accept only direct, exact PEP-440-like == pins; no pip options or URLs."""
    pins: dict[str, str] = {}
    for line_no, raw in enumerate(contents.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_PATTERN.fullmatch(line)
        if not match:
            raise AuditError(f"requirements line {line_no} is not an exact direct pin")
        name = normalize_name(match.group(1))
        if name in pins:
            raise AuditError(f"duplicate direct requirement: {name}")
        pins[name] = match.group(2)
    if not pins:
        raise AuditError("direct requirements are empty")
    return pins


def _trusted_archive_url(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in TRUSTED_INDEX_HOSTS
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
        or parts.query
        or parts.fragment
    ):
        raise AuditError("resolution contains an untrusted, credentialed or mutable artifact URL")
    filename = parts.path.rsplit("/", 1)[-1]
    if filename.endswith(".whl") and filename[:-4]:
        return filename, "wheel"
    if filename.endswith((".tar.gz", ".zip")) and filename.rsplit(".", 1)[0]:
        return filename, "source_archive"
    raise AuditError("resolution contains an unsupported artifact type")


def inspect_report(
    report: dict,
    pins: dict[str, str],
    report_bytes: bytes,
    pins_bytes: bytes,
    *,
    require_wheels: bool = False,
) -> dict:
    if not isinstance(report, dict) or str(report.get("version")) != "1":
        raise AuditError("unsupported pip JSON report format")
    entries = report.get("install")
    if not isinstance(entries, list) or not 0 < len(entries) <= MAX_PACKAGES:
        raise AuditError("empty or unbounded resolved dependency list")

    resolved: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("is_yanked", False):
            raise AuditError("malformed or yanked package in resolution")
        metadata = entry.get("metadata")
        download = entry.get("download_info")
        if not isinstance(metadata, dict) or not isinstance(download, dict):
            raise AuditError("resolution entry has no package metadata or provenance")
        raw_name = metadata.get("name")
        version = metadata.get("version")
        if not isinstance(raw_name, str) or not isinstance(version, str):
            raise AuditError("resolution entry has invalid name/version")
        name = normalize_name(raw_name)
        if not VERSION_PATTERN.fullmatch(version):
            raise AuditError(f"invalid version for {name}")
        if name in resolved:
            raise AuditError(f"duplicate normalized resolved package: {name}")

        url = download.get("url")
        if not isinstance(url, str):
            raise AuditError(f"missing artifact URL for {name}")
        artifact, artifact_type = _trusted_archive_url(url)
        if require_wheels and artifact_type != "wheel":
            raise AuditError(f"wheel-only release gate blocked by source archive: {name}")
        archive = download.get("archive_info")
        hashes = archive.get("hashes") if isinstance(archive, dict) else None
        digest = hashes.get("sha256") if isinstance(hashes, dict) else None
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
            raise AuditError(f"missing SHA256 archive provenance for {name}")

        resolved[name] = {
            "name": name,
            "version": version,
            "artifact_filename": artifact,
            "artifact_type": artifact_type,
            "index_url": url,
            "index_reported_sha256": digest.lower(),
            "direct_requirement": name in pins,
        }

    for name, expected_version in pins.items():
        found = resolved.get(name)
        if not found or found["version"] != expected_version:
            raise AuditError(f"missing or mismatched direct pin: {name}=={expected_version}")

    environment = report.get("environment")
    if not isinstance(environment, dict):
        raise AuditError("pip resolution report lacks platform environment")
    platform = {}
    for key in ("python_version", "sys_platform", "platform_machine", "platform_system"):
        value = environment.get(key)
        if not isinstance(value, str) or not value or len(value) > 120:
            raise AuditError(f"resolution report lacks environment field: {key}")
        platform[key] = value

    source_archives = sorted(
        row["name"] for row in resolved.values() if row["artifact_type"] == "source_archive"
    )
    return {
        "schema_version": 1,
        "status": (
            "BLOCKED_BY_SOURCE_ARCHIVES_NOT_PRODUCTION_APPROVED"
            if source_archives
            else "INDEX_METADATA_ONLY_NOT_A_WHEELHOUSE_OR_PRODUCTION_APPROVAL"
        ),
        "pip_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "direct_requirements_sha256": hashlib.sha256(pins_bytes).hexdigest(),
        "environment": platform,
        "direct_requirement_count": len(pins),
        "resolved_artifact_count": len(resolved),
        "resolved_wheel_count": len(resolved) - len(source_archives),
        "source_archive_count": len(source_archives),
        "source_archives_needing_reviewed_build": source_archives,
        "packages": sorted(resolved.values(), key=lambda row: row["name"]),
        "unverified": [
            "index-reported hashes have not been independently verified against downloaded wheel bytes",
            "source archives require a separately reviewed, reproducible wheel build before release",
            "preinstalled PyTorch CUDA/base-image OS and bundled libraries are not enumerated",
            "actual container build, checkpoint loading and headless texture bake were not run",
            "model weights, training data, SaaS geography and transitive licenses are not cleared",
        ],
    }


def read_limited(path: Path) -> bytes:
    if path.stat().st_size > MAX_REPORT_BYTES:
        raise AuditError("input exceeds maximum offline audit size")
    value = path.read_bytes()
    if len(value) > MAX_REPORT_BYTES:
        raise AuditError("input exceeds maximum offline audit size")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--require-wheels", action="store_true",
        help="Fail the release preflight if any resolved artifact is an sdist/source archive",
    )
    args = parser.parse_args(argv)
    try:
        report_bytes = read_limited(args.report)
        pins_bytes = read_limited(args.requirements)
        report = json.loads(report_bytes)
        pins = parse_pins(pins_bytes.decode("utf-8"))
        inventory = inspect_report(
            report, pins, report_bytes, pins_bytes, require_wheels=args.require_wheels
        )
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(inventory, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except (AuditError, OSError, UnicodeError, ValueError) as exc:
        print(f"TripoSR dependency inventory rejected: {exc}", file=sys.stderr)
        return 2
    print(
        f"Recorded {inventory['resolved_artifact_count']} index-reported digests; "
        f"{inventory['source_archive_count']} source archives require reviewed builds. "
        f"Status: {inventory['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
