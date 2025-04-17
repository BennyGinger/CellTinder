from pathlib import Path
import re

import pandas as pd

from celltinder.backend.cell_image_set import CellImageSet

   
class DataLoader:
    """Class to load and filter data from a CSV file. Specific to your our pipeline."""
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        self.ratios = self.df['ratio']
        # Set default thresholds
        self.retrieve_threshold_range()

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
    
    # TODO: Merge with retrieve_threshold_range
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

    def loads_arrays(self, cell_idx: int, img_label: str = 'measure', mask_label: str = 'mask', n_frames: int = 2, crop_size: int = 151) -> CellImageSet:
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
    
    def retrieve_threshold_range(self) -> tuple[float, float]:
        """
        Check if the DataFrame contains a threshold column that follows the pattern "float < x < float".
        If found, extract the lower and upper bounds; otherwise, use default values.
        """
        threshold_cols = [col for col in self.df.columns if "< x <" in col]
        if threshold_cols:
            # Extract the two float values using a regex pattern.
            pattern = r"([\d\.]+)\s*<\s*x\s*<\s*([\d\.]+)"
            match = re.match(pattern, threshold_cols[0])
            if match:
                lower_bound = float(match.group(1))
                upper_bound = float(match.group(2))
                self.update_thresholds(lower_bound, upper_bound, threshold_cols[0])
            else:
                # Fall back to default values if regex fails.
                lower_bound = self.default_lower
                upper_bound = self.default_upper
        else:
            # If no threshold column is found, set default values.
            lower_bound = self.default_lower
            upper_bound = self.default_upper
            self.update_thresholds(self.default_lower, self.default_upper, None)
        return lower_bound, upper_bound
    
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
