import base64
import io
import json
import struct

import pytest

from build3d_gateway.glb_validation import inspect_glb
from build3d_gateway.textured_glb import (
    SimpleOBJ,
    TexturedGLBError,
    build_textured_glb,
    package_files,
    parse_xatlas_obj_bytes,
)


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZQmcAAAAASUVORK5CYII="
)

XATLAS_OBJ = b"""\
v 0 0 0
v 1 0 0
v 0 1 0
vn 0 0 1
vn 0 0 1
vn 0 0 1
vt 0 0
vt 1 0
vt 0 1
f 1/1/1 2/2/2 3/3/3
"""


def glb_document(payload: bytes) -> dict:
    magic, version, declared = struct.unpack("<4sII", payload[:12])
    assert magic == b"glTF"
    assert version == 2
    assert declared == len(payload)
    json_length, kind = struct.unpack("<I4s", payload[12:20])
    assert kind == b"JSON"
    return json.loads(payload[20 : 20 + json_length].decode("utf-8"))


def test_xatlas_obj_and_png_package_as_self_contained_textured_glb():
    mesh = parse_xatlas_obj_bytes(XATLAS_OBJ)
    payload = build_textured_glb(mesh, PNG_1X1)
    report = inspect_glb(io.BytesIO(payload))
    document = glb_document(payload)

    assert report.mesh_count == 1
    assert report.primitive_count == 1
    assert report.material_count == 1
    assert report.node_count == 1
    assert document["images"] == [{"bufferView": 4, "mimeType": "image/png"}]
    assert document["textures"][0]["source"] == 0
    assert document["meshes"][0]["primitives"][0]["material"] == 0
    assert document["meshes"][0]["primitives"][0]["attributes"] == {
        "POSITION": 0,
        "TEXCOORD_0": 2,
        "NORMAL": 1,
    }
    assert document["buffers"][0].get("uri") is None
    assert PNG_1X1 in payload


def test_packager_supports_mesh_without_normals():
    mesh = SimpleOBJ(
        positions=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        texcoords=((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)),
        normals=None,
        triangles=((0, 1, 2),),
    )
    document = glb_document(build_textured_glb(mesh, PNG_1X1))
    assert document["meshes"][0]["primitives"][0]["attributes"] == {
        "POSITION": 0,
        "TEXCOORD_0": 1,
    }


def test_xatlas_obj_rejects_external_material_directives_and_index_aliases():
    with pytest.raises(TexturedGLBError, match="unsupported OBJ directive"):
        parse_xatlas_obj_bytes(b"mtllib outside.mtl\n" + XATLAS_OBJ)

    mismatched = XATLAS_OBJ.replace(b"1/1/1", b"1/2/1")
    with pytest.raises(TexturedGLBError, match="position and UV indices must match"):
        parse_xatlas_obj_bytes(mismatched)


@pytest.mark.parametrize(
    "face",
    [
        b"f 1/1/1 2/2/2 3/3/3 1/1/1\n",
        b"f -1/-1/-1 2/2/2 3/3/3\n",
        b"f 1//1 2//2 3//3\n",
    ],
)
def test_xatlas_obj_rejects_non_candidate_face_shapes(face):
    prefix = XATLAS_OBJ.rsplit(b"f ", 1)[0]
    with pytest.raises(TexturedGLBError):
        parse_xatlas_obj_bytes(prefix + face)


def test_package_files_writes_atomically_and_reports_product_integrity(tmp_path):
    obj = tmp_path / "mesh.obj"
    texture = tmp_path / "texture.png"
    output = tmp_path / "nested" / "mesh.glb"
    obj.write_bytes(XATLAS_OBJ)
    texture.write_bytes(PNG_1X1)

    report = package_files(obj, texture, output)

    assert output.is_file()
    assert report["path"] == str(output)
    assert report["vertex_count"] == 3
    assert report["triangle_count"] == 1
    with output.open("rb") as handle:
        inspected = inspect_glb(handle)
    assert report["sha256"] == inspected.sha256
    assert report["size_bytes"] == inspected.size_bytes


def test_flip_v_is_explicit_not_implicit():
    mesh = parse_xatlas_obj_bytes(XATLAS_OBJ)
    unchanged = build_textured_glb(mesh, PNG_1X1, flip_v=False)
    flipped = build_textured_glb(mesh, PNG_1X1, flip_v=True)
    assert unchanged != flipped
    assert inspect_glb(io.BytesIO(flipped)).mesh_count == 1
