from functools import cached_property
from pathlib import Path

import pandas as pd

from celltinder.backend.cell_image_set import CellImageSet

   
class DataLoader:
    """Class to load and filter data from a CSV file."""
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        self.ratios = self.df['ratio']

    def filter_data(self, lower: float, upper: float, col_name: str = 'ratio') -> pd.DataFrame:
        """Filter the data based on the lower and upper thresholds."""
        
        return self.df[(self.df[col_name] >= lower) & (self.df[col_name] <= upper)]

    def get_cell_count(self, lower: float, upper: float) -> int:
        """Get the cell count based on the lower and upper thresholds."""
        
        filtered = self.filter_data(lower, upper)
        return len(filtered)
    
    def update_thresholds(self, lower: float, upper: float, new_column: str) -> None:
        """Update the thresholds and add a new column to the DataFrame."""
        
        self.lower = lower
        self.upper = upper
        self.column_thresholds = new_column
    
    def save_csv(self) -> None:
        """Save the data to a new CSV file."""
        self.df.to_csv(self.csv_path, index=False)

    def loads_arrays(self, cell_idx: int, img_folder: Path, mask_folder: Path, img_label: str = 'measure', mask_label: str = 'mask', n_frames: int = 2, box_size: int = 150) -> CellImageSet:
        """Load and crop all images or masks for a specific cell.
        
        Args:
            cell_idx: Index of the cell to load from the dataframe
            img_folder: Path to the folder containing the images
            mask_folder: Path to the folder containing the masks
            img_label: Label of the image files
            mask_label: Label of the mask files
            n_frames: Number of frames to load
            box_size: Size of the cropped images
        
        Returns:
            CellArrays: A CellArrays object containing the loaded and cropped images and masks
        """
        
        # Check that threshold have been set
        if not hasattr(self, 'lower') or not hasattr(self, 'upper'):
            raise ValueError("Thresholds must be set before loading arrays.")
        
        # Get the positive cells
        pos_df = self.pos_df
        
        # Extract cell specific parameters
        cell_centroid: tuple[float, float] = tuple(pos_df[['centroid_y', 'centroid_x']].iloc[cell_idx].values)
        fov_ID = pos_df['fov_ID'].iloc[cell_idx]
        
        # Buidl arrays file paths
        pre_img_path = img_folder.joinpath(f"{fov_ID}_{img_label}.tif")
        pre_mask_path = mask_folder.joinpath(f"{fov_ID}_{mask_label}.tif")
        
        return CellImageSet(cell_centroid, pre_img_path, pre_mask_path, n_frames, box_size)
    
    @property
    def default_lower(self) -> float:
        """Return the default lower threshold."""
        return self.ratios.min()
    
    @property
    def default_upper(self) -> float:
        """Return the default upper threshold."""
        return self.ratios.max()
    
    @cached_property
    def pos_df(self) -> pd.DataFrame:
        """Return the DataFrame containing positive cells sorted by ratio."""
        
        return self.filter_data(self.lower, self.upper, self.column_thresholds).sort_values(by='ratio', ascending=False)
