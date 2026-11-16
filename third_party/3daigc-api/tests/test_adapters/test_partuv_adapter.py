"""
Unit tests for PartUV UV unwrapping adapter.
"""

import os
import pytest
import tempfile
from pathlib import Path

from adapters.partuv_adapter import PartUVUnwrappingAdapter


@pytest.fixture
def partuv_adapter():
    """Create a PartUV adapter instance for testing."""
    adapter = PartUVUnwrappingAdapter(
        model_id="test_partuv",
        vram_requirement=4096,
    )
    return adapter


@pytest.fixture
def sample_mesh_path():
    """Provide a sample mesh file path for testing."""
    # Use a sample mesh from the assets folder
    mesh_path = "assets/example_uv/max-planck.obj"
    if os.path.exists(mesh_path):
        return mesh_path
    pytest.skip("Sample mesh file not found")


class TestPartUVAdapter:
    """Test suite for PartUV UV unwrapping adapter."""

    def test_adapter_initialization(self, partuv_adapter):
        """Test that the adapter initializes correctly."""
        assert partuv_adapter.model_id == "test_partuv"
        assert partuv_adapter.feature_type == "uv_unwrapping"
        assert partuv_adapter.distortion_threshold == 1.25

    def test_supported_formats(self, partuv_adapter):
        """Test that the adapter reports correct supported formats."""
        formats = partuv_adapter.get_supported_formats()
        assert "input" in formats
        assert "output" in formats
        assert "obj" in formats["input"]
        assert "glb" in formats["input"]
        assert "obj" in formats["output"]

    @pytest.mark.skipif(
        not os.path.exists("pretrained/PartUV/model_objaverse.ckpt"),
        reason="PartField model not available",
    )
    def test_model_loading(self, partuv_adapter):
        """Test that the model can be loaded."""
        try:
            partuv_adapter.load(gpu_id=0)
            assert partuv_adapter.status.value == "loaded"
            assert partuv_adapter.model is not None
        finally:
            partuv_adapter.unload()

    @pytest.mark.skipif(
        not os.path.exists("pretrained/PartUV/model_objaverse.ckpt"),
        reason="PartField model not available",
    )
    def test_uv_unwrapping_process(self, partuv_adapter, sample_mesh_path):
        """Test the UV unwrapping process with a sample mesh."""
        try:
            # Load model
            partuv_adapter.load(gpu_id=0)

            # Process mesh
            inputs = {
                "mesh_path": sample_mesh_path,
                "output_format": "obj",
                "distortion_threshold": 1.25,
                "pack_method": "none",  # Skip packing for faster testing
                "save_individual_parts": True,
                "save_visuals": False,
            }

            result = partuv_adapter.process(inputs)

            # Validate result
            assert result is not None
            assert "output_mesh_path" in result
            assert "num_components" in result
            assert "distortion" in result
            assert "success" in result
            assert result["success"] is True

            # Check that output file exists
            output_path = Path(result["output_mesh_path"])
            assert output_path.exists()

            # Check UV info
            assert result["num_components"] > 0
            assert result["distortion"] > 0

        finally:
            partuv_adapter.unload()

    def test_invalid_mesh_path(self, partuv_adapter):
        """Test handling of invalid mesh path."""
        inputs = {
            "mesh_path": "nonexistent_mesh.obj",
            "output_format": "obj",
        }

        with pytest.raises(Exception):
            partuv_adapter._process_request(inputs)

    def test_missing_mesh_path(self, partuv_adapter):
        """Test handling of missing mesh path."""
        inputs = {
            "output_format": "obj",
        }

        with pytest.raises(ValueError):
            partuv_adapter._process_request(inputs)

    def test_invalid_output_format(self, partuv_adapter, sample_mesh_path):
        """Test handling of invalid output format."""
        inputs = {
            "mesh_path": sample_mesh_path,
            "output_format": "invalid_format",
        }

        with pytest.raises(ValueError):
            partuv_adapter._process_request(inputs)

    def test_invalid_pack_method(self, partuv_adapter, sample_mesh_path):
        """Test handling of invalid pack method."""
        inputs = {
            "mesh_path": sample_mesh_path,
            "output_format": "obj",
            "pack_method": "invalid_method",
        }

        with pytest.raises(ValueError):
            partuv_adapter._process_request(inputs)

