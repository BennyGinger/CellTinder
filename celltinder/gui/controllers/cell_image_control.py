from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LinearSegmentedColormap
from PyQt6.QtGui import QPixmap, QImage
import numpy as np
from scipy.ndimage import binary_dilation

from celltinder.backend.data_loader import DataLoader
from celltinder.gui.views.cell_view_manager import CellImageView

# Constants for figure size and DPI
FIG_SIZE = (5, 5)  # inches
DPI = 100  # dots per inch

# Define the custom colormap: 
CURRENT_COLOR = 'green'
# maps low intensities to black and high to current color.
CUSTOM_CMAP = {'green': {'red': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                         'green': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                         'blue': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]},
               'red': {'red': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                       'green': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                       'blue': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]},
               'blue': {'red': [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                        'green': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
                        'blue': [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]}}

class CellImageController:
    def __init__(self, data_loader: DataLoader, view: CellImageView) -> None:
        
        self.data = data_loader
        self.data.add_process_col()
        self.df = self.data.pos_df
        # Starting index for the positive cells
        self.current_idx = 0
        self.current_frame = 1          

        # Setup view and connect signals...
        self.view = view
        self.view.total_cells = len(self.df)
        self.view.previousCellClicked.connect(self.on_previous_cell)
        self.view.skipCellClicked.connect(self.on_reject_cell)
        self.view.keepCellClicked.connect(self.on_keep_cell)
        self.view.processCellsClicked.connect(self.on_process_cells)
        self.view.frameChanged.connect(self.on_frame_changed)
        self.view.overlayToggled.connect(self.on_overlay_toggled)
        self.view.cellSliderChanged.connect(self.on_cell_slider_changed)
        self.view.cell_slider.valueChanged.connect(self.on_cell_slider_value_preview)

        # Set the initial size of the view.
        self.view.adjustSize()

        # Load the first cell using its index from the df.
        self._load_cell()

    def _load_cell(self) -> None:
        """
        Load the current cell based on the current index.
        """
        # Use the DataLoader to fetch the images and masks for the current cell.
        cell_image_set = self.data.loads_arrays(self.current_idx)
        # Update the view with new cell info.
        self.current_cell = cell_image_set
        self._update_view()
        
    def _update_view(self) -> None:
        """
        Update the view with the current cell information.
        """
        cell_ratio = self.df['ratio'].iloc[self.current_idx]
        # Read the cell's state from the DataFrame (True if kept, False if rejected).
        processed = self.df['process'].iloc[self.current_idx]
        # Compute the total number of kept cells (assuming the DataFrame column 'process' holds booleans).
        selected_count = int(self.df['process'].sum())
        self.view.set_cell_info(self.current_idx, self.total_cells, cell_ratio, processed, selected_count)
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
        canvas = FigureCanvas(fig)
        canvas.draw()
        width, height = canvas.get_width_height()
        # Retrieve the RGBA buffer from the canvas.
        img_buffer = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
        
        # Create a QImage from the RGBA buffer.
        qimage = QImage(img_buffer.data, width, height, QImage.Format.Format_RGBA8888)
        # Convert QImage to QPixmap
        pixmap = QPixmap.fromImage(qimage)
        self.view.setImage(pixmap)
    
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
        ax = fig.add_subplot(111)
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
        ax.contour(dilated_mask, levels=[1], colors='gray', linewidths=2)
    
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
        Handle the event when the previous cell button is clicked. If the current index is greater than 0, decrement the index and load the previous cell.
        """
        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_cell()

    def on_reject_cell(self) -> None:
        """
        Handle the event when the skip cell button is clicked. Mark the current cell as rejected and move to the next cell."""
        # Mark current cell as rejected by setting the process flag to False.
        self.df.iloc[self.current_idx, self.df.columns.get_loc('process')] = False
        self._move_to_next_cell()

    def on_keep_cell(self) -> None:
        """
        Handle the event when the keep cell button is clicked. Mark the current cell for processing. Then move to the next cell.
        """
        # Mark current cell for processing.
        self.df.iloc[self.current_idx, self.df.columns.get_loc('process')] = True
        self._move_to_next_cell()

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
        index = value - 1  # Convert the slider value to 0-indexed.
        # Retrieve the preview data from your DataFrame.
        ratio = self.df['ratio'].iloc[index]
        processed = self.df['process'].iloc[index]
        selected_count = int(self.df['process'].sum())
        # Update the info panel (and overlay indicator) without loading a new image.
        self.view.update_info_preview(index, self.total_cells, ratio, processed, selected_count)

    def _move_to_next_cell(self) -> None:
        """
        Move to the next cell in the DataFrame. If at the end, loop back to the start.
        """
        if self.current_idx < len(self.df) - 1:
            self.current_idx += 1
        else:
            self.current_idx = 0
        self._load_cell()

    def on_process_cells(self) -> None:
        """
        Handle the event when the process cells button is clicked. This will finalize the process by updating the cell to process in the DataFrame and saving the modify CSV. It will then close the view.
        """
        # Finalize the process, for example saving the DataFrame.
        self.data.update_cell_to_process_in_df(self.df)
        self.data.save_csv()
        self.view.close()

    @property
    def total_cells(self) -> int:
        """
        Get the total number of positive cells.
        """
        return len(self.df)