import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from celltinder.backend.data_loader import DataLoader
from celltinder.gui.views.histo_view import HistogramView, HistogramController
from celltinder.gui.views.cell_view_manager import CellViewManager, CellImageController

class MainApp(QMainWindow):
    """
    Main application window managing the histogram and cell image views.
    Uses a QStackedWidget to switch between the two GUIs.
    """
    def __init__(self, csv_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("CellTinder GUI")
        # Stacked widget to hold different pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize the data loader (shared between both views)
        self.data_loader = DataLoader(csv_path)

        # --- Histogram Page ---
        self.hist_view = HistogramView()
        self.hist_ctrl = HistogramController(self.data_loader, self.hist_view)
        # Add histogram view to the stack
        self.stack.addWidget(self.hist_view)
        # Connect 'Next' button to switch to cell view
        self.hist_view.next_button.clicked.connect(self.show_cell_view)

        # Keep references for dynamic creation
        self.cell_view = None
        self.cell_ctrl = None

    def show_cell_view(self) -> None:
        """
        Handler for the 'Next' button. Applies current thresholds, creates the cell view,
        and switches the stack to display it.
        """
        # Apply thresholds and save via histogram controller
        self.hist_ctrl.on_next_pressed()

        # Determine number of frames by loading the first cell
        first_cell = self.data_loader.loads_arrays(0)
        n_frames = len(first_cell.imgs)

        # Create and initialize cell view and controller
        self.cell_view = CellViewManager(n_frames)
        self.cell_ctrl = CellImageController(self.data_loader, self.cell_view)

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
        self.stack.setCurrentWidget(self.hist_view)

        # Remove and delete the existing cell view
        if self.cell_view is not None:
            idx = self.stack.indexOf(self.cell_view)
            if idx != -1:
                widget = self.stack.widget(idx)
                self.stack.removeWidget(widget)
                widget.deleteLater()

        # Clear references
        self.cell_view = None
        self.cell_ctrl = None


def main(csv_path: Path) -> None:
    app = QApplication(sys.argv)
    window = MainApp(csv_path)
    window.resize(500, 500)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    main(csv_path)
