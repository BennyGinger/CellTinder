import pytest
import numpy as np
import tifffile
from pathlib import Path
from celltinder.backend.cell_image_set import CellImageSet

# --- Fixtures and Helpers ---

def create_dummy_tiff(file_path: Path, shape=(100, 100), value=1):
    """Helper to write a dummy TIFF file."""
    arr = np.full(shape, value, dtype=np.uint8)
    tifffile.imwrite(file_path, arr)

@pytest.fixture
def dummy_images(tmp_path: Path):
    """
    Create a temporary folder structure with dummy image and mask TIFF files.
    Files are named so that the CellImageSet class will build paths as:
    {fov_ID}_{label}_{frame}.tif.
    """
    img_folder = tmp_path / "images"
    mask_folder = tmp_path / "masks"
    img_folder.mkdir()
    mask_folder.mkdir()
    
    # Pre file paths (the base file names, without the frame number)
    pre_img_path = img_folder / "001_measure.tif"
    pre_mask_path = mask_folder / "001_mask.tif"
    
    n_frames = 2
    for frame in range(1, n_frames + 1):
        img_file = img_folder / f"001_measure_{frame}.tif"
        mask_file = mask_folder / f"001_mask_{frame}.tif"
        # Create dummy arrays with a constant value (different per frame for clarity)
        create_dummy_tiff(img_file, shape=(100, 100), value=frame)
        create_dummy_tiff(mask_file, shape=(100, 100), value=frame + 10)
    
    return pre_img_path, pre_mask_path, n_frames

# --- Tests for CellImageSet ---

def test_cellimageset_loading(dummy_images):
    pre_img_path, pre_mask_path, n_frames = dummy_images
    # Use a cell centroid that is centrally located so that no padding is required.
    cell_centroid = (50, 50)
    box_size = 50  # crop to a 50x50 image
    
    cell_set = CellImageSet(cell_centroid, pre_img_path, pre_mask_path, n_frames, box_size)
    # Verify that for each frame the cropped images and masks have the correct dimensions.
    for frame in range(1, n_frames + 1):
        assert cell_set.imgs[frame].shape == (box_size, box_size)
        assert cell_set.masks[frame].shape == (box_size, box_size)

def test_cropping_with_padding(tmp_path: Path):
    """
    Test cropping behavior when the cell centroid is near the edge,
    forcing padding to be applied.
    """
    img_folder = tmp_path / "images"
    mask_folder = tmp_path / "masks"
    img_folder.mkdir()
    mask_folder.mkdir()
    
    pre_img_path = img_folder / "002_measure.tif"
    pre_mask_path = mask_folder / "002_mask.tif"
    
    n_frames = 1
    # Create a small dummy image (10x10) so that the crop window exceeds the image dimensions.
    dummy_array = np.arange(100).reshape((10, 10)).astype(np.uint8)
    tifffile.imwrite(img_folder / "002_measure_1.tif", dummy_array)
    tifffile.imwrite(mask_folder / "002_mask_1.tif", dummy_array)
    
    # Set a cell centroid near the top-left corner. With a box_size of 8, the crop will require padding.
    cell_centroid = (2, 2)
    box_size = 8
    
    cell_set = CellImageSet(cell_centroid, pre_img_path, pre_mask_path, n_frames, box_size)
    
    cropped_img = cell_set.imgs[1]
    cropped_mask = cell_set.masks[1]
    # The cropped output should always be (box_size, box_size)
    assert cropped_img.shape == (box_size, box_size)
    assert cropped_mask.shape == (box_size, box_size)
    # Since the crop window extends beyond the top and left of the array, expect zeros in those padded areas.
    # For example, the top-left corner (first few rows/columns) of the cropped image should be 0.
    assert np.all(cropped_img[:2, :2] == 0)

def test_build_file_path_error(tmp_path: Path):
    """
    Test that _build_file_path raises a FileNotFoundError if the expected file does not exist.
    """
    from celltinder.backend.cell_image_set import CellImageSet
    fake_path = tmp_path / "fake_measure.tif"
    with pytest.raises(FileNotFoundError):
        CellImageSet._build_file_path(fake_path, 1)
