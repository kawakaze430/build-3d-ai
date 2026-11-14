"""Structural validation of self-contained GLB 2.0 outputs.

This is an integrity/portability preflight, NOT a geometry topology analysis or
a renderer security guarantee. Blender/3D-engine import validation is still
required for production acceptance.
"""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from typing import BinaryIO


MAX_GLB_BYTES = 250 * 1024 * 1024
MAX_JSON_BYTES = 32 * 1024 * 1024
GLB_MAGIC = b"glTF"
JSON_CHUNK = b"JSON"
BIN_CHUNK = b"BIN\x00"


class GLBValidationError(ValueError):
    """A result is not a structurally acceptable, self-contained GLB."""


@dataclass(frozen=True)
class GLBInspection:
    size_bytes: int
    sha256: str
    mesh_count: int
    primitive_count: int
    material_count: int
    node_count: int


def _array(payload: dict, key: str) -> list:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise GLBValidationError(f"GLB {key} must be an array")
    return value


def inspect_glb(handle: BinaryIO, *, max_bytes: int = MAX_GLB_BYTES) -> GLBInspection:
    """Inspect a seekable binary stream without loading the BIN chunk into memory.

    Checks GLB header, JSON chunk, aligned chunk boundaries, embedded buffers,
    minimum mesh structure, and references to external assets. The output is
    unsuitable for use if any of these checks fail.
    """
    handle.seek(0, 2)
    actual_size = handle.tell()
    handle.seek(0)

    if actual_size > max_bytes:
        raise GLBValidationError("GLB exceeds configured byte limit")
    if actual_size < 20:
        raise GLBValidationError("GLB header is incomplete")

    magic, version, declared_size = struct.unpack("<4sII", handle.read(12))
    if magic != GLB_MAGIC or version != 2:
        raise GLBValidationError("Not a GLB 2.0 binary")
    if declared_size != actual_size or actual_size % 4:
        raise GLBValidationError("GLB declared length does not match its bytes")

    json_len, json_type = struct.unpack("<I4s", handle.read(8))
    if json_type != JSON_CHUNK:
        raise GLBValidationError("First GLB chunk must be JSON")
    if json_len == 0 or json_len > MAX_JSON_BYTES or json_len % 4:
        raise GLBValidationError("JSON chunk has invalid length")
    if json_len > actual_size - 20:
        raise GLBValidationError("JSON chunk overruns the GLB")

    try:
        document = json.loads(handle.read(json_len).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GLBValidationError("GLB JSON chunk is invalid") from exc

    if not isinstance(document, dict):
        raise GLBValidationError("GLB JSON root must be an object")
    asset = document.get("asset")
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        raise GLBValidationError("GLB must declare glTF asset version 2.0")

    meshes = _array(document, "meshes")
    if not meshes:
        raise GLBValidationError("GLB does not contain a mesh")

    primitive_count = 0
    for mesh in meshes:
        if not isinstance(mesh, dict):
            raise GLBValidationError("GLB mesh is not an object")
        primitives = mesh.get("primitives")
        if not isinstance(primitives, list) or not primitives:
            raise GLBValidationError("GLB mesh has no primitives")
        if not all(isinstance(item, dict) for item in primitives):
            raise GLBValidationError("GLB primitive is not an object")
        primitive_count += len(primitives)

    materials = _array(document, "materials")
    nodes = _array(document, "nodes")
    buffers = _array(document, "buffers")
    images = _array(document, "images")

    # An exported .glb must not depend on unknown paths or network resources.
    for item in buffers + images:
        if not isinstance(item, dict):
            raise GLBValidationError("GLB buffer/image reference is malformed")
        uri = item.get("uri")
        if uri is not None and (not isinstance(uri, str) or not uri.startswith("data:")):
            raise GLBValidationError("GLB references external buffers or images")

    bin_length: int | None = None
    while handle.tell() < actual_size:
        remaining = actual_size - handle.tell()
        if remaining < 8:
            raise GLBValidationError("Truncated GLB chunk header")
        chunk_len, chunk_type = struct.unpack("<I4s", handle.read(8))
        if chunk_len % 4 or chunk_len > actual_size - handle.tell():
            raise GLBValidationError("Invalid GLB chunk boundary")
        if chunk_type == JSON_CHUNK:
            raise GLBValidationError("Duplicate GLB JSON chunk")
        if chunk_type == BIN_CHUNK:
            if bin_length is not None:
                raise GLBValidationError("Duplicate GLB BIN chunk")
            bin_length = chunk_len
        handle.seek(chunk_len, 1)

    for buffer in buffers:
        size = buffer.get("byteLength")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise GLBValidationError("GLB buffer declares invalid size")
        if buffer.get("uri") is None and (bin_length is None or size > bin_length):
            raise GLBValidationError("GLB buffer data is missing or too short")

    digest = hashlib.sha256()
    handle.seek(0)
    while chunk := handle.read(1024 * 1024):
        digest.update(chunk)
    handle.seek(0)

    return GLBInspection(
        size_bytes=actual_size,
        sha256=digest.hexdigest(),
        mesh_count=len(meshes),
        primitive_count=primitive_count,
        material_count=len(materials),
        node_count=len(nodes),
    )
