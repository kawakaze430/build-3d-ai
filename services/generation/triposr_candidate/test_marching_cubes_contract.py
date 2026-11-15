"""CPU-only contract checks for the scikit-image marching-cubes replacement."""
from __future__ import annotations

import numpy as np
from skimage import measure


def adapted_marching_cubes(volume: np.ndarray, resolution: int):
    vertices, faces, _, _ = measure.marching_cubes(volume, level=0.0)
    faces = np.ascontiguousarray(faces[:, [1, 0, 2]])
    return np.ascontiguousarray(vertices) / (resolution - 1.0), faces


def test_axis_order_and_normalization_are_stable():
    resolution = 12
    x = np.linspace(-1.0, 1.0, resolution, dtype=np.float32)
    volume = np.broadcast_to(x[:, None, None], (resolution, resolution, resolution)).copy()
    vertices, faces = adapted_marching_cubes(volume, resolution)

    # The x=0 isosurface should remain the first array axis; this detects the
    # accidental [2,1,0] swap that was specific to torchmcubes output order.
    assert np.allclose(vertices[:, 0], 0.5, atol=1 / (resolution - 1))
    assert vertices[:, 1].ptp() > 0.9
    assert vertices[:, 2].ptp() > 0.9
    assert faces.ndim == 2 and faces.shape[1] == 3


def test_face_winding_is_explicitly_reversed_from_scikit_output():
    resolution = 10
    coords = np.linspace(-1.0, 1.0, resolution, dtype=np.float32)
    xx, yy, zz = np.meshgrid(coords, coords, coords, indexing="ij")
    volume = xx * xx + yy * yy + zz * zz - 0.5
    raw_vertices, raw_faces, _, _ = measure.marching_cubes(volume, level=0.0)
    vertices, faces = adapted_marching_cubes(volume, resolution)

    assert np.array_equal(faces[:, 0], raw_faces[:, 1])
    assert np.array_equal(faces[:, 1], raw_faces[:, 0])
    assert np.array_equal(faces[:, 2], raw_faces[:, 2])
    assert vertices.shape == raw_vertices.shape
