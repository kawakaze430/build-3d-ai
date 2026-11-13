"""Artifact integrity tests. These only use synthetic triangle GLBs, not AI inference."""
from __future__ import annotations

import hashlib
import io
import struct

import pytest

from build3d_gateway.glb_validation import GLBValidationError, inspect_glb


def check(data: bytes):
    return inspect_glb(io.BytesIO(data))


def test_valid_triangle_has_real_mesh_structure(glb_bytes):
    report = check(glb_bytes)
    assert report.size_bytes == len(glb_bytes)
    assert report.mesh_count == 1
    assert report.primitive_count == 1
    assert report.node_count == 1
    assert report.sha256 == hashlib.sha256(glb_bytes).hexdigest()


@pytest.mark.parametrize("data", [b"", b"glTF", b"not a binary", b"glTF" + b"\x00" * 28])
def test_truncated_or_invalid_header_is_rejected(data):
    with pytest.raises(GLBValidationError):
        check(data)


def test_declared_size_must_match_bytes(glb_bytes):
    invalid = bytearray(glb_bytes)
    struct.pack_into("<I", invalid, 8, len(invalid) + 4)
    with pytest.raises(GLBValidationError, match="length"):
        check(bytes(invalid))


def test_only_binary_version_two_is_accepted(glb_bytes):
    invalid = bytearray(glb_bytes)
    struct.pack_into("<I", invalid, 4, 1)
    with pytest.raises(GLBValidationError, match="GLB 2.0"):
        check(bytes(invalid))


def test_json_chunk_cannot_overrun_file(glb_bytes):
    invalid = bytearray(glb_bytes)
    struct.pack_into("<I", invalid, 12, 100000000)
    with pytest.raises(GLBValidationError, match="JSON chunk"):
        check(bytes(invalid))


def test_no_mesh_is_not_a_valid_generated_asset(glb_factory):
    with pytest.raises(GLBValidationError, match="mesh"):
        check(glb_factory(mesh=False))


def test_missing_bin_chunk_is_rejected(glb_factory):
    with pytest.raises(GLBValidationError, match="buffer data"):
        check(glb_factory(include_bin=False))


def test_invalid_gltf_asset_version_is_rejected(glb_factory):
    with pytest.raises(GLBValidationError, match="version"):
        check(glb_factory(asset_version="1.0"))


def test_rejects_external_image_resources(glb_factory):
    data = glb_factory(images=[{"uri": "https://example.com/asset.png"}])
    with pytest.raises(GLBValidationError, match="external"):
        check(data)


def test_rejects_relative_image_file_references(glb_factory):
    with pytest.raises(GLBValidationError, match="external"):
        check(glb_factory(images=[{"uri": "textures/diffuse.png"}]))


def test_byte_cap_is_enforced(glb_bytes):
    with pytest.raises(GLBValidationError, match="limit"):
        inspect_glb(io.BytesIO(glb_bytes), max_bytes=len(glb_bytes) - 1)


def test_duplicate_chunk_rejected(glb_bytes):
    # Add a second JSON chunk and fix the header size.
    extra = struct.pack("<I4s", 4, b"JSON") + b"    "
    tampered = bytearray(glb_bytes + extra)
    struct.pack_into("<I", tampered, 8, len(tampered))
    with pytest.raises(GLBValidationError, match="Duplicate"):
        check(bytes(tampered))
