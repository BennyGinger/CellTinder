from __future__ import annotations
from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from scipy.ndimage import binary_dilation
import numpy as np

from celltinder.backend.data_loader import DataLoader
from celltinder.guis.utilities.shortcuts import ShortcutManager
from celltinder.guis.views.cell_view import CellView


# Constants for figure size and DPI
FIG_SIZE = (10, 10)  # inches
DPI = 100  # dots per inch

# Define the custom colormap: 
CURRENT_COLOR = 'white'
# maps low intensities to black and high to current color.
CUSTOM_CMAP = {'green': {'red': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                         'green': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                         'blue': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]},
               'red': {'red': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                       'green': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                       'blue': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]},
               'blue': {'red': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                        'green': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                        'blue': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]},
               'white': {'red': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                         'green': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                         'blue': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]}}

class CellCrush():
    """
    Controller for the Cell Crush GUI. It manages the interaction between the data and the view.
    """
    def __init__(self, data_loader: DataLoader, view: CellView) -> None:
        
        # Initialize the data loader and DataFrame.
        self._init_data_loader(data_loader, img_label, mask_label, n_frames, crop_size)          

        # Setup view and connect signals...
        self._init_view(view)

        # Load the first cell using its index from the df.
        self._load_cell()

    #----------------
    # Controller Methods
    #----------------

    def _init_data_loader(self, data_loader: DataLoader, img_label: str, mask_label: str, n_frames: int, crop_size: int) -> None:
        """
        Initialize the data loader and DataFrame. 
        """
        # Set the image and mask labels.
        self.img_label = img_label
        self.mask_label = mask_label
        self.n_frames = n_frames
        self.crop_size = crop_size
        
        # Extract the DataFrame from the data loader. Add a process column to it.
        self.data = data_loader
        self.data.add_process_col()
        self.df = self.data.pos_df
        
        # Set the initial index and frame.
        self.current_idx = 0
        self.current_frame = 1          
        
        # Setup view and connect signals...
        self.view = view
        self.view.total_cells = len(self.df)
        self.view.previousCellClicked.connect(self.on_previous_cell)
        self.view.skipCellClicked.connect(self.on_reject_cell)
        self.view.keepCellClicked.connect(self.on_keep_cell)
        self.view.nextCellClicked.connect(self.on_next_cell)
        self.view.processCellsClicked.connect(self.on_process_cells)
        self.view.frameChanged.connect(self.on_frame_changed)
        self.view.overlayToggled.connect(self.on_overlay_toggled)
        self.view.cellSliderChanged.connect(self.on_cell_slider_changed)
        self.view.cell_slider.valueChanged.connect(self.on_cell_slider_value_preview)
        
        # Create the shortcuts
        self._init_shortcuts()
        self.view.top_bar.helpClicked.connect(self._sc_manager.show_shortcuts)
        
        # Set the initial size of the view.
        self.view.adjustSize()
        
        # Load the first cell using its index from the df.
        self._load_cell()

    def _init_shortcuts(self) -> None:
        self._sc_manager = ShortcutManager(self)
    
    def _gather_info(self, idx: int | None = None) -> tuple[float, bool, int]:
        """
        Gather information about the current cell.
        """
        if idx is None:
            idx = self.current_idx
        ratio = self.df['ratio'].iat[idx]
        processed = self.df['process'].iat[idx]
        selected_count = int(self.df['process'].sum())
        before = self.df['before_stim'].iat[idx]
        after = self.df['after_stim'].iat[idx]
        return ratio, processed, selected_count, before, after

    def _refresh_info(self, *, preview: bool = False) -> None:
        """
        Refresh the information displayed in the view.
        Args:
            preview (bool): If True, updates the info without moving the slider.
        """
        ratio, processed, selected_count, before, after = self._gather_info()
        self.view.content_area.update_info(self.current_idx, self.total_cells, ratio, processed, selected_count, before, after, preview=preview)
    
    def _mark_cell(self, keep: bool) -> None:
        """
        Mark or unmark the current cell, then refresh the icon/text.
        """
        self.df.iat[self.current_idx, self.df.columns.get_loc('process')] = keep
        self._refresh_info(preview=False)

    def _load_cell(self) -> None:
        """
        Load the current cell based on the current index.
        """
        # Use the DataLoader to fetch the images and masks for the current cell.
        self.current_cell = self.data.loads_arrays(self.current_idx, self.img_label, self.mask_label, self.n_frames, self.crop_size)
        
        # Update the view with new cell info.
        self._update_view()
        
    def _update_view(self) -> None:
        """
        Update the view with the current cell information.
        """
        self._refresh_info(preview=False)
        self._update_image()

    def _update_image(self) -> None:
        """
        Update the image displayed in the view using matplotlib.
        
        The 16-bit image is displayed with a custom green colormap, and, if enabled, a gray overlay is applied from the mask.
        """
        # Get the 16-bit image and mask (if necessary) from the current cell.
        img16, mask = self._get_image_and_mask()
        
        # Create a matplotlib figure.
        # Adjust figsize/dpi as needed to get the appropriate resolution.
        fig, ax = self._create_figure(fig_size=FIG_SIZE, dpi=DPI)
        
        # Display the 16-bit cell image using the custom green colormap.
        self._display_image(ax, img16)
        
        # If overlay is enabled, add the mask as a contour.
        if mask is not None:
            self._overlay_mask(ax, mask)
        
        # Render the figure to a canvas.
        self._draw_canvas_and_set_image(fig)
    
    def _get_image_and_mask(self) -> tuple[np.ndarray, np.ndarray | None]:
        """
        Retrieves the 16-bit image and, if enabled, the mask from the current cell.
        Returns:
            img16 (np.ndarray): The 16-bit image.
            mask (np.ndarray or None): The mask if overlay is enabled, otherwise None.
        """
        img16 = self.current_cell.imgs[self.current_frame]
        mask = None
        if getattr(self, "overlay_enabled", False):
            mask = self.current_cell.masks[self.current_frame]
        return img16, mask
    
    def _create_figure(self, fig_size: tuple[int, int], dpi: int) -> tuple[Figure, Axes]:
        """
        Creates and returns a matplotlib figure and axis.
        
        Args:
            fig_size (tuple[int, int]): The size of the figure in inches.
            dpi (int): The resolution of the figure in dots per inch.
    
        Returns:
            A tuple containing the fig (Figure) and the ax (Axes) for the display.
        """
        fig = Figure(figsize=fig_size, dpi=dpi)
        ax  = fig.add_axes([0, 0, 1, 1])
        # Hide axes
        ax.axis('off')
        return fig, ax
    
    def _display_image(self, ax: Axes, img16: np.ndarray) -> None:
        """
        Displays the 16-bit image on the provided axis using a custom colormap.
        """
        # Create a custom colormap.
        cmap = LinearSegmentedColormap('GreenScale', segmentdata=CUSTOM_CMAP[CURRENT_COLOR], N=256)
        
        # Display the image
        ax.imshow(img16, cmap=cmap, interpolation='bicubic',
                  vmin=np.min(img16), vmax=np.max(img16))
    
    def _overlay_mask(self, ax: Axes, mask: np.ndarray) -> None:
        """
        Overlays the mask on the image by drawing a contour outlining the mask. Assumes that the mask is binary (background=0, foreground>=1).
        """
        # Dilate the mask to make the edges more visible. Need to reconvert it to uint8 for contouring.
        # the new mask value is set to 50 to allow contour() to have a better dynamic range.
        dilated_mask_bool = binary_dilation(mask, iterations=5)
        dilated_mask = np.where(dilated_mask_bool, 50, 0).astype(np.uint8)
        
        # For a binary mask, a threshold of 1 is appropriate to delineate edges.
        ax.contour(dilated_mask, levels=[1], colors=[(1,1,0,0.5)], linewidths=2)
    
    def _draw_canvas_and_set_image(self, fig: Figure) -> None:
        """
        Renders the given figure to a FigureCanvas, converts the result to a QPixmap, and updates the view's image.
        """
        canvas = FigureCanvas(fig)
        canvas.draw()
        width, height = canvas.get_width_height()
        # Convert the canvas buffer to a numpy array in a 8-bit format.
        img_buffer = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
        # Create a QImage from the RGBA buffer.
        qimage = QImage(img_buffer.data, width, height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        # Set the image in the view.
        self.view.setImage(pixmap)
    
    def _step_cell(self, delta: int) -> None:
        """
        Move forward or back (with wrap) and reload.
        """
        self.current_idx = (self.current_idx + delta) % len(self.df)
        self._load_cell()
    
    def _bump_frame(self) -> None:
        """
        Increments the frame slider value by 1. If it exceeds the maximum, it wraps around to the minimum.
        """
        slider = self.view.content_area.slider
        nxt = slider.value() + 1
        if nxt > slider.maximum():
            nxt = slider.minimum()
        slider.setValue(nxt)
    
    def _toggle_overlay(self) -> None:
        """
        Toggles the overlay checkbox in the view.
        """
        self.view.content_area.overlay_checkbox.toggle()
    
    # --------- Event handlers for the view signals -----------------
    def on_frame_changed(self, frame: int) -> None:
        """
        Handle the event when the frame slider is changed. Update the current frame and refresh the image.
        """
        self.current_frame = frame
        self._update_image()

    def on_overlay_toggled(self, enabled: bool) -> None:
        """
        Handle the event when the overlay checkbox is toggled. Update the overlay status and refresh the image.
        """
        self.overlay_enabled = enabled
        self._update_image()
    
    def on_previous_cell(self) -> None:
        """
        Move to the previous cell in the DataFrame. If at the start, loop back to the end.
        """
        self._step_cell(-1)

    def on_reject_cell(self) -> None:
        """
        Mark the current cell as rejected. This will set the process flag to False and refresh the view.
        """
        # Mark current cell as rejected by setting the process flag to False.
        self._mark_cell(False)

    def on_keep_cell(self) -> None:
        """
        Mark the current cell as kept. This will set the process flag to True and refresh the view.
        """
        self._mark_cell(True)

    def on_next_cell(self) -> None:
        """
        Move to the next cell in the DataFrame. If at the end, loop back to the start.
        """
        self._step_cell(+1)
    
    def on_cell_slider_changed(self, cell_number: int) -> None:
        """
        Called when the user releases the cell slider. Update the current index and load that cell.
        """
        self.current_idx = cell_number - 1
        self._load_cell()
    
    def on_cell_slider_value_preview(self, value: int) -> None:
        """
        Update the info panel and icon based on slider movement.
        (This is a preview update and should not trigger a full image reload.)
        """
        self.current_idx = value - 1
        self._refresh_info(preview=True)

    def on_process_cells(self) -> None:
        """
        Handle the event when the process cells button is clicked. This will finalize the process by updating the cell to process in the DataFrame and saving the modify CSV. It will then close the view.
        """
        # Finalize the process, for example saving the DataFrame.
        self.data.update_cell_to_process_in_df(self.df)
        self.data.save_csv()
        # Shut down the GUI.
        main_win = self.view.window()
        main_win.close()

    @property
    def total_cells(self) -> int:
        """
        Get the total number of positive cells.
        """
        return len(self.df) 


def run_cell_crush(csv_path: Path, n_frames: int = 2, crop_size: int = 151) -> None:
    """
    Run the Cell Crush GUI application.
    Args:
        csv_path (Path): Path to the CSV file containing cell data.
        n_frames (int): Number of frames to load.
        crop_size (int): Size of the cropped images.
    """
    app = QApplication(sys.argv)
    data = DataLoader(csv_path, n_frames, crop_size)
    
    view = CellView(n_frames)
    
    controller = CellCrush(data, view)
    controller.view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    run_cell_crush(csv_path)