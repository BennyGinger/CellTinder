from pathlib import Path

import pandas as pd
import tifffile as tiff
import numpy as np


class CellArrays:
    """ Class to load and crop all cell images and masks from Series."""
    
    def __init__(self, cell_centroid: tuple[float, float], pre_img_path: Path, pre_mask_path: Path, n_frames: int = 2, box_size: int = 150) -> None:
        """Initialize the CellArrays object with the paths to the images and masks. 
        
        Args:
            cell_centroid: The centroid of the cell to crop around
            pre_img_path: Pre path to the img files, which contains the extension but lack the frame number
            pre_mask_path: Pre path to the mask files, which contains the extension but lack the frame number
            n_frames: Number of frames to load
            box_size: Size of the cropped images"""
        
        # Build the paths for all images and masks
        self.imgs = self.loads_arrays(pre_img_path, n_frames, box_size, cell_centroid)
        self.masks = self.loads_arrays(pre_mask_path, n_frames, box_size, cell_centroid)
        
    def loads_arrays(self, pre_file_path: Path, n_frames: int, box_size: int, cell_centroid: tuple[float, float]) -> dict[int, np.ndarray]:
        """Load and crop all images or masks from a specified folder.
        
        Args:
            pre_file_path: Path to the image or mask files, which contains the extension but lack the frame number
            n_frames: Number of frames to load
            box_size: Size of the cropped images
            cell_centroid: Centroid of the cell to crop around"""
        
        arrays: dict[int, np.ndarray] = {}
        for frame in range(1, n_frames + 1):
            # Get the file path for the current frame
            file_path = self._build_file_path(pre_file_path, frame)
            
            # Load and crop the array
            arrays[frame] = self._crop_array(file_path, cell_centroid, box_size)
        return arrays

    @staticmethod
    def _build_file_path(pre_file_path: Path, frame: int) -> Path:
        # Build the file name
        file_name = f"{pre_file_path.stem}_{frame}{pre_file_path.suffix}"
        
        # Build the full path
        file_path = pre_file_path.parent.joinpath(file_name)
        
        # Check if the file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at: {file_path}")
        return file_path
    
    @staticmethod      
    def _crop_array(path: Path, cell_centroid: tuple[float, float], size: int) -> np.ndarray:
        """Crop a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros."""
        
        try:
            arr = tiff.imread(path)
        except FileNotFoundError as f:
            raise FileNotFoundError(f"Image file not found at: {path}") from f
        except Exception as e:
            raise IOError(f"Error reading image file at {path}: {e}") from e
        return CellArrays._box_array(arr, cell_centroid, size)
    
    @staticmethod
    def _box_array(array: np.ndarray, cell_centroid: tuple[float, float], size: int) -> np.ndarray:
        """Box a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros."""
        
        half = size // 2
        y, x = cell_centroid
        
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

    def loads_arrays(self, cell_idx: int, img_folder: Path, mask_folder: Path, img_label: str = 'measure', mask_label: str = 'mask', n_frames: int = 2, box_size: int = 150) -> CellArrays:
        """Load and crop all images or masks from a specified folder.
        
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
        pos_df = self.filter_data(self.lower, self.upper, self.column_thresholds)
        
        # Extract cell specific parameters
        cell_centroid: tuple[float, float] = tuple(pos_df[['centroid_y', 'centroid_x']].iloc[cell_idx].values)
        fov_ID = pos_df['fov_ID'].iloc[cell_idx]
        
        # Buidl arrays file paths
        pre_img_path = img_folder.joinpath(f"{fov_ID}_{img_label}.tif")
        pre_mask_path = mask_folder.joinpath(f"{fov_ID}_{mask_label}.tif")
        
        return CellArrays(cell_centroid, pre_img_path, pre_mask_path, n_frames, box_size)
    
    @property
    def default_lower(self) -> float:
        """Return the default lower threshold."""
        return self.ratios.min()
    
    @property
    def default_upper(self) -> float:
        """Return the default upper threshold."""
        return self.ratios.max()
