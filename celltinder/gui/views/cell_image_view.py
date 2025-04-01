from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from gui.views.base_view import BaseView


class CellImageView(BaseView):
    """View class for the cell image GUI."""
    
    def __init__(self, n_frames: int, cell_number: int, total_cells: int, cell_ratio, parent=None):
        super().__init__("Cell Image Viewer")
        self.n_frames = n_frames
        self.cell_number = cell_number
        self.total_cells = total_cells
        self.cell_ratio = cell_ratio
        self.current_frame = 1
        
        # Create a top bar with a Back button and frame title
        self.back_button = QPushButton("Back to histo gui")
        self.frame_title = QLabel(f"Frame {self.current_frame}")
        self.frame_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.create_top_bar(left_widget=self.back_button, center_widget=self.frame_title)
        
        # Create the main content area with left panel, center image area, and right panel
        content_layout = QHBoxLayout()
        
        # Left panel: cell info and ratio
        left_panel = QVBoxLayout()
        self.cell_info_label = QLabel(f"Cell {self.cell_number} / {self.total_cells}")
        self.ratio_label = QLabel(f"Ratio: {self.cell_ratio}")
        left_panel.addWidget(self.cell_info_label)
        left_panel.addWidget(self.ratio_label)
        left_panel.addStretch()
        content_layout.addLayout(left_panel)
        
        # Center panel: image display and frame slider
        center_panel = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_panel.addWidget(self.image_label)
        
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(1)
        self.frame_slider.setMaximum(self.n_frames)
        self.frame_slider.setValue(self.current_frame)
        center_panel.addWidget(self.frame_slider)
        content_layout.addLayout(center_panel)
        
        # Right panel: overlay checkbox
        right_panel = QVBoxLayout()
        self.overlay_checkbox = QCheckBox("Overlay Mask")
        right_panel.addWidget(self.overlay_checkbox)
        right_panel.addStretch()
        content_layout.addLayout(right_panel)
        
        self.main_layout.addLayout(content_layout)
        
        # Create bottom bar with navigation buttons
        self.prev_button = QPushButton("Previous cell")
        self.skip_button = QPushButton("Skip cell")
        self.keep_button = QPushButton("Keep cell")
        self.process_button = QPushButton("Process cells")
        self.create_bottom_bar([self.prev_button, self.skip_button, self.keep_button, self.process_button])
    
    def setImage(self, pixmap: QPixmap):
        self.image_label.setPixmap(pixmap)
