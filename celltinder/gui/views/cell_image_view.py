from PyQt6.QtWidgets import (QLabel, QSlider, QCheckBox, QPushButton, QWidget,
                             QVBoxLayout, QHBoxLayout)
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

        # --- Top Bar: Back button ---
        self.back_btn = QPushButton("Back to histo gui")
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.create_top_bar(left_widget=self.back_btn)

        # --- Central Area: Left, Center, Right Layouts ---
        self.content_layout = QHBoxLayout()

        # Left side: Display cell information.
        # Initialize with default placeholder values.
        self.info_widget = QWidget()
        self.info_layout = QVBoxLayout(self.info_widget)
        self.cell_info_label = QLabel("Cell ?/?")
        self.cell_ratio_label = QLabel("Ratio: ?")
        self.info_layout.addWidget(self.cell_info_label)
        self.info_layout.addWidget(self.cell_ratio_label)
        self.info_layout.addStretch()
        self.content_layout.addWidget(self.info_widget)

        # Center: Image display, frame title and slider.
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout(self.image_widget)
        self.frame_title_label = QLabel("Frame 1")
        self.frame_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_layout.addWidget(self.frame_title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_layout.addWidget(self.image_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(self.n_frames)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.valueChanged.connect(self.on_slider_value_changed)
        self.image_layout.addWidget(self.slider)

        self.content_layout.addWidget(self.image_widget, stretch=1)

        # Right side: Overlay checkbox.
        self.overlay_checkbox = QCheckBox("Overlay mask")
        self.overlay_checkbox.setChecked(False)
        self.overlay_checkbox.toggled.connect(self.overlayToggled.emit)
        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_layout.addStretch()
        self.overlay_layout.addWidget(self.overlay_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        self.overlay_layout.addStretch()
        self.content_layout.addWidget(self.overlay_widget)

        # Add the central content layout.
        self.main_layout.addLayout(self.content_layout)

        # --- Bottom Bar: Navigation Buttons ---
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
        """Update the cell info labels."""
        self.cell_info_label.setText(f"Cell {cell_number + 1}/{total_cells}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio}")

    def on_slider_value_changed(self, value: int) -> None:
        # Update the frame title (displaying one-indexed frame number).
        self.frame_title_label.setText(f"Frame {value}")
        # Emit the frameChanged signal (subtract one if using zero-indexing in controller).
        self.frameChanged.emit(value - 1)

    def setImage(self, pixmap: QPixmap) -> None:
        """Update the central image display."""
        self.image_label.setPixmap(pixmap)

    def setTitle(self, title: str) -> None:
        """Update the frame title label."""
        self.frame_title_label.setText(title)
