from PyQt6.QtWidgets import (QLabel, QSlider, QCheckBox, QPushButton, QWidget,
                             QVBoxLayout, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from gui.views.base_view import BaseView


class CellImageView(BaseView):
    # Define signals to communicate user actions.
    backClicked = pyqtSignal()
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)

    def __init__(self, n_frames: int) -> None:
        super().__init__("Cell Image View")
        self.n_frames = n_frames

        # Set up the top bar, content area, and bottom bar.
        self._init_top_bar()
        self._init_content_area()
        self._init_bottom_bar()

    def _init_top_bar(self) -> None:
        """
        Create the top bar with the back button.
        """
        self.back_btn = QPushButton("Back to histo gui")
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.create_top_bar(left_widget=self.back_btn)

    def _init_content_area(self) -> None:
        """
        Create the central area. The center now will have a single column (the image panel) with the info panel as a row above the image display, and the overlay checkbox remains in a right column.
        """
        self.content_layout = QHBoxLayout()

        # Center: Image display area (will include the info panel at the top).
        self._init_image_panel()
        self.content_layout.addWidget(self.image_widget, stretch=1)

        # Right: Overlay checkbox.
        self._init_overlay_panel()
        self.content_layout.addWidget(self.overlay_widget)

        self.main_layout.addLayout(self.content_layout)

    def _init_info_panel_in_image_area(self) -> None:
        """
        Initialize the info panel to be placed above the image display. The info panel will contain the cell info and cell ratio labels and be horizontally centered.
        """
        self.info_widget = QWidget()
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.cell_info_label = QLabel("Cell ?/?")
        self.cell_ratio_label = QLabel("Ratio: ?")
        # Set the labels to be centered.
        self.cell_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cell_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Place the two labels with a stretch between so that they stay separated.
        info_layout.addStretch()
        info_layout.addWidget(self.cell_info_label)
        info_layout.addSpacing(50)
        info_layout.addWidget(self.cell_ratio_label)
        info_layout.addStretch()
        

        # Add the info panel to the image panel layout, aligned center.
        self.image_layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def _init_image_panel(self) -> None:
        """
        Initialize the central image display area.
        This panel now has a row at the top for the info panel, followed by the image display and slider area.
        """
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout(self.image_widget)

        # Info panel row: shows cell info and ratio above the image display.
        self._init_info_panel_in_image_area()

        # Image display area.
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setScaledContents(True)
        self.image_layout.addWidget(self.image_label)

        # Slider area (includes title, slider, and numbering).
        self._init_slider_area()
        self.image_layout.addLayout(self.slider_area_layout)

    def _init_slider_area(self) -> None:
        """
        Create a vertical layout for slider title, slider and frame numbers.
        """
        self.slider_area_layout = QVBoxLayout()

        # Slider title.
        self.slider_title = QLabel("Frames")
        self.slider_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_area_layout.addWidget(self.slider_title)

        # Slider widget.
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.n_frames)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.on_slider_value_changed)
        self.slider_area_layout.addWidget(self.slider)

        # Numbering below the slider.
        self.slider_numbers_layout = QHBoxLayout()
        for i in range(1, self.n_frames + 1):
            number_label = QLabel(str(i))
            number_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            # For the first label, align left; for the last label, align right; the rest center.
            if i == 1:
                number_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            elif i == self.n_frames:
                number_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.slider_numbers_layout.addWidget(number_label)
        self.slider_area_layout.addLayout(self.slider_numbers_layout)

    def _init_overlay_panel(self) -> None:
        """
        Initialize the overlay checkbox panel on the right side.
        """
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
        self.prev_cell_btn = QPushButton("Previous cell")
        self.prev_cell_btn.clicked.connect(self.previousCellClicked.emit)
        self.skip_cell_btn = QPushButton("Skip cell")
        self.skip_cell_btn.clicked.connect(self.skipCellClicked.emit)
        self.keep_cell_btn = QPushButton("Keep cell")
        self.keep_cell_btn.clicked.connect(self.keepCellClicked.emit)
        self.process_cells_btn = QPushButton("Process cells")
        self.process_cells_btn.clicked.connect(self.processCellsClicked.emit)
        buttons = [self.prev_cell_btn, self.skip_cell_btn, self.keep_cell_btn, self.process_cells_btn]
        self.create_bottom_bar(buttons, alignment=Qt.AlignmentFlag.AlignLeft)

    def set_cell_info(self, cell_number: int, total_cells: int, cell_ratio: float) -> None:
        """
        Update the cell info labels.
        """
        self.cell_info_label.setText(f"Cell {cell_number + 1}/{total_cells}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio:.2f}")

    def on_slider_value_changed(self, value: int) -> None:
        """
        Emit the frameChanged signal.
        """
        self.frameChanged.emit(value)

    def setImage(self, pixmap: QPixmap) -> None:
        """
        Update the central image display.
        """
        self.image_label.setPixmap(pixmap)
