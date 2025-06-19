from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from celltinder.backend.cell_image_set import CellImageSet

DEFAULT_COL_NAME = 'ratio'

class DataLoader:
    """
    Class to load and filter data from a CSV file. Specific to your our pipeline.
    """
    
    def __init__(self, csv_file: Path, n_frames: int, crop_size: int) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.n_frames = n_frames
        self.crop_size = crop_size
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        if 'Unnamed: 0' in self.df.columns:
            self.df.drop(columns=['Unnamed: 0'], inplace=True)
        self.ratios = self.df[DEFAULT_COL_NAME]
        
        # Set default thresholds
        self.load_threshold_bounds()

    def filter_ratio(self, lower: float, upper: float, col_name: str = 'ratio') -> pd.DataFrame:
        """
        Filter the data based on the lower and upper thresholds.
        Args:
            lower: Lower threshold
            upper: Upper threshold
            col_name: Column name to filter on
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        return self.df[(self.df[col_name] >= lower) & (self.df[col_name] <= upper)]

    def get_cell_count(self, lower: float, upper: float) -> int:
        """
        Get the cell count based on the lower and upper thresholds.
        Args:
            lower: Lower threshold
            upper: Upper threshold
        Returns:
            int: Number of cells within the thresholds
        """
        filtered = self.filter_ratio(lower, upper)
        return len(filtered)
    
    def save_csv(self) -> None:
        """
        Save the data to a new CSV file.
        """
        self.df.to_csv(self.csv_path, index=False)

    def loads_arrays(self, cell_idx: int, img_label: str = 'measure', mask_label: str = 'mask') -> CellImageSet:
        """
        Load and crop all images or masks for a specific cell.
        
        Args:
            cell_idx: Index of the cell to load from the dataframe
            img_label: Label of the image files
            mask_label: Label of the mask files
        
        Returns:
            CellArrays: A CellArrays object containing the loaded and cropped images and masks
        """
        # Get the positive cells
        pos_df = self.pos_df
        
        # Extract cell specific parameters
        cell_centroid: tuple[float, float] = tuple(pos_df[['centroid_y', 'centroid_x']].iloc[cell_idx].values)
        fov_id = pos_df['fov_ID'].iloc[cell_idx]
        cell_mask_value = pos_df['cell_numb'].iloc[cell_idx]
        
        # Build img and mask directories
        img_dir, mask_dir = self._build_image_mask_dirs(fov_id)
        
        # Build arrays file pre-paths (missing the frame number)
        pre_img_path = img_dir.joinpath(f"{fov_id}_{img_label}.tif")
        pre_mask_path = mask_dir.joinpath(f"{fov_id}_{mask_label}.tif")
        
        return CellImageSet(cell_centroid, pre_img_path, pre_mask_path, cell_mask_value, self.n_frames, self.crop_size)

    def _build_image_mask_dirs(self, fov_id: str) -> tuple[Path, Path]:
        """
        Build the image and mask directories based on the fov_id.
        """
        # Build the folder names
        # FIXME: I need to change the split to 'P' later on
        well_ID = fov_id.split('_')[0]
        img_folder_name = f"{well_ID}_images"
        mask_folder_name = f"{well_ID}_masks"
        # Build the folder paths
        project_path = self.csv_path.parent
        img_path = project_path.joinpath(img_folder_name)
        mask_path = project_path.joinpath(mask_folder_name)
        return img_path, mask_path
    
    def add_process_col(self) -> None:
        """Add a 'process' column to the DataFrame."""
        
        if 'process' not in self.df.columns:
            self.df['process'] = False
    
    def update_cell_to_process_in_df(self, pos_df: pd.DataFrame) -> None:
        """Update the DataFrame with the cells to process."""
        
        self.df.update(pos_df)
    
    def load_threshold_bounds(self) -> tuple[float, float]:
        """
        Check if the DataFrame contains a threshold column that follows the pattern "float < x < float".
        If found, extract the lower and upper bounds; otherwise, use default values.
        """
        pattern = r"([\d\.]+)\s*<\s*x\s*<\s*([\d\.]+)"
        cols = [c for c in self.df.columns if "< x <" in c]

        # start with the defaults
        lower, upper = self.default_lower, self.default_upper
        col_name = None

        if cols:
            col_name = cols[0]
            m = re.match(pattern, col_name)
            if m:
                lower, upper = float(m.group(1)), float(m.group(2))

        # now set once
        self.lower, self.upper, self.column_thresholds = lower, upper, col_name
        return lower, upper
    
    @property
    def default_lower(self) -> float:
        """Return the default lower threshold."""
        return self.ratios.min()
    
    @property
    def default_upper(self) -> float:
        """Return the default upper threshold."""
        return self.ratios.max()
    
    @property
    def pos_df(self) -> pd.DataFrame:
        """Return the DataFrame containing positive cells sorted by ratio."""
        if self.column_thresholds is None:
            raise ValueError("No threshold column found. Please set thresholds first.")
        return self.df.loc[self.df[self.column_thresholds] == True].sort_values(by='ratio', ascending=False)
