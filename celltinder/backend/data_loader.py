from __future__ import annotations

from pathlib import Path

import pandas as pd

from celltinder.backend.cell_image_set import CellImageSet


DEFAULT_COL_NAME = 'ratio'
# TODO: implement a frame column in the csv file -> self.n_frames can then be set automatically

class DataLoader:
    """
    Class to load and filter data from a CSV file. Specific to your our pipeline.
    """
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        self.ratios = self.df[DEFAULT_COL_NAME]
        
        # Set default thresholds
        self.lower = self.default_lower
        self.upper = self.default_upper
        self.column_thresholds = DEFAULT_COL_NAME

    def filter_data(self, lower: float, upper: float, col_name: str = DEFAULT_COL_NAME) -> pd.DataFrame:
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
        filtered = self.filter_data(lower, upper)
        return len(filtered)
    
    def update_thresholds(self, lower: float, upper: float, new_column: str) -> None:
        """
        Update the thresholds and add a new column to the DataFrame.
        """
        self.lower = lower
        self.upper = upper
        self.column_thresholds = new_column
    
    def save_csv(self) -> None:
        """
        Save the data to a new CSV file.
        """
        self.df.to_csv(self.csv_path, index=False)

    def loads_arrays(self, cell_idx: int, img_label: str, mask_label: str, n_frames: int, crop_size: int) -> CellImageSet:
        """
        Load and crop all images or masks for a specific cell.
        
        Args:
            cell_idx: Index of the cell to load from the dataframe
            img_label: Label of the image files
            mask_label: Label of the mask files
            n_frames: Number of frames to load
            box_size: Size of the cropped images
        
        Returns:
            CellArrays: A CellArrays object containing the loaded and cropped images and masks
        """
        # Get the positive cells
        pos_df = self.pos_df
        
        # Extract cell specific parameters
        cell_centroid: tuple[float, float] = tuple(pos_df[['centroid_y', 'centroid_x']].iloc[cell_idx].values)
        fov_ID = pos_df['fov_ID'].iloc[cell_idx]
        cell_mask_value = pos_df['cell_numb'].iloc[cell_idx]
        
        # Build img and mask directories
        img_dir, mask_dir = self._build_image_mask_dirs(fov_ID)
        
        # Build arrays file pre-paths (missing the frame number)
        pre_img_path = img_dir.joinpath(f"{fov_ID}_{img_label}.tif")
        pre_mask_path = mask_dir.joinpath(f"{fov_ID}_{mask_label}.tif")
        
        return CellImageSet(cell_centroid, pre_img_path, pre_mask_path, cell_mask_value, n_frames, crop_size)

    def _build_image_mask_dirs(self, fov_ID: str) -> tuple[Path, Path]:
        """
        Build the image and mask directories based on the fov_ID.
        """
        # Build the folder names
        well_ID = fov_ID.split('_')[0]
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
        """Return the DataFrame containing positive cells sorted by DEFAULT_COL_NAME."""
        
        return self.filter_data(self.lower, self.upper, self.column_thresholds).sort_values(by=DEFAULT_COL_NAME, ascending=False)
