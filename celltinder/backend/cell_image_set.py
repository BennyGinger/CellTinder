from pathlib import Path

import tifffile as tiff
import numpy as np


class CellImageSet:
    """ Class to load and crop all images and masks from a specific cell."""
    
    def __init__(self, cell_centroid: tuple[float, float], pre_img_path: Path, pre_mask_path: Path, cell_mask_value: int, n_frames: int, box_size: int) -> None:
        """Initialize the CellArrays object with the paths to the images and masks. 
        
        Args:
            cell_centroid: The centroid of the cell to crop around
            pre_img_path: Pre path to the img files, which contains the extension but lack the frame number
            pre_mask_path: Pre path to the mask files, which contains the extension but lack the frame number
            cell_mask_value: The value of the cell in the mask
            n_frames: Number of frames to load
            box_size: Size of the cropped images
        """
        
        # Build the paths for all images and masks
        self.imgs = self._loads_arrays(pre_img_path, n_frames, box_size, cell_centroid)
        self.masks = self._loads_arrays(pre_mask_path, n_frames, box_size, cell_centroid, cell_mask_value)
        
    def _loads_arrays(self, pre_file_path: Path, n_frames: int, box_size: int, cell_centroid: tuple[float, float], cell_mask_value: int = None) -> dict[int, np.ndarray]:
        """Load and crop all images or masks from a specified folder.
        
        Args:
            pre_file_path: Path to the image or mask files, which contains the extension but lack the frame number
            n_frames: Number of frames to load
            box_size: Size of the cropped images
            cell_centroid: Centroid of the cell to crop around
        Returns:
            dict: A dictionary with frame numbers as keys and the corresponding cropped images or masks as values.
        """
        arrays: dict[int, np.ndarray] = {}
        for frame in range(1, n_frames + 1):
            # Get the file path for the current frame
            file_path = self._build_file_path(pre_file_path, frame)
            
            # Load and crop the array
            arrays[frame] = self._crop_array(file_path, cell_centroid, box_size, cell_mask_value)
        return arrays

    @staticmethod
    def _build_file_path(pre_file_path: Path, frame: int) -> Path:
        """Build the file path for a specific frame.
        Args:
            pre_file_path: Path to the image or mask files, which contains the extension but lack the frame number
            frame: Frame number to append to the file name
        Returns:
            file_path: Full path to the image or mask file for the specified frame.
        Raises:
            FileNotFoundError: If the file does not exist at the specified path.
        """
        # Build the file name
        file_name = f"{pre_file_path.stem}_{frame}{pre_file_path.suffix}"
        
        # Build the full path
        file_path = pre_file_path.parent.joinpath(file_name)
        
        # Check if the file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at: {file_path}")
        return file_path
    
    @staticmethod      
    def _crop_array(path: Path, cell_centroid: tuple[float, float], size: int, cell_mask_value: int | None) -> np.ndarray:
        """
        Crop a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros.
        Args:
            path: Path to the image or mask file
            cell_centroid: Centroid of the cell to crop around
            size: Size of the cropped image
        Returns:
            np.ndarray: Cropped and padded array
        Raises:
            FileNotFoundError: If the file does not exist at the specified path.
            IOError: If there is an error reading the image file.
        """
        try:
            arr = tiff.imread(path)
        except FileNotFoundError as f:
            raise FileNotFoundError(f"Image file not found at: {path}") from f
        except Exception as e:
            raise IOError(f"Error reading image file at {path}: {e}") from e
        return CellImageSet._box_array(arr, cell_centroid, size, cell_mask_value)
    
    @staticmethod
    def _box_array(array: np.ndarray, cell_centroid: tuple[float, float], crop_size: int, cell_mask_value: int | None) -> np.ndarray:
        """
        Box a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros.
        Args:
            array: 2D array to crop
            cell_centroid: Centroid of the cell to crop around
            size: Size of the cropped image
        Returns:
            np.ndarray: Cropped and padded array
        """
        # Calculate the half size of the box
        half = crop_size // 2
        y, x = cell_centroid
        
        # Desired indices
        x_min = int(x) - half
        x_max = x_min + crop_size
        y_min = int(y) - half
        y_max = y_min + crop_size
        
        # Determine how much padding is needed
        return CellImageSet._pad_array(array, x_min, x_max, y_min, y_max, cell_mask_value)

    @staticmethod
    def _pad_array(array: np.ndarray, x_min: int, x_max: int, y_min: int, y_max: int, cell_mask_value: int | None) -> np.ndarray:
        """Pad a cropped array to match the desired size."""
        
        # Crop region (only the part that lies within the array)
        cropped = array[max(y_min, 0):min(y_max, array.shape[0]),
                        max(x_min, 0):min(x_max, array.shape[1])]
        
        # If cell_mask_value is provided, remove all values that are not equal to cell_mask_value
        if cell_mask_value is not None:
            cropped[cropped != cell_mask_value] = 0
        
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

