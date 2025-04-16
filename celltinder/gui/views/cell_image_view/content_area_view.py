from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QCheckBox, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


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
        
        # --- Overlay Checkbox ---
        self._init_overlay_checkbox()
        
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
        self.image_label.setScaledContents(True)
        grid_layout.addWidget(self.image_label, 0, 0)
        
        self.state_indicator_label = QLabel()
        self.state_indicator_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.state_indicator_label.setStyleSheet("background: rgba(0,0,0,0); font-size: 24px; color: red;")
        self.state_indicator_label.setText("✗")
        grid_layout.addWidget(self.state_indicator_label, 0, 0, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        self.layout.addWidget(self.image_container)

    def _init_overlay_checkbox(self) -> None:
        """
        Creates a checkbox for overlaying the mask on the image.
        """
        self.overlay_checkbox = QCheckBox("Overlay mask")
        self.overlay_checkbox.setChecked(False)
        self.overlay_checkbox.toggled.connect(lambda checked: self.overlayToggled.emit(checked))
        self.layout.addWidget(self.overlay_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
    
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
            self.state_indicator_label.setStyleSheet("background: rgba(0,0,0,0); font-size: 24px; color: green;")
        else:
            self.state_indicator_label.setText("✗")
            self.state_indicator_label.setStyleSheet("background: rgba(0,0,0,0); font-size: 24px; color: red;")

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
            self.state_indicator_label.setStyleSheet("background: rgba(0,0,0,0); font-size: 24px; color: green;")
        else:
            self.state_indicator_label.setText("✗")
            self.state_indicator_label.setStyleSheet("background: rgba(0,0,0,0); font-size: 24px; color: red;")

    def setImage(self, pixmap: QPixmap) -> None:
        """
        Sets the image in the display area. The image is scaled to fit the label.
        Args:
            pixmap: The QPixmap to display.
        """
        self.image_label.setPixmap(pixmap)

