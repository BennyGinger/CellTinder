import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from backend.data_loader import DataLoader
from gui.views.cell_image_view import CellImageView
from gui.controllers.cell_image_control import CellImageController
from gui.views.histo_view import HistogramView
from gui.controllers.histo_control import HistogramController


def main(csv_path: Path) -> None:
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    view = HistogramView()
    
    controller = HistogramController(data, view)
    controller.view.show()

    sys.exit(app.exec())


def main2(csv_path: Path, n_frames: int = 2, box_size: int = 150) -> None:
    
    
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    pos_df = data.pos_df
    
    view = CellImageView(n_frames)
    
    controller = CellImageController(data, view)
    controller.view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    
    csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test/A1/A1_cell_data.csv")
    main2(csv_path)
