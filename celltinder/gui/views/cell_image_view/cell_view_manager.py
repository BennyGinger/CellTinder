from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSlider
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPixmap

from celltinder.gui.views.cell_image_view.top_bar_view import TopBarWidget
from celltinder.gui.views.cell_image_view.bottom_bar_view import BottomBarWidget
from celltinder.gui.views.cell_image_view.content_area_view import ContentAreaWidget


class CellViewManager(QMainWindow):
    # Define signals to propagate actions from the subwidgets.
    backClicked = pyqtSignal()
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()
    frameChanged = pyqtSignal(int)
    overlayToggled = pyqtSignal(bool)
    cellSliderChanged = pyqtSignal(int)
    
    def __init__(self, n_frames: int) -> None:
        super().__init__()
        self.setWindowTitle("Cell Image View")
        self.resize(1200, 800)

        # Initialize central widget and main layout.
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
        # Create and inject subwidgets.
        self._init_ui_components(n_frames)
        
        # Connect subwidget signals to the main view's signals.
        self._connect_signals()

    def _init_ui_components(self, n_frames: int) -> None:
        """
        Initializes the UI components of the CellViewManager.
        Args:
            n_frames: Number of frames to be displayed.
        """
        self.top_bar = TopBarWidget()
        self.content_area = ContentAreaWidget(n_frames)
        self.bottom_bar = BottomBarWidget()
        
        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.content_area, stretch=1)
        self.main_layout.addWidget(self.bottom_bar)

    def _connect_signals(self) -> None:
        """
        Connect signals from subwidgets to the main view's signals.
        """
        self.top_bar.backClicked.connect(self.backClicked.emit)
        self.bottom_bar.previousCellClicked.connect(self.previousCellClicked.emit)
        self.bottom_bar.skipCellClicked.connect(self.skipCellClicked.emit)
        self.bottom_bar.keepCellClicked.connect(self.keepCellClicked.emit)
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