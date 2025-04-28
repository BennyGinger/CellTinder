from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSlider, QHBoxLayout, QPushButton, QLabel, QCheckBox, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QResizeEvent

from celltinder.guis.utilities.widgets_utilities import BaseToolBar


class CellView(QMainWindow):
    """
    Main view for the Cell Crush application, containing the top bar, content area, and bottom bar. Propagates signals
    from subwidgets to the main view.
    """
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
        self.setWindowTitle("Cell Crush")

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


class TopBar(BaseToolBar):
    """
    Top bar with a back button and a help button.
    """
    backClicked = pyqtSignal()
    helpClicked = pyqtSignal()

    def __init__(self, parent: QWidget=None) -> None:
        super().__init__([("To Flame Filter", "back")], parent)
        
        # remove the first stretch so the button hugs the left edge
        self._box.takeAt(0)
        self._box.addStretch()
        
        self.back.clicked.disconnect()
        self.back.clicked.connect(self.backClicked.emit)
        
        help_btn = QPushButton(self)
        help_btn.setIcon(QIcon.fromTheme("help-about"))    # or a local “?” pixmap
        help_btn.setToolTip("Show keyboard shortcuts")
        help_btn.setFlat(True)
        help_btn.clicked.connect(self.helpClicked.emit)
        self._box.addStretch()      # push it to the far right
        self._box.addWidget(help_btn)


class BottomBar(BaseToolBar):
    """
    Bottom bar with buttons for cell navigation and processing.
    """
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    nextCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()

    def __init__(self, parent: QWidget=None) -> None:
        super().__init__([
            ("Previous", "previousCell"),
            ("Reject",   "skipCell"),
            ("Keep",     "keepCell"),
            ("Next",     "nextCell"),
            ("Process",  "processCells")
        ], parent)


class ContentAreaWidget(QWidget):
    """
    Content area of the Cell Crush View, containing the cell image, sliders, and info panel.
    """
    cellSliderChanged = pyqtSignal(int)
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)
    
    INDICATOR_STYLE = ("background:rgba(0,0,0,0);font-size:48px;color:{color};")

    def __init__(self, n_frames: int, parent: QWidget=None) -> None:
        super().__init__(parent)
        # set the size policy to allow for dynamic resizing
        sp = self.sizePolicy()
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.setMinimumSize(0, 0)
        
        self.n_frames = n_frames
        self.total_cells = 100  # Default; will be updated by the controller.
        self.layout = QVBoxLayout(self)
        
        # --- Title ---
        self.title_label = QLabel("Find your cell crush!")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # --- Info Panel ---
        self._init_info_panel()
        
        # --- Cell Slider ---
        self._init_cell_slider()
        
        # --- Image Display Area ---
        self._init_image_display()
        # ensure the label expands, but doesn’t itself stretch the pixmap:
        self.image_label.setScaledContents(False)
        self._raw_pixmap: QPixmap | None = None
        
        # --- Frame Slider Area ---
        self._init_frame_slider_area()

    def _make_slider(self, maximum: int, *, ticks: bool=False) -> QSlider:
        """
        Creates a horizontal slider with the specified maximum value.
        Args:
            maximum (int): The maximum value for the slider.
        Returns:
            QSlider: The created slider.
        """
        s = QSlider(Qt.Orientation.Horizontal)
        s.setMinimum(1)
        s.setMaximum(maximum)
        s.setValue(1)
        if ticks:
            s.setTickPosition(QSlider.TickPosition.TicksBelow)
            s.setTickInterval(1)
        return s
    
    def _init_info_panel(self) -> None:
        """
        Builds the info panel to show cell number, ratio, and a selected cells counter.
        """
        self.info_widget = QWidget()
        info_layout = QHBoxLayout(self.info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a label for the cell info.
        self.cell_info_label = QLabel("Cell ?/?")
        self.cell_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create labels for before and after cell info.
        self.before_label = QLabel("Before: ?")
        self.before_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.after_label  = QLabel("After:  ?")
        self.after_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a label for the cell ratio.
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
        info_layout.addWidget(self.before_label)
        info_layout.addSpacing(50)
        info_layout.addWidget(self.after_label)
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
        self.cell_slider = self._make_slider(self.total_cells, ticks=False)
        self.cell_slider.valueChanged.connect(self._on_cell_slider_value_changed)
        # Emit a signal when the slider is released.
        self.cell_slider.sliderReleased.connect(lambda: self.cellSliderChanged.emit(self.cell_slider.value()))
        self.cell_slider_area.addWidget(self.cell_slider)
        self.layout.addLayout(self.cell_slider_area)

    def _init_image_display(self) -> None:
        """
        Sets up the image display area: just a single QLabel that expands,
        plus two overlay widgets parented to that QLabel.
        """
        # — the image label itself —
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setScaledContents(False)   # we manually scale in _update_scaled_pixmap
        self.layout.addWidget(self.image_label)
        self.image_label.setMinimumSize(0, 0)

        # — the state indicator, as a child of the label —
        self.state_indicator_label = QLabel("✗", parent=self.image_label)
        self.state_indicator_label.setStyleSheet(self.INDICATOR_STYLE.format(color="red"))
        self.state_indicator_label.show()

        # — the overlay checkbox, also as a child of the label —
        self._init_overlay_checkbox()  # this creates self.overlay_checkbox
        self.overlay_checkbox.setParent(self.image_label)
        self.overlay_checkbox.show()

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
        
        self.slider = self._make_slider(self.n_frames, ticks=True)
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

    def update_info(self, cell_number: int, total_cells: int, cell_ratio: float, processed: bool, selected_count: int, before: float, after: float, *, preview: bool = False) -> None:
        """
        Updates the cell info displayed in the content area.
        Args:
            cell_number: Current cell number.
            total_cells: Total number of cells.
            cell_ratio: Ratio of the current cell.
            processed: Indicates if the cell has been processed.
            selected_count: Number of selected cells.
            before: Ratio before stimulation.
            after: Ratio after stimulation.
            preview: If True, updates only the info panel without moving the slider.
        """
        self.total_cells = total_cells
        self.cell_info_label.setText(f"Cell {cell_number+1}/{total_cells}")
        self.before_label.setText(f"Before: {before:.2f}")
        self.after_label .setText(f"After:  {after:.2f}")
        self.cell_ratio_label.setText(f"Ratio: {cell_ratio:.2f}")
        self.selected_cells_value_label.setText(str(selected_count))

        self.state_indicator_label.setText("✓" if processed else "✗")
        color = "yellow" if processed else "red"
        self.state_indicator_label.setStyleSheet(self.INDICATOR_STYLE.format(color=color))

        if not preview:
            # only move the slider on “real” updates
            self.cell_slider.blockSignals(True)
            self.cell_slider.setMaximum(total_cells)
            self.cell_slider.setValue(cell_number+1)
            self.cell_slider.blockSignals(False)

    def setImage(self, pixmap: QPixmap) -> None:
        """
        Called by the controller with the full-resolution pixmap.
        """
        self._raw_pixmap = pixmap
        self._update_scaled_pixmap()
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Whenever our widget (and thus the label) resizes, rescale the pixmap.
        """
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        """
        Scale the stored raw pixmap to fit the label, keeping aspect ratio. Also position the state indicator and checkbox.
        """
        if not self._raw_pixmap:
            return

        lbl_size = self.image_label.size()
        scaled = self._raw_pixmap.scaled(lbl_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self._aspect_ratio = scaled.width() / scaled.height()
        
        # --- now compute where the pixmap actually sits inside the label ---
        lbl_w = self.image_label.width()
        lbl_h = self.image_label.height()
        pix_w = scaled.width()
        pix_h = scaled.height()
        x0 = (lbl_w - pix_w) / 2
        y0 = (lbl_h - pix_h) / 2
        margin = 10  # pixels from the edge of the pixmap

        # --- move the state indicator to top-right of the pixmap ---
        si = self.state_indicator_label
        si.adjustSize()
        w_si, h_si = si.width(), si.height()
        si.move(int(x0 + pix_w - w_si - margin), int(y0 + margin))
        si.raise_()

        # --- move the checkbox to bottom-center of the pixmap ---
        cb = self.overlay_checkbox
        cb.adjustSize()
        w_cb, h_cb = cb.width(), cb.height()
        cb_x = x0 + (pix_w - w_cb) / 2
        cb_y = y0 + pix_h - h_cb - margin
        cb.move(int(cb_x), int(cb_y))
        cb.raise_()

    def heightForWidth(self, w: int) -> int:
        """
        Returns the height for a given width, maintaining the aspect ratio.
        This is used to ensure that the image label maintains its aspect ratio when resized.
        """
        # Qt will ask you “if I have width=w, what height should I be?”
        ar = getattr(self, "_aspect_ratio", None)
        if ar is not None and ar > 0:
            return int(w / ar)
        # fallback to default
        return super().heightForWidth(w)
    
    def minimumSizeHint(self) -> QSize:
        """
        Allows the widget to be resized to a minimum size.
        """
        return QSize(0, 0)


