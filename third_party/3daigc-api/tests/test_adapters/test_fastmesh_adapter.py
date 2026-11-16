"""
Unit tests for FastMesh retopology adapter.
"""

import os
import pytest
import tempfile
from pathlib import Path

from adapters.fastmesh_adapter import FastMeshRetopologyAdapter


@pytest.fixture
def fastmesh_adapter():
    """Create a FastMesh adapter instance for testing."""
    # Use V1K variant for faster testing
    adapter = FastMeshRetopologyAdapter(
        model_id="test_fastmesh_v1k",
        variant="V1K",
        vram_requirement=4096,
    )
    return adapter


@pytest.fixture
def sample_mesh_path():
    """Provide a sample mesh file path for testing."""
    # Use a sample mesh from the assets folder
    mesh_path = "assets/example_retopo/001.obj"
    if os.path.exists(mesh_path):
        return mesh_path
    pytest.skip("Sample mesh file not found")


class TestFastMeshAdapter:
    """Test suite for FastMesh retopology adapter."""

    def test_adapter_initialization(self, fastmesh_adapter):
        """Test that the adapter initializes correctly."""
        assert fastmesh_adapter.model_id == "test_fastmesh_v1k"
        assert fastmesh_adapter.variant == "V1K"
        assert fastmesh_adapter.feature_type == "mesh_retopology"
        assert fastmesh_adapter.target_vertex_count == 1000

    def test_supported_formats(self, fastmesh_adapter):
        """Test that the adapter reports correct supported formats."""
        formats = fastmesh_adapter.get_supported_formats()
        assert "input" in formats
        assert "output" in formats
        assert "obj" in formats["input"]
        assert "glb" in formats["input"]
        assert "obj" in formats["output"]

    @pytest.mark.skipif(
        not os.path.exists("pretrained/FastMesh-V1K"),
        reason="FastMesh V1K model not available",
    )
    def test_model_loading(self, fastmesh_adapter):
        """Test that the model can be loaded."""
        try:
            fastmesh_adapter.load(gpu_id=0)
            assert fastmesh_adapter.status.value == "loaded"
            assert fastmesh_adapter.model is not None
        finally:
            fastmesh_adapter.unload()

    @pytest.mark.skipif(
        not os.path.exists("pretrained/FastMesh-V1K"),
        reason="FastMesh V1K model not available",
    )
    def test_retopology_process(self, fastmesh_adapter, sample_mesh_path):
        """Test the retopology process with a sample mesh."""
        try:
            # Load model
            fastmesh_adapter.load(gpu_id=0)

            # Process mesh
            inputs = {
                "mesh_path": sample_mesh_path,
                "output_format": "obj",
                "seed": 42,
            }

            result = fastmesh_adapter.process(inputs)

            # Validate result
            assert result is not None
            assert "output_mesh_path" in result
            assert "original_stats" in result
            assert "output_stats" in result
            assert "success" in result
            assert result["success"] is True

            # Check that output file exists
            output_path = Path(result["output_mesh_path"])
            assert output_path.exists()

            # Check stats
            assert result["output_stats"]["vertex_count"] > 0
            assert result["output_stats"]["face_count"] > 0

        finally:
            fastmesh_adapter.unload()

    def test_invalid_mesh_path(self, fastmesh_adapter):
        """Test handling of invalid mesh path."""
        inputs = {
            "mesh_path": "nonexistent_mesh.obj",
            "output_format": "obj",
        }

        with pytest.raises(Exception):
            fastmesh_adapter._process_request(inputs)

    def test_missing_mesh_path(self, fastmesh_adapter):
        """Test handling of missing mesh path."""
        inputs = {
            "output_format": "obj",
        }

        with pytest.raises(ValueError):
            fastmesh_adapter._process_request(inputs)

    def test_invalid_output_format(self, fastmesh_adapter, sample_mesh_path):
        """Test handling of invalid output format."""
        inputs = {
            "mesh_path": sample_mesh_path,
            "output_format": "invalid_format",
        }

        with pytest.raises(ValueError):
            fastmesh_adapter._process_request(inputs)


class TestFastMeshVariants:
    """Test suite for different FastMesh variants."""

    def test_v1k_adapter(self):
        """Test V1K variant adapter."""
        adapter = FastMeshRetopologyAdapter(
            model_id="test_v1k",
            variant="V1K",
        )
        assert adapter.variant == "V1K"
        assert adapter.target_vertex_count == 1000

    def test_v4k_adapter(self):
        """Test V4K variant adapter."""
        adapter = FastMeshRetopologyAdapter(
            model_id="test_v4k",
            variant="V4K",
        )
        assert adapter.variant == "V4K"
        assert adapter.target_vertex_count == 4000

    def test_invalid_variant(self):
        """Test handling of invalid variant."""
        # This should raise an error during runner initialization
        adapter = FastMeshRetopologyAdapter(
            model_id="test_invalid",
            variant="INVALID",
        )
        # The error will occur during model loading
        with pytest.raises(Exception):
            adapter.load(gpu_id=0)

