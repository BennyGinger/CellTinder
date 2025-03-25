from pathlib import Path

import pandas as pd
import tifffile as tiff
import numpy as np


class DataLoader:
    """Class to load and filter data from a CSV file."""
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        self.ratios = self.df['ratio']
        self.default_lower: float = self.ratios.min()
        self.default_upper: float = self.ratios.max()

    def filter_data(self, lower: float, upper: float, col_name: str = 'ratio') -> pd.DataFrame:
        """Filter the data based on the lower and upper thresholds."""
        
        return self.df[(self.df[col_name] >= lower) & (self.df[col_name] <= upper)]

    def get_cell_count(self, lower: float, upper: float) -> int:
        """Get the cell count based on the lower and upper thresholds."""
        
        filtered = self.filter_data(lower, upper)
        return len(filtered)
    
    def save_csv(self, new_column: str) -> None:
        """Save the data to a new CSV file."""
        
        # Save the new threshold within the class
        self.thresholds = new_column
        
        # Save the DataFrame to a new CSV file
        self.df.to_csv(self.csv_path, index=False)

    # Add the CellArrays processing method here
    
    
    
# Pipeline related constants 
# TODO: Pass these as parameters in the future
IMG_LABEL = 'measure'
MASK_LABEL = 'mask'
DEFAULT_SIZE = 150 # Default size for cropping, in pixels


class CellArrays:
    """ Class to load and crop all cell images and masks from Series."""
    
    def __init__(self, cell_data: pd.Series, folder_path: Path):
        """Initialize the CellArrays object with a Series of cell data and a folder path."""
        
        # Extract the relevant data
        fov_ID: str = cell_data.fov_ID
        y: float = cell_data.centroid_y
        x: float = cell_data.centroid_x
        
        # Determine all the paths
        img_folder = f"{folder_path.name}_images"
        mask_folder = f"{folder_path.name}_masks"
        img_path1: Path = folder_path.joinpath(img_folder, f"{fov_ID}_{IMG_LABEL}_1.tif")
        img_path2: Path = folder_path.joinpath(img_folder, f"{fov_ID}_{IMG_LABEL}_2.tif")
        mask_path1: Path = folder_path.joinpath(mask_folder, f"{fov_ID}_{MASK_LABEL}_1.tif")
        mask_path2: Path = folder_path.joinpath(mask_folder, f"{fov_ID}_{MASK_LABEL}_2.tif")
        
        # Load the images and masks
        self.img1 = self.crop_array(img_path1, x, y, DEFAULT_SIZE)
        self.img2 = self.crop_array(img_path2, x, y, DEFAULT_SIZE)
        self.mask1 = self.crop_array(mask_path1, x, y, DEFAULT_SIZE)
        self.mask2 = self.crop_array(mask_path2, x, y, DEFAULT_SIZE)
        
    def crop_array(self, path: Path, x: float, y: float, size: int) -> np.ndarray:
        """Crop a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros."""
        
        try:
            arr = tiff.imread(path)
        except FileNotFoundError as f:
            raise FileNotFoundError(f"Image file not found at: {path}") from f
        except Exception as e:
            raise IOError(f"Error reading image file at {path}: {e}") from e
        return self._box_array(arr, x, y, size)
    
    @staticmethod
    def _box_array(array: np.ndarray, x: float, y: float, size: int) -> np.ndarray:
        """Box a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros."""
        
        half = size // 2
        
        # Desired indices
        x_min = int(x) - half
        x_max = x_min + size
        y_min = int(y) - half
        y_max = y_min + size
        
        # Determine how much padding is needed
        return CellArrays._pad_array(array, x_min, x_max, y_min, y_max)

    @staticmethod
    def _pad_array(array: np.ndarray, x_min: int, x_max: int, y_min: int, y_max: int) -> np.ndarray:
        """Pad a cropped array to match the desired size."""
        
        # Crop region (only the part that lies within the array)
        cropped = array[max(y_min, 0):min(y_max, array.shape[0]),
                        max(x_min, 0):min(x_max, array.shape[1])]
        
        # Determine how much padding is needed
        pad_top = 0 - y_min if y_min < 0 else 0
        pad_left = 0 - x_min if x_min < 0 else 0
        pad_bottom = y_max - array.shape[0] if y_max > array.shape[0] else 0
        pad_right = x_max - array.shape[1] if x_max > array.shape[1] else 0
        
        # Apply padding if needed
        if any((pad_top, pad_bottom, pad_left, pad_right)):
            return np.pad(cropped, 
                        ((pad_top, pad_bottom), (pad_left, pad_right)), 
                        mode='constant', 
                        constant_values=0)                   
        return cropped
    
    