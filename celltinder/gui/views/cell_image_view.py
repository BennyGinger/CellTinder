from PyQt6.QtWidgets import (QLabel, QSlider, QCheckBox, QPushButton, QWidget,
                             QVBoxLayout, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from gui.views.base_view import BaseView

# TODO: Add the state of the current cell: Rejected or kept.
# TODO: Move the "select cell" title above the cell info panel.
# TODO: Merge the 2 GUI and connect the 'Back to histo gui' button and complete the logic of the "Process cells" button.
class CellImageView(BaseView):
    # Define signals for user actions.
    backClicked = pyqtSignal()
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)
    # New signal: Emitted when cell selection is finalized (slider released)
    cellSliderChanged = pyqtSignal(int)

    def __init__(self, n_frames: int) -> None:
        super().__init__("Cell Image View")
        self.n_frames = n_frames
        
        # Set a default value just for the initialization. This will be updated by the controller.
        self.total_cells = 100

        # Set up the top bar, content area, and bottom bar.
        self._init_top_bar()
        self._init_content_area()
        self._init_bottom_bar()

    def _init_top_bar(self) -> None:
        """Create the top bar with the back button."""
        self.back_btn = QPushButton("Back to histo gui")
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.create_top_bar(left_widget=self.back_btn)

    def _init_content_area(self) -> None:
        """
        Create the central area.
        The center now contains a single column (the image panel) that starts with the info panel row,
        followed by the new cell selection slider, then the image display and finally the frame slider.
        The overlay checkbox remains in a right column.
        """
        self.content_layout = QHBoxLayout()

        # Center: Image display area (which will include our info panel and new cell slider)
        self._init_image_panel()
        self.content_layout.addWidget(self.image_widget, stretch=1)

        # Right: Overlay checkbox.
        self._init_overlay_panel()
        self.content_layout.addWidget(self.overlay_widget)

        self.main_layout.addLayout(self.content_layout)

    def _init_info_panel_in_image_area(self) -> None:
        """
        Initialize the info panel to be placed at the top of the image panel.
        This panel displays the cell number and ratio.
        """
        self.info_widget = QWidget()
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.cell_info_label = QLabel("Cell ?/?")
        self.cell_ratio_label = QLabel("Ratio: ?")
        # Center both labels.
        self.cell_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cell_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add a fixed spacing between the two labels.
        info_layout.addStretch()
        info_layout.addWidget(self.cell_info_label)
        info_layout.addSpacing(50)
        info_layout.addWidget(self.cell_ratio_label)
        info_layout.addStretch()

        self.image_layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def _init_cell_slider(self, with_title: bool = True) -> None:
        """
        Initialize a new slider for cell selection. If with_title is True, a label "Select Cell" is added. Otherwise, only the slider is added.
        """
        self.cell_slider_area = QVBoxLayout()
        
        if with_title:
            self.cell_slider_title = QLabel("Select Cell")
            self.cell_slider_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cell_slider_area.addWidget(self.cell_slider_title)
        
        self.cell_slider = QSlider(Qt.Orientation.Horizontal)
        self.cell_slider.setMinimum(1)
        # The maximum is the total number of cells; update dynamically as needed.
        self.cell_slider.setMaximum(self.total_cells)
        self.cell_slider.setValue(1)
        
        # Connect signals.
        self.cell_slider.valueChanged.connect(self._on_cell_slider_value_changed)
        self.cell_slider.sliderReleased.connect(self._on_cell_slider_released)
        self.cell_slider_area.addWidget(self.cell_slider)
        
        self.image_layout.addLayout(self.cell_slider_area)

    def _init_image_panel(self) -> None:
        """
        Initialize the central image display area.
        1. A new title ("Select Cell")
        2. Info panel (cell info and ratio)
        3. Cell selection slider (without a title)
        4. Image display
        5. Frame slider
        """
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout(self.image_widget)
        
        # New: Add the "Select Cell" title at the top.
        self.title_label = QLabel("Select Cell")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_layout.addWidget(self.title_label)
        
        # Info panel row.
        self._init_info_panel_in_image_area()
        
        # Cell slider: modified so it does not add its own title.
        self._init_cell_slider(with_title=False)

        # Image display area.
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setScaledContents(True)
        self.image_layout.addWidget(self.image_label)
        
        # Frame slider area.
        self._init_frame_slider_area()
        self.image_layout.addLayout(self.slider_area_layout)

    def _init_frame_slider_area(self) -> None:
        """
        Create a vertical layout for the frame slider area.
        (This slider is for selecting the frame within the current cell.)
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
        self.slider.valueChanged.connect(self.on_frame_slider_value_changed)
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

    def _init_overlay_panel(self) -> None:
        """Initialize the overlay checkbox panel on the right side."""
        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_layout.addStretch()
        self.overlay_checkbox = QCheckBox("Overlay mask")
        self.overlay_checkbox.setChecked(False)
        self.overlay_checkbox.toggled.connect(self.overlayToggled.emit)
        self.overlay_layout.addWidget(self.overlay_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        self.overlay_layout.addStretch()

    def _init_bottom_bar(self) -> None:
        """
        Create the bottom bar with navigation buttons.
        """
        # Create the bottom bar using a horizontal layout.
        bottom_layout = QHBoxLayout()
        
        # List of buttons with signals connected.
        self.prev_cell_btn = QPushButton("Previous cell")
        self.prev_cell_btn.clicked.connect(self.previousCellClicked.emit)
        self.skip_cell_btn = QPushButton("Reject cell")
        self.skip_cell_btn.clicked.connect(self.skipCellClicked.emit)
        self.keep_cell_btn = QPushButton("Keep cell")
        self.keep_cell_btn.clicked.connect(self.keepCellClicked.emit)
        self.process_cells_btn = QPushButton("Process cells")
        self.process_cells_btn.clicked.connect(self.processCellsClicked.emit)
        
        buttons = [self.prev_cell_btn, self.skip_cell_btn, self.keep_cell_btn, self.process_cells_btn]
        
        # Set each button's size policy so that they expand evenly.
        for btn in buttons:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Add a stretch before the first button.
        bottom_layout.addStretch()
        # Add each button with a stretch between them.
        for btn in buttons:
            bottom_layout.addWidget(btn)
            bottom_layout.addStretch()
        
        # Now add the bottom_layout to the main layout.
        self.main_layout.addLayout(bottom_layout)

    def set_cell_info(self, cell_number: int, total_cells: int, cell_ratio: float) -> None:
        """
        Update the info panel labels. This method is also used to update the cell number as it changes from the cell slider.
        """
        self.total_cells = total_cells
        self.cell_info_label.setText(f"Cell {cell_number + 1}/{total_cells}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio:.2f}")
        
        # Set the slider to the maximum number of cells and the current cell number.
        self.cell_slider.setMaximum(total_cells)
        self.cell_slider.setValue(cell_number + 1)

    def _on_cell_slider_value_changed(self, value: int) -> None:
        """
        Slot called whenever the cell slider's value changes.
        Update the info panel with the currently selected cell number.
        (Note: The actual image load will be triggered when the slider is released.)
        """
        # Use the new slider value to update the cell info display.
        # If the controller knows the updated ratio for that cell, it can be updated later.
        self.cell_info_label.setText(f"Cell {value}/{self.total_cells}")
        # Optionally, you could update cell_ratio_label here if you can compute the ratio in the view.

    def _on_cell_slider_released(self) -> None:
        """
        Slot called when the user releases the cell slider.
        Emit a signal so the controller can load the selected cell.
        """
        self.cellSliderChanged.emit(self.cell_slider.value())

    def on_frame_slider_value_changed(self, value: int) -> None:
        """Emit the frameChanged signal (for frame within cell)."""
        self.frameChanged.emit(value)

    def setImage(self, pixmap: QPixmap) -> None:
        """Update the central image display."""
        self.image_label.setPixmap(pixmap)
