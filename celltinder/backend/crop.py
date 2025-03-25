from pathlib import Path

from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib as mpl


def crop_array(array: np.ndarray, x: float, y: float, size: int) -> np.ndarray:
    """Crop a 2D array around a specified point. If the crop region extends beyond the array, pad with zeros."""
    
    half = size // 2
    
    # Desired indices
    x_min = int(x) - half
    x_max = x_min + size
    y_min = int(y) - half
    y_max = y_min + size
    
    # Crop region (only the part that lies within the array)
    cropped = array[max(y_min, 0):min(y_max, array.shape[0]),
                    max(x_min, 0):min(x_max, array.shape[1])]
    
    # Determine how much padding is needed
    cropped = _pad_array(array.shape, x_min, x_max, y_min, y_max, cropped)
    return cropped

def _pad_array(arr_shape: tuple[int, int], x_min: int, x_max: int, y_min: int, y_max: int, cropped) -> np.ndarray:
    """Pad a cropped array to match the desired size."""
    
    # Determine how much padding is needed
    pad_top = 0 - y_min if y_min < 0 else 0
    pad_left = 0 - x_min if x_min < 0 else 0
    pad_bottom = y_max - arr_shape[0] if y_max > arr_shape[0] else 0
    pad_right = x_max - arr_shape[1] if x_max > arr_shape[1] else 0
    
    # Apply padding if needed
    if any((pad_top, pad_bottom, pad_left, pad_right)):
        return np.pad(cropped, 
                      ((pad_top, pad_bottom), (pad_left, pad_right)), 
                      mode='constant', 
                      constant_values=0)                   
    return cropped

def load_arrays(folder_path: Path, cell_row: pd.Series) -> np.ndarray:
    """Load an image array from a specified row in a DataFrame."""
    
    img_path = Path(cell_row['image_path'])
    return tiff.imread(img_path)




def main():

    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")

    data = pd.read_csv(csv_path, index_col=0).reset_index(drop=True)

    # Select rows where 2.0 < x < 5.0
    pos = data.loc[data['2.0 < x < 5.0'] == True].copy()
    
    # Select the first cell
    cell = pos.iloc[0]
    base_path = csv_path.parent
    img_folder = f"{base_path.name}_images"
    mask_folder = f"{base_path.name}_masks"
    img_cond = "measure"
    mask_cond = "mask"
    frame_1 = "1"
    frame_2 = "2"
    
    img_path1 = base_path.joinpath(img_folder, f"{cell.fov_ID}_{img_cond}_{frame_1}.tif")
    img1 = tiff.imread(img_path1)
    img_path2 = base_path.joinpath(img_folder, f"{cell.fov_ID}_{img_cond}_{frame_2}.tif")
    img2 = tiff.imread(img_path2)
    mask_path1 = base_path.joinpath(mask_folder, f"{cell.fov_ID}_{mask_cond}_{frame_1}.tif")
    mask_path2 = base_path.joinpath(mask_folder, f"{cell.fov_ID}_{mask_cond}_{frame_2}.tif")
    
    # Crop img
    # cent_y = cell.centroid_y
    # cent_x = cell.centroid_x
    cent_y = 160
    cent_x = 9
    print(cent_x, cent_y)
    
    
    cropped_img1 = crop_array(img1, cent_x, cent_y, 150)
    
    
    # Create a custom colormap: index 0 -> black, index 1 -> green.
    custom_cmap = mpl.colors.LinearSegmentedColormap.from_list('custom_green', ['black', 'green'])
    
    # Compute robust intensity limits (e.g., 2nd and 98th percentiles)
    low1, high1 = np.percentile(cropped_img1, [2, 98])

    plt.imshow(cropped_img1)
    plt.show()
    # plt.imshow(cropped_img2, cmap=custom_cmap, vmin=low2, vmax=high2)
    # plt.show()
    
    


if __name__ == '__main__':
    main()