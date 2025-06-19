import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from celltinder.backend.data_loader import DataLoader
from celltinder.guis.flame_filter import FlameFilter
from celltinder.guis.views.cell_view import CellView
from celltinder.guis.cell_crush import CellCrush
from celltinder.guis.views.flame_view import FlameView


# TODO: Develop a similar GUI for view the cells after illumination with their red channel
# TODO: Add flexibility to this gui to allow users to visualize their analysises and select cells for display
# TODO: Sort out the pytests
# FIXME: Include parquet as an option for the data loader
class CellTinder(QMainWindow):
    """
    Main application window managing the histogram and cell image views.
    Uses a QStackedWidget to switch between the two GUIs.
    """
    def __init__(self, csv_path: Path, n_frames: int, crop_size: int) -> None:
        super().__init__()
        self.setWindowTitle("CellTinder")
        
        self.n_frames = n_frames
        
        # Stacked widget to hold different pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # allow the window + stack to go down to zero if needed
        self.stack.setMinimumSize(0, 0)
        self.centralWidget().setMinimumSize(0, 0)
        self.setMinimumSize(0, 0)

        # Initialize the data loader (shared between both views)
        self.data_loader = DataLoader(csv_path, n_frames, crop_size)

        # --- Histogram Page ---
        self.flame_view = FlameView()
        self.flame_filter = FlameFilter(self.data_loader, self.flame_view)
        # Add histogram view to the stack
        self.stack.addWidget(self.flame_view)
        # Connect 'Next' button to switch to cell view
        self.flame_view.next_button.clicked.connect(self.show_cell_view)

        # Keep references for dynamic creation
        self.cell_view = None
        self.cell_crush = None

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
        central_h = self.centralWidget().height()
        return total_h - central_h

# TODO: Sort out the size of the window
def run_cell_tinder(csv_path: Path, n_frames: int = 2, crop_size: int = 151) -> None:
    """
    Run the CellTinder application.
    Args:
        csv_path: Path to the CSV file containing cell data.
        n_frames: Number of frames to load for each cell.
        crop_size: Size of the cropped images.
    """
    app = QApplication(sys.argv)
    window = CellTinder(csv_path, n_frames, crop_size)
    # window.showMaximized()
    window.show()
    app.exec()


if __name__ == "__main__":
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    run_cell_tinder(csv_path)
