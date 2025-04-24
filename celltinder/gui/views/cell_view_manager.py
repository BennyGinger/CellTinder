from typing import Iterable
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSlider, QHBoxLayout, QPushButton, QLabel, QCheckBox, QSizePolicy, QGridLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtGui import QShortcut, QKeySequence
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from scipy.ndimage import binary_dilation
import numpy as np

from celltinder.backend.data_loader import DataLoader


class BaseToolBar(QWidget):
    """HBox toolbar whose buttons & signals are declared in a list."""
    def __init__(self, buttons: Iterable[tuple[str, str]], parent=None):
        """
        buttons: iterable of (text, attr_name)  
        An attr named *attr_name* is created to host the button **and** a
        pyqtSignal with the same name + "Clicked".
        """
        super().__init__(parent)
        self._box = QHBoxLayout(self)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.addStretch()

        for text, name in buttons:
            self._add_button(text, name)

    def __getattr__(self, item) -> pyqtSignal:
        """
        Create a signal when the attribute is accessed for the first time.
        """
        if item.endswith("Clicked"):
            self.__dict__[item] = pyqtSignal()
            return self.__dict__[item]
        raise AttributeError(item)

    def _add_button(self, text: str, name: str) -> None:
        """
        Create a button with the given text and name, and connect it to the signal.
        """
        btn = QPushButton(text, self)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sig = getattr(self, f"{name}Clicked")
        btn.clicked.connect(sig.emit)
        setattr(self, name, btn)
        self._box.addWidget(btn)
        self._box.addStretch()


class TopBar(BaseToolBar):
    backClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__([("Back to histo gui", "back")], parent)
        
        # remove the first stretch so the button hugs the left edge
        self._box.takeAt(0)
        self._box.addStretch()
        
        self.back.clicked.disconnect()          # disconnect generic emit
        self.back.clicked.connect(self.backClicked.emit)


class BottomBar(BaseToolBar):
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    nextCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__([
            ("Previous", "previousCell"),
            ("Reject",   "skipCell"),
            ("Keep",     "keepCell"),
            ("Next",     "nextCell"),
            ("Process",  "processCells")
        ], parent)

INDICATOR_STYLE = ("background:rgba(0,0,0,0);font-size:48px;color:{color};")
class ContentAreaWidget(QWidget):
    """
    Content area of the Cell Image View, containing the cell image, sliders, and info panel.
    """
    cellSliderChanged = pyqtSignal(int)
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)
    
    def __init__(self, n_frames: int, parent=None):
        super().__init__(parent)
        self.n_frames = n_frames
        self.total_cells = 100  # Default; will be updated by the controller.
        self.layout = QVBoxLayout(self)
        
        # --- Title ---
        self.title_label = QLabel("Select Cell")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # --- Info Panel ---
        self._init_info_panel()
        
        # --- Cell Slider ---
        self._init_cell_slider()
        
        # --- Image Display Area ---
        self._init_image_display()
        
        # --- Frame Slider Area ---
        self._init_frame_slider_area()

    def _init_info_panel(self) -> None:
        """
        Builds the info panel to show cell number, ratio, and a selected cells counter.
        """
        self.info_widget = QWidget()
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cell_info_label = QLabel("Cell ?/?")
        self.cell_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.cell_ratio_label = QLabel("Ratio: ?")
        self.cell_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Selected cells counter: dynamic value and static title.
        self.selected_cells_value_label = QLabel("0")
        self.selected_cells_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.selected_cells_title_label = QLabel(" cells selected")
        self.selected_cells_title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        selected_layout = QHBoxLayout()
        selected_layout.addWidget(self.selected_cells_value_label)
        selected_layout.addWidget(self.selected_cells_title_label)
        
        info_layout.addStretch()
        info_layout.addWidget(self.cell_info_label)
        info_layout.addSpacing(50)
        info_layout.addWidget(self.cell_ratio_label)
        info_layout.addSpacing(50)
        info_layout.addLayout(selected_layout)
        info_layout.addStretch()
        
        self.layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def _init_cell_slider(self) -> None:
        """
        Creates a horizontal slider for selecting cells.
        """
        self.cell_slider_area = QVBoxLayout()
        self.cell_slider = QSlider(Qt.Orientation.Horizontal)
        self.cell_slider.setMinimum(1)
        self.cell_slider.setMaximum(self.total_cells)
        self.cell_slider.setValue(1)
        self.cell_slider.valueChanged.connect(self._on_cell_slider_value_changed)
        # Emit a signal when the slider is released.
        self.cell_slider.sliderReleased.connect(lambda: self.cellSliderChanged.emit(self.cell_slider.value()))
        self.cell_slider_area.addWidget(self.cell_slider)
        self.layout.addLayout(self.cell_slider_area)

    # TODO: Remove both slider from the ContentArea
    def _init_image_display(self) -> None:
        """
        Sets up the image display area including an overlay indicator. The image and state indicator are placed in a grid layout to allow overlap.
        """
        self.image_container = QWidget()
        self.image_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid_layout = QGridLayout(self.image_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        grid_layout.addWidget(self.image_label, 0, 0)
        
        self.state_indicator_label = QLabel("✗")
        self.state_indicator_label.setStyleSheet(INDICATOR_STYLE.format(color="red"))
        self.state_indicator_label.setContentsMargins(0, 10, 20, 0)
        grid_layout.addWidget(self.state_indicator_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        # Add the overlay checkbox to the grid layout.
        self._init_overlay_checkbox()
        grid_layout.addWidget(self.overlay_checkbox, 0, 0, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        
        self.layout.addWidget(self.image_container)

    def _init_overlay_checkbox(self) -> None:
        """
        Creates a checkbox for overlaying the mask on the image.
        """
        self.overlay_checkbox = QCheckBox("Overlay mask")
        self.overlay_checkbox.setChecked(False)
        self.overlay_checkbox.toggled.connect(lambda checked: self.overlayToggled.emit(checked))
        self.overlay_checkbox.setStyleSheet("""
                    QCheckBox::indicator {
                        width: 15px;
                        height: 15px;
                        border-radius: 4px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 2px solid white;
                        background: transparent;
                    }
                    QCheckBox::indicator:checked {
                        border: 2px solid white;
                        background: rgba(255, 255, 0, 0.5);
                    }
                    QCheckBox {
                        color: white;
                        background: transparent;
                        spacing: 6px;
                        margin-bottom: 20px;
                    }""")
        
    def _init_frame_slider_area(self) -> None:
        """
        Creates the frame slider area with its title and numbered labels.
        """
        self.slider_area_layout = QVBoxLayout()
        self.slider_title = QLabel("Frames")
        self.slider_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_area_layout.addWidget(self.slider_title)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.n_frames)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(lambda val: self.frameChanged.emit(val))
        self.slider_area_layout.addWidget(self.slider)
        
        self.slider_numbers_layout = QHBoxLayout()
        for i in range(1, self.n_frames + 1):
            number_label = QLabel(str(i))
            number_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            if i == 1:
                number_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            elif i == self.n_frames:
                number_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.slider_numbers_layout.addWidget(number_label)
        self.slider_area_layout.addLayout(self.slider_numbers_layout)
        self.layout.addLayout(self.slider_area_layout)

    def _on_cell_slider_value_changed(self, value: int) -> None:
        """
        Updates the cell info label when the slider value changes.
        """
        self.cell_info_label.setText(f"Cell {value}/{self.total_cells}")

    def set_cell_info(self, cell_number: int, total_cells: int, cell_ratio: float, processed: bool, selected_count: int) -> None:
        """
        Updates the cell info panel with the current cell number, total cells, ratio, and processed state.
        Args:
            cell_number: Current cell number.
            total_cells: Total number of cells.
            cell_ratio: Ratio of the current cell.
            processed: Indicates if the cell has been processed.
            selected_count: Number of selected cells.
        """
        self.total_cells = total_cells
        self.cell_info_label.setText(f"Cell {cell_number+1}/{total_cells}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio:.2f}")
        self.cell_slider.setMaximum(total_cells)
        self.cell_slider.setValue(cell_number+1)
        self.selected_cells_value_label.setText(str(selected_count))
        if processed:
            self.state_indicator_label.setText("✓")
            self.state_indicator_label.setStyleSheet(INDICATOR_STYLE.format(color="yellow"))
        else:
            self.state_indicator_label.setText("✗")
            self.state_indicator_label.setStyleSheet(INDICATOR_STYLE.format(color="red"))

    def update_info_preview(self, cell_number: int, total_cells: int, cell_ratio: float, processed: bool, selected_count: int) -> None:
        """
        Updates the info panel with a preview of the cell information. This is used to show the information without changing the slider value.
        Args:
            cell_number: Current cell number.
            total_cells: Total number of cells.
            cell_ratio: Ratio of the current cell.
            processed: Indicates if the cell has been processed.
            selected_count: Number of selected cells.
        """
        self.cell_info_label.setText(f"Cell {cell_number+1}/{total_cells}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio:.2f}")
        self.selected_cells_value_label.setText(str(selected_count))
        if processed:
            self.state_indicator_label.setText("✓")
            self.state_indicator_label.setStyleSheet(INDICATOR_STYLE.format(color="yellow"))
        else:
            self.state_indicator_label.setText("✗")
            self.state_indicator_label.setStyleSheet(INDICATOR_STYLE.format(color="red"))

    def setImage(self, pixmap: QPixmap) -> None:
        """
        Sets the image in the display area. The image is scaled to fit the label.
        Args:
            pixmap: The QPixmap to display.
        """
        self.image_label.setPixmap(pixmap)

class CellImageView(QMainWindow):
    # Define signals to propagate actions from the subwidgets.
    backClicked = pyqtSignal()
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    nextCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)
    cellSliderChanged = pyqtSignal(int)
    
    def __init__(self, n_frames: int) -> None:
        super().__init__()
        self.setWindowTitle("Cell Image View")
        self.resize(1000, 1000)

        # Initialize central widget and main layout.
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Create and inject subwidgets.
        self.top_bar = TopBar()
        self.content_area = ContentAreaWidget(n_frames)
        self.bottom_bar = BottomBar()
        
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.content_area, stretch=1)
        self.main_layout.addWidget(self.bottom_bar)
        
        # Connect subwidget signals to the main view's signals.
        self.top_bar.backClicked.connect(self.backClicked.emit)
        self.bottom_bar.previousCellClicked.connect(self.previousCellClicked.emit)
        self.bottom_bar.skipCellClicked.connect(self.skipCellClicked.emit)
        self.bottom_bar.keepCellClicked.connect(self.keepCellClicked.emit)
        self.bottom_bar.nextCellClicked.connect(self.nextCellClicked.emit)
        self.bottom_bar.processCellsClicked.connect(self.processCellsClicked.emit)
        self.content_area.cellSliderChanged.connect(self.cellSliderChanged.emit)
        self.content_area.frameChanged.connect(self.frameChanged.emit)
        self.content_area.overlayToggled.connect(self.overlayToggled.emit)
        
    
    def set_cell_info(self, cell_number: int, total_cells: int, cell_ratio: float, processed: bool, selected_count: int) -> None:
        """
        Updates the cell info displayed in the content area.
        Args:
            cell_number: Current cell number.
            total_cells: Total number of cells.
            cell_ratio: Ratio of the current cell.
            processed: Indicates if the cell has been processed.
            selected_count: Number of selected cells.
        """
        self.content_area.set_cell_info(cell_number, total_cells, cell_ratio, processed, selected_count)
    
    def update_info_preview(self, cell_number: int, total_cells: int, cell_ratio: float, processed: bool, selected_count: int) -> None:
        """
        Updates the info preview displayed in the content area.
        Args:
            cell_number: Current cell number.
            total_cells: Total number of cells.
            cell_ratio: Ratio of the current cell.
            processed: Indicates if the cell has been processed.
            selected_count: Number of selected cells.
        """
        self.content_area.update_info_preview(cell_number, total_cells, cell_ratio, processed, selected_count)
    
    def setImage(self, pixmap: QPixmap) -> None:
        """
        Sets the image in the content area.
        Args:
            pixmap: The QPixmap to display.
        """
        self.content_area.setImage(pixmap)

    @property
    def cell_slider(self) -> QSlider:
        """
        Returns the cell slider for external access.
        """
        return self.content_area.cell_slider


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
        self.view.nextCellClicked.connect(self._move_to_next_cell)
        self.view.processCellsClicked.connect(self.on_process_cells)
        self.view.frameChanged.connect(self.on_frame_changed)
        self.view.overlayToggled.connect(self.on_overlay_toggled)
        self.view.cellSliderChanged.connect(self.on_cell_slider_changed)
        self.view.cell_slider.valueChanged.connect(self.on_cell_slider_value_preview)

        # Set the initial size of the view.
        self.view.adjustSize()
        
        # Create the shortcuts
        self._init_shortcuts()

        # Load the first cell using its index from the df.
        self._load_cell()

    def _init_shortcuts(self) -> None:
        self._shortcuts: list[QShortcut] = []

        def bind(key: str, slot: callable) -> None:
            """
            Create a shortcut for a key and bind it to a slot.
            """
            sc = QShortcut(QKeySequence(key), self.view)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(slot)
            self._shortcuts.append(sc)

        bind("8", self._bump_frame)
        bind("6", self._move_to_next_cell)
        bind("4", self.on_previous_cell)
        bind("s", self.on_keep_cell)
        bind("r", self.on_reject_cell)
        bind("m", self._toggle_overlay)
    
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
    
    def _refresh_state_icon(self):
        """
        Update only the indicator + counters, no image reload.
        """
        ratio          = self.df['ratio'].iloc[self.current_idx]
        processed      = self.df['process'].iloc[self.current_idx]
        selected_count = int(self.df['process'].sum())

        # False ⇒ preview-only update, so sliders are not jumped
        self.view.update_info_preview(self.current_idx, self.total_cells, ratio, processed, selected_count)
    
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
    
    def _move_to_next_cell(self) -> None:
        """
        Move to the next cell in the DataFrame. If at the end, loop back to the start.
        """
        if self.current_idx < len(self.df) - 1:
            self.current_idx += 1
        else:
            self.current_idx = 0
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
        self._refresh_state_icon()

    def on_keep_cell(self) -> None:
        """
        Handle the event when the keep cell button is clicked. Mark the current cell for processing. Then move to the next cell.
        """
        # Mark current cell for processing.
        self.df.iloc[self.current_idx, self.df.columns.get_loc('process')] = True
        self._refresh_state_icon()

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


