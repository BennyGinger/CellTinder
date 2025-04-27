import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from celltinder.backend.data_loader import DataLoader
from celltinder.guis.cell_crush import CellView, CellCrush
from celltinder.guis.flame_filter import FlameView, FlameFilter


def main(csv_path: Path) -> None:
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    view = FlameView()
    
    controller = FlameFilter(data, view)
    controller.view.show()

    sys.exit(app.exec())


def main2(csv_path: Path, n_frames: int = 2, box_size: int = 150) -> None:
    
    
    app = QApplication(sys.argv)
    data = DataLoader(csv_path)
    
    view = CellView(n_frames)
    
    controller = CellCrush(data, view)
    controller.view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    
    # csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    main2(csv_path)
