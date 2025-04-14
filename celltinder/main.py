import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from celltinder.backend.data_loader import DataLoader
from celltinder.gui.views.cell_image_view.cell_view_manager import CellViewManager
from celltinder.gui.controllers.cell_control import CellController
from celltinder.gui.views.histogram_view.histo_view_manager import HistoViewManager
from celltinder.gui.controllers.histo_control import HistogramController


def main(csv_path: Path) -> None:
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    view = HistoViewManager()
    
    controller = HistogramController(data, view)
    controller.view.show()

    sys.exit(app.exec())


def main2(csv_path: Path, n_frames: int = 2, box_size: int = 150) -> None:
    
    
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    
    view = CellViewManager(n_frames)
    
    controller = CellController(data, view)
    controller.view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    
    # csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    main(csv_path)
