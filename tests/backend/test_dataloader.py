from pathlib import Path

import pytest
import pandas as pd
import numpy as np
import tifffile

from celltinder.backend.data_loader import DataLoader
from celltinder.backend.cell_image_set import CellImageSet 

# --- Fixtures and Helpers ---

@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing DataLoader."""
    data = {
        'ratio': [0.1, 0.5, 0.8],
        'centroid_y': [50, 60, 55],
        'centroid_x': [100, 110, 105],
        'fov_ID': ['A1', 'A2', 'A3'],
        'cell_numb': [1, 2, 3],
    }
    df = pd.DataFrame(data)
    csv_file = tmp_path / "test.csv"
    df.to_csv(csv_file, index=False)
    return csv_file

class DummyCellImageSet:
    def __init__(self, cell_centroid, pre_img_path, pre_mask_path, cell_mask_value, n_frames, box_size):
        self.cell_centroid = cell_centroid
        self.pre_img_path = pre_img_path
        self.pre_mask_path = pre_mask_path
        self.cell_mask_value = cell_mask_value
        self.n_frames = n_frames
        self.box_size = box_size

# --- Tests for DataLoader ---

def test_default_thresholds(sample_csv: Path):
    loader = DataLoader(sample_csv)
    # default_lower and default_upper come directly from the CSV column 'ratio'
    assert loader.default_lower == pytest.approx(0.1)
    assert loader.default_upper == pytest.approx(0.8)

def test_filter_data(sample_csv: Path):
    loader = DataLoader(sample_csv)
    # Filter to only include rows where ratio is between 0.3 and 0.9
    filtered = loader.filter_data(0.3, 0.9)
    # Should filter out the first row (0.1) and keep rows with 0.5 and 0.8
    assert len(filtered) == 2
    assert (filtered['ratio'] >= 0.3).all() and (filtered['ratio'] <= 0.9).all()

def test_get_cell_count(sample_csv: Path):
    loader = DataLoader(sample_csv)
    # Using thresholds that include only the second and third rows
    count = loader.get_cell_count(0.3, 1.0)
    assert count == 2

def test_update_thresholds_and_pos_df(sample_csv: Path):
    loader = DataLoader(sample_csv)
    # Set thresholds using the 'ratio' column
    loader.update_thresholds(0.3, 0.9, 'ratio')
    pos_df = loader.pos_df
    # pos_df should include only rows with ratio between 0.3 and 0.9,
    # sorted descending by ratio (i.e. [0.8, 0.5])
    expected_ratios = sorted([0.5, 0.8], reverse=True)
    assert list(pos_df['ratio']) == expected_ratios

def test_save_csv(sample_csv: Path):
    loader = DataLoader(sample_csv)
    # Add a new column and save
    loader.df['new_col'] = [1, 2, 3]
    loader.save_csv()
    # Read the saved file to verify changes
    df_saved = pd.read_csv(sample_csv)
    assert 'new_col' in df_saved.columns
    assert df_saved['new_col'].tolist() == [1, 2, 3]

def test_loads_arrays_pre_file_path(sample_csv: Path, monkeypatch):
    """Test the loads_arrays method of DataLoader. Just make sure that the pre_file_path are built correctly and that the cell data are extracted correctly."""
    
    
    # Monkeypatch the __init__ method of CellImageSet to use our dummy,
    # so we can capture the parameters passed by DataLoader.
    monkeypatch.setattr(CellImageSet, "__init__", DummyCellImageSet.__init__)

    loader = DataLoader(sample_csv)
    # Set thresholds using the 'ratio' column; here, [0.0, 1.0] ensures all rows are included.
    loader.update_thresholds(0.0, 1.0, 'ratio')
    
    # pos_df is sorted in descending order by ratio.
    # In our CSV the row with ratio 0.8 (with fov_ID 'B4') comes first.
    cell_idx = 0
    expected_fov_ID = 'A3'
    expected_centroid = (55, 105)  # (centroid_y, centroid_x)

    # Compute expected directories based on the CSV parent directory
    project_path = sample_csv.parent
    # Since fov_ID is "A3", well_ID is "A3"
    expected_img_dir = project_path.joinpath("A3_images")
    expected_mask_dir = project_path.joinpath("A3_masks")


    n_frames = 3
    box_size = 150

    # Call loads_arrays. This should internally build the pre_file_path using the fov_ID and label.
    dummy_set = loader.loads_arrays(
        cell_idx=cell_idx,
        img_label='measure',
        mask_label='mask',
        n_frames=n_frames,
        crop_size=box_size
    )

    # Verify that the extracted centroid matches the expected value.
    assert dummy_set.cell_centroid == expected_centroid

    # Verify that the pre_img_path and pre_mask_path are built correctly.
    expected_img_path = expected_img_dir.joinpath(f"{expected_fov_ID}_measure.tif")
    expected_mask_path = expected_mask_dir.joinpath(f"{expected_fov_ID}_mask.tif")
    assert dummy_set.pre_img_path == expected_img_path
    assert dummy_set.pre_mask_path == expected_mask_path

    # Also verify that the other parameters are passed along correctly.
    assert dummy_set.n_frames == n_frames
    assert dummy_set.box_size == box_size

