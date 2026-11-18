"""Strict OBJ + PNG to self-contained textured GLB 2.0 packaging.

This utility exists for isolated model adapters such as the TripoSR candidate.
It intentionally accepts only the simple, single-mesh OBJ shape emitted by
xatlas-python's export helper: one position/UV (and optional normal) index per
vertex and triangular positive-index faces. It does not load MTL files or any
external resource referenced by the OBJ.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .glb_validation import MAX_GLB_BYTES, inspect_glb


MAX_OBJ_BYTES = 128 * 1024 * 1024
MAX_TEXTURE_BYTES = 64 * 1024 * 1024
MAX_VERTICES = 2_000_000
MAX_TRIANGLES = 4_000_000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963
FLOAT = 5126
UNSIGNED_INT = 5125
LINEAR = 9729
LINEAR_MIPMAP_LINEAR = 9987
REPEAT = 10497


class TexturedGLBError(ValueError):
    """The candidate mesh/texture cannot be safely packaged."""


@dataclass(frozen=True)
class SimpleOBJ:
    positions: tuple[tuple[float, float, float], ...]
    texcoords: tuple[tuple[float, float], ...]
    normals: tuple[tuple[float, float, float], ...] | None
    triangles: tuple[tuple[int, int, int], ...]


def _finite(values: Iterable[float], field: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in result):
        raise TexturedGLBError(f"{field} contains a non-finite number")
    return result


def _parse_positive_index(token: str, *, limit: int, field: str) -> int:
    if not token.isdigit():
        raise TexturedGLBError(f"{field} must use positive OBJ indices")
    value = int(token)
    if value < 1 or value > limit:
        raise TexturedGLBError(f"{field} is out of range")
    return value - 1


def parse_xatlas_obj_bytes(payload: bytes) -> SimpleOBJ:
    """Parse the narrow OBJ dialect emitted by xatlas-python export()."""
    if len(payload) > MAX_OBJ_BYTES:
        raise TexturedGLBError("OBJ exceeds candidate adapter byte limit")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TexturedGLBError("OBJ must be UTF-8 text") from exc

    positions: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    raw_faces: list[list[str]] = []

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        directive = parts[0]
        try:
            if directive == "v":
                if len(parts) != 4:
                    raise TexturedGLBError("vertex must have exactly 3 coordinates")
                positions.append(_finite(parts[1:], "vertex"))
                if len(positions) > MAX_VERTICES:
                    raise TexturedGLBError("OBJ exceeds vertex limit")
            elif directive == "vt":
                if len(parts) != 3:
                    raise TexturedGLBError("texture coordinate must have exactly 2 values")
                texcoords.append(_finite(parts[1:], "texture coordinate"))
                if len(texcoords) > MAX_VERTICES:
                    raise TexturedGLBError("OBJ exceeds texture-coordinate limit")
            elif directive == "vn":
                if len(parts) != 4:
                    raise TexturedGLBError("normal must have exactly 3 coordinates")
                normals.append(_finite(parts[1:], "normal"))
                if len(normals) > MAX_VERTICES:
                    raise TexturedGLBError("OBJ exceeds normal limit")
            elif directive == "f":
                if len(parts) != 4:
                    raise TexturedGLBError("only triangular OBJ faces are accepted")
                raw_faces.append(parts[1:])
                if len(raw_faces) > MAX_TRIANGLES:
                    raise TexturedGLBError("OBJ exceeds triangle limit")
            else:
                # In particular, reject mtllib/usemtl instead of following paths.
                raise TexturedGLBError(f"unsupported OBJ directive: {directive}")
        except (ValueError, TexturedGLBError) as exc:
            if isinstance(exc, TexturedGLBError):
                raise TexturedGLBError(f"OBJ line {line_number}: {exc}") from exc
            raise TexturedGLBError(f"OBJ line {line_number} contains invalid numeric data") from exc

    if len(positions) < 3 or not raw_faces:
        raise TexturedGLBError("OBJ must contain at least one triangle")
    if len(texcoords) != len(positions):
        raise TexturedGLBError("xatlas OBJ must have one UV per position")
    if normals and len(normals) != len(positions):
        raise TexturedGLBError("xatlas OBJ normals must align one-to-one with positions")

    triangles: list[tuple[int, int, int]] = []
    for face in raw_faces:
        parsed: list[int] = []
        for token in face:
            fields = token.split("/")
            if len(fields) not in {2, 3} or not fields[0] or not fields[1]:
                raise TexturedGLBError("textured faces must contain position/UV indices")
            position_index = _parse_positive_index(
                fields[0], limit=len(positions), field="position index"
            )
            uv_index = _parse_positive_index(
                fields[1], limit=len(texcoords), field="UV index"
            )
            # xatlas export duplicates vertices so all indices must be identical.
            if uv_index != position_index:
                raise TexturedGLBError("xatlas OBJ position and UV indices must match")
            if normals:
                if len(fields) != 3 or not fields[2]:
                    raise TexturedGLBError("all faces must include normals when normals exist")
                normal_index = _parse_positive_index(
                    fields[2], limit=len(normals), field="normal index"
                )
                if normal_index != position_index:
                    raise TexturedGLBError("xatlas OBJ normal index must match position index")
            elif len(fields) == 3 and fields[2]:
                raise TexturedGLBError("face references normals but no normal records exist")
            parsed.append(position_index)
        if len(set(parsed)) != 3:
            raise TexturedGLBError("degenerate triangle indices are not accepted")
        triangles.append(tuple(parsed))

    return SimpleOBJ(
        positions=tuple(positions),
        texcoords=tuple(texcoords),
        normals=tuple(normals) if normals else None,
        triangles=tuple(triangles),
    )


def load_xatlas_obj(path: str | Path) -> SimpleOBJ:
    path = Path(path)
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise TexturedGLBError("OBJ cannot be read") from exc
    if size > MAX_OBJ_BYTES:
        raise TexturedGLBError("OBJ exceeds candidate adapter byte limit")
    try:
        return parse_xatlas_obj_bytes(path.read_bytes())
    except OSError as exc:
        raise TexturedGLBError("OBJ cannot be read") from exc


def validate_png(payload: bytes) -> tuple[int, int]:
    if len(payload) > MAX_TEXTURE_BYTES:
        raise TexturedGLBError("PNG texture exceeds candidate adapter byte limit")
    if len(payload) < 33 or not payload.startswith(PNG_SIGNATURE):
        raise TexturedGLBError("texture must be a PNG")
    if payload[12:16] != b"IHDR":
        raise TexturedGLBError("PNG is missing its leading IHDR chunk")
    width, height = struct.unpack(">II", payload[16:24])
    if width < 1 or height < 1 or width > 16_384 or height > 16_384:
        raise TexturedGLBError("PNG dimensions are outside the accepted range")
    return width, height


def _pack_float_vectors(rows: Sequence[Sequence[float]], width: int) -> bytes:
    flattened: list[float] = []
    for row in rows:
        if len(row) != width:
            raise TexturedGLBError("mesh vector has unexpected width")
        flattened.extend(row)
    return struct.pack(f"<{len(flattened)}f", *flattened)


def _append_view(blob: bytearray, payload: bytes) -> tuple[int, int]:
    while len(blob) % 4:
        blob.append(0)
    offset = len(blob)
    blob.extend(payload)
    length = len(payload)
    while len(blob) % 4:
        blob.append(0)
    return offset, length


def build_textured_glb(
    mesh: SimpleOBJ,
    png: bytes,
    *,
    generator: str = "Build 3D AI candidate textured-GLB adapter",
    flip_v: bool = False,
) -> bytes:
    """Package one xatlas-style mesh and PNG as an embedded GLB 2.0."""
    validate_png(png)
    if not mesh.positions or not mesh.texcoords or not mesh.triangles:
        raise TexturedGLBError("mesh is incomplete")
    if len(mesh.positions) != len(mesh.texcoords):
        raise TexturedGLBError("mesh positions/UVs are not aligned")
    if mesh.normals is not None and len(mesh.normals) != len(mesh.positions):
        raise TexturedGLBError("mesh normals are not aligned")

    positions = tuple(_finite(row, "vertex") for row in mesh.positions)
    texcoords = tuple(_finite(row, "texture coordinate") for row in mesh.texcoords)
    if flip_v:
        texcoords = tuple((uv[0], 1.0 - uv[1]) for uv in texcoords)
    normals = (
        tuple(_finite(row, "normal") for row in mesh.normals)
        if mesh.normals is not None
        else None
    )

    vertex_count = len(positions)
    indices: list[int] = []
    for face in mesh.triangles:
        if len(face) != 3:
            raise TexturedGLBError("only triangles can be packaged")
        for index in face:
            if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= vertex_count:
                raise TexturedGLBError("triangle index is out of range")
            indices.append(index)

    binary = bytearray()
    views: list[dict] = []
    accessors: list[dict] = []

    def add_view(payload: bytes, *, target: int | None = None) -> int:
        offset, length = _append_view(binary, payload)
        item = {"buffer": 0, "byteOffset": offset, "byteLength": length}
        if target is not None:
            item["target"] = target
        views.append(item)
        return len(views) - 1

    pos_view = add_view(_pack_float_vectors(positions, 3), target=ARRAY_BUFFER)
    mins = [min(row[axis] for row in positions) for axis in range(3)]
    maxs = [max(row[axis] for row in positions) for axis in range(3)]
    accessors.append({
        "bufferView": pos_view,
        "componentType": FLOAT,
        "count": vertex_count,
        "type": "VEC3",
        "min": mins,
        "max": maxs,
    })
    position_accessor = len(accessors) - 1

    normal_accessor: int | None = None
    if normals is not None:
        normal_view = add_view(_pack_float_vectors(normals, 3), target=ARRAY_BUFFER)
        accessors.append({
            "bufferView": normal_view,
            "componentType": FLOAT,
            "count": vertex_count,
            "type": "VEC3",
        })
        normal_accessor = len(accessors) - 1

    uv_view = add_view(_pack_float_vectors(texcoords, 2), target=ARRAY_BUFFER)
    accessors.append({
        "bufferView": uv_view,
        "componentType": FLOAT,
        "count": vertex_count,
        "type": "VEC2",
    })
    uv_accessor = len(accessors) - 1

    index_payload = struct.pack(f"<{len(indices)}I", *indices)
    index_view = add_view(index_payload, target=ELEMENT_ARRAY_BUFFER)
    accessors.append({
        "bufferView": index_view,
        "componentType": UNSIGNED_INT,
        "count": len(indices),
        "type": "SCALAR",
        "min": [min(indices)],
        "max": [max(indices)],
    })
    index_accessor = len(accessors) - 1

    image_view = add_view(png)
    attributes = {
        "POSITION": position_accessor,
        "TEXCOORD_0": uv_accessor,
    }
    if normal_accessor is not None:
        attributes["NORMAL"] = normal_accessor

    document = {
        "asset": {"version": "2.0", "generator": generator},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Generated mesh"}],
        "meshes": [{
            "name": "Generated mesh",
            "primitives": [{
                "attributes": attributes,
                "indices": index_accessor,
                "material": 0,
                "mode": 4,
            }],
        }],
        "materials": [{
            "name": "Baked base color",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "baseColorTexture": {"index": 0, "texCoord": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
            "doubleSided": True,
        }],
        "samplers": [{
            "magFilter": LINEAR,
            "minFilter": LINEAR_MIPMAP_LINEAR,
            "wrapS": REPEAT,
            "wrapT": REPEAT,
        }],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": image_view, "mimeType": "image/png"}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
    }

    json_bytes = json.dumps(
        document, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    bin_bytes = bytes(binary)
    if len(bin_bytes) % 4:
        raise AssertionError("BIN chunk must be aligned")

    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    if total_length > MAX_GLB_BYTES:
        raise TexturedGLBError("packaged GLB exceeds product byte limit")

    output = bytearray(struct.pack("<4sII", b"glTF", 2, total_length))
    output.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    output.extend(json_bytes)
    output.extend(struct.pack("<I4s", len(bin_bytes), b"BIN\x00"))
    output.extend(bin_bytes)

    # Reuse the same structural policy enforced on product downloads.
    try:
        inspect_glb(io.BytesIO(output))
    except Exception as exc:
        raise TexturedGLBError("packaged GLB failed product structural validation") from exc
    return bytes(output)


def package_files(
    obj_path: str | Path,
    png_path: str | Path,
    output_path: str | Path,
    *,
    flip_v: bool = False,
) -> dict:
    mesh = load_xatlas_obj(obj_path)
    png_path = Path(png_path)
    try:
        if png_path.stat().st_size > MAX_TEXTURE_BYTES:
            raise TexturedGLBError("PNG texture exceeds candidate adapter byte limit")
        png = png_path.read_bytes()
    except OSError as exc:
        raise TexturedGLBError("PNG texture cannot be read") from exc

    payload = build_textured_glb(mesh, png, flip_v=flip_v)
    report = inspect_glb(io.BytesIO(payload))

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, suffix=".glb.part", delete=False
        ) as handle:
            staged = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, destination)
        staged = None
    finally:
        if staged is not None:
            Path(staged).unlink(missing_ok=True)

    return {
        "path": str(destination),
        "size_bytes": report.size_bytes,
        "sha256": report.sha256,
        "mesh_count": report.mesh_count,
        "primitive_count": report.primitive_count,
        "material_count": report.material_count,
        "node_count": report.node_count,
        "vertex_count": len(mesh.positions),
        "triangle_count": len(mesh.triangles),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Package xatlas-python's strict single-mesh OBJ plus baked PNG "
            "into a self-contained textured GLB 2.0."
        )
    )
    parser.add_argument("obj", help="xatlas-exported OBJ")
    parser.add_argument("texture", help="baked PNG base-color texture")
    parser.add_argument("output", help="destination .glb path")
    parser.add_argument(
        "--flip-v",
        action="store_true",
        help=(
            "replace each V coordinate with 1-V. Keep disabled by default; "
            "enable only if a visual orientation check proves it is required."
        ),
    )
    args = parser.parse_args(argv)
    try:
        report = package_files(args.obj, args.texture, args.output, flip_v=args.flip_v)
    except TexturedGLBError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
