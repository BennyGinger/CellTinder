import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from celltinder.backend.load_data import LoadData
from celltinder.gui.views.histo_view import HistogramView
from celltinder.gui.controllers.histo_control import HistogramController


def main(csv_path: Path) -> None:
    app = QApplication(sys.argv)
    data = LoadData(csv_path)
    view = HistogramView()
    
    controller = HistogramController(data, view)
    view.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    main(csv_path)
