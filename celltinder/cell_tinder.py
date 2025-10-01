import sys
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

from celltinder.backend.data_loader import DataLoader
from celltinder.guis.flame_filter import FlameFilter
from celltinder.guis.views.cell_view import CellView
from celltinder.guis.cell_crush import CellCrush
from celltinder.guis.views.flame_view import FlameView


# TODO: Develop a similar GUI for view the cells after illumination with their red channel
# TODO: Add flexibility to this gui to allow users to visualize their analysises and select cells for display
# TODO: Sort out the pytests
# FIXME: Include parquet as an option for the data loader
# TODO: Create an exit button that that could trigger a graceful shutdown within gem_screening for example

class CellTinderWidget(QWidget):
    """
    Embeddable CellTinder widget for integration in other GUIs.
    Emits finished signal when the user is done.
    """
    finished = pyqtSignal()

    def __init__(self, csv_path: Path, n_frames: int, crop_size: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.n_frames = n_frames
        self._layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self._layout.addWidget(self.stack)

        # Initialize the data loader (shared between both views)
        self.data_loader = DataLoader(csv_path, n_frames, crop_size)

        # --- Histogram Page ---
        self.flame_view = FlameView()
        self.flame_filter = FlameFilter(self.data_loader, self.flame_view)
        self.stack.addWidget(self.flame_view)
        self.flame_view.next_button.clicked.connect(self.show_cell_view)

        # Keep references for dynamic creation
        self.cell_view = None
        self.cell_crush = None

        # Add Done button at the bottom
        self.done_button = QPushButton("Done")
        self.done_button.setStyleSheet("background-color: #44aa44; color: white; font-weight: bold;")
        self.done_button.clicked.connect(self._on_done)
        self._layout.addWidget(self.done_button)

    def show_cell_view_widget(self) -> None:
        self.flame_filter.on_next_pressed()
        self.cell_view = CellView(self.n_frames)
        self.cell_crush = CellCrush(self.data_loader, self.cell_view)
        self.cell_view.backClicked.connect(self.show_histogram_widget)
        self.stack.addWidget(self.cell_view)
        self.stack.setCurrentWidget(self.cell_view)

    def show_histogram_widget(self) -> None:
        self.stack.setCurrentWidget(self.flame_view)
        if self.cell_view is not None:
            idx = self.stack.indexOf(self.cell_view)
            if idx != -1:
                widget = self.stack.widget(idx)
                self.stack.removeWidget(widget)
                if widget is not None:
                    widget.deleteLater()
        self.cell_view = None
        self.cell_crush = None

    def _on_done(self):
        self.finished.emit()

    # No _decoration_delta needed for widget

    def show_cell_view(self) -> None:
        """
        Handler for the 'Next' button. Applies current thresholds, creates the cell view,
        and switches the stack to display it.
        """
        # Apply thresholds and save via histogram controller
        self.flame_filter.on_next_pressed()

        # Create and initialize cell view and controller
        self.cell_view = CellView(self.n_frames)
        self.cell_crush = CellCrush(self.data_loader, self.cell_view)

        # Connect back button to return to histogram
        self.cell_view.backClicked.connect(self.show_histogram)

        # Add and display the cell view
        self.stack.addWidget(self.cell_view)
        self.stack.setCurrentWidget(self.cell_view)

    def show_histogram(self) -> None:
        """
        Handler for the 'Back' button in the cell view. Returns to the histogram and
        cleans up the cell view so it will be reinitialized next time.
        """
        # Switch back to histogram
        self.stack.setCurrentWidget(self.flame_view)

        # Remove and delete the existing cell view
        if self.cell_view is not None:
            idx = self.stack.indexOf(self.cell_view)
            if idx != -1:
                widget = self.stack.widget(idx)
                self.stack.removeWidget(widget)
                if widget is not None:
                    widget.deleteLater()

        # Clear references
        self.cell_view = None
        self.cell_crush = None

    def _decoration_delta(self) -> int:
        """
        Returns the extra pixels of window chrome + top/bottom bars
        to add back on top of the content-area's pure height.
        """
        total_h = self.height()
        # Use the stack widget as the central content area
        central_h = self.stack.height() if self.stack is not None else 0
        return total_h - central_h

# TODO: Sort out the size of the window

class CellTinder(QMainWindow):
    """
    Main application window for standalone use.
    """
    def __init__(self, csv_path: Path, n_frames: int, crop_size: int) -> None:
        super().__init__()
        self.setWindowTitle("CellTinder")
        self.setMinimumSize(0, 0)
        self.widget = CellTinderWidget(csv_path, n_frames, crop_size)
        self.setCentralWidget(self.widget)

def run_cell_tinder(csv_path: Path, n_frames: int = 2, crop_size: int = 151) -> None:
    """
    Run the CellTinder application (standalone window).
    """
    app = QApplication(sys.argv)
    window = CellTinder(csv_path, n_frames, crop_size)
    window.show()
    app.exec()

if __name__ == "__main__":
    # Standalone usage for testing only
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    run_cell_tinder(csv_path)
