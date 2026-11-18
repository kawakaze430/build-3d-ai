"""Small, structurally valid in-memory glTF 2.0 triangle fixture.

No inference or pretrained weights are used by these unit tests.
"""
import json
import struct

import pytest


def build_triangle_glb(*, asset_version="2.0", images=None, mesh=True, include_bin=True):
    positions = struct.pack("<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    doc = {
        "asset": {"version": asset_version},
        "buffers": [{"byteLength": len(positions)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(positions)}],
        "accessors": [{
            "bufferView": 0, "componentType": 5126, "count": 3,
            "type": "VEC3", "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0],
        }],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    if mesh:
        doc["meshes"] = [{"primitives": [{"attributes": {"POSITION": 0}}]}]
    if images is not None:
        doc["images"] = images
    encoded = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    parts = [struct.pack("<I4s", len(encoded), b"JSON"), encoded]
    if include_bin:
        parts += [struct.pack("<I4s", len(positions), b"BIN\x00"), positions]
    payload = b"".join(parts)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(payload)) + payload


@pytest.fixture
def glb_bytes():
    return build_triangle_glb()


@pytest.fixture
def glb_factory():
    return build_triangle_glb
