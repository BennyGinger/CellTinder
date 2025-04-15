from pathlib import Path
import sys
from PyQt6.QtWidgets import QApplication

from celltinder.backend.data_loader import DataLoader
from celltinder.gui.controllers.cell_control import CellController
from celltinder.gui.controllers.histo_control import HistogramController
from celltinder.gui.views.celltinder_view_manager import CellTinderView


class CellTinder:
    """
    The MasterController creates the MasterView and coordinates the two subcontrollers
    (HistogramController and CellController) by injecting the appropriate subviews.
    """
    def __init__(self, data_loader: DataLoader, n_frames: int = 2):
        # Create the persistent master view.
        self.master_view = CellTinderView(n_frames)
        
        # Retrieve the individual subviews from the master view.
        self.histo_view = self.master_view.histo_view  # Histogram GUI view
        self.cell_view = self.master_view.cell_view    # Cell Image GUI view
        
        # Inject the subviews into their respective controllers.
        self.histogram_controller = HistogramController(data_loader, self.histo_view)
        self.cell_controller = CellController(data_loader, self.cell_view, n_frames=n_frames)
        
        # Connect signals for view switching.
        self.histo_view.toCellViewClicked.connect(self.switch_to_cell_view)
        self.cell_view.backClicked.connect(self.switch_to_histogram_view)
        
        # Connect the threshold-changed signal to reset cell view
        # self.histogram_controller.thresholdChanged.connect(self.handle_threshold_change)
    
    def handle_threshold_change(self) -> None:
        """
        Handle the threshold change signal from the histogram controller. This method is called when the histogram view signals that the threshold values have changed. It resets the cell controller's state to ensure it reflects the new threshold values.
        """
        # Reset the cell controller before switching views (or whenever appropriate)
        self.cell_controller.reset_state()
    
    def switch_to_cell_view(self) -> None:
        """
        Called when the histogram view signals it's time to transition to the cell view.
        """
        self.master_view.switchToCellView()
    
    def switch_to_histogram_view(self) -> None:
        """
        Called when the cell view signals it wants to go back to the histogram view.
        """
        self.master_view.switchToHistoView()
    
    def show(self) -> None:
        self.master_view.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Setup your data model (ensure DataLoader is configured properly).
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    data_loader = DataLoader(csv_path)
    
    # Initialize and show the master controller.
    master_controller = CellTinder(data_loader)
    master_controller.show()
    
    sys.exit(app.exec())
