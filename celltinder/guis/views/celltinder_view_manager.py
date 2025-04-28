from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from celltinder.gui.views.cell_main_view import CellViewWidget
from celltinder.gui.views.histo_main_view import HistoViewWidget


class CellTinderView(QMainWindow):
    """
    Master view that holds two different GUIs and swaps between them.
    """
    def __init__(self, n_frames: int) -> None:
        super().__init__()
        self.setWindowTitle("Combined GUI")
        # Set an initial size that fits both GUIs.
        self.resize(600, 600)

        # Create a QStackedWidget to serve as the container for both GUIs.
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate the two view managers.
        self.histo_view = HistoViewWidget()
        self.cell_view = CellViewWidget(n_frames)

        # Add the widget instances directly.
        self.stacked_widget.addWidget(self.histo_view)
        self.stacked_widget.addWidget(self.cell_view)
        # Show the histogram view first.
        self.stacked_widget.setCurrentWidget(self.histo_view)

        # Wire up signals between your views.
        self.histo_view.toCellViewClicked.connect(self.switchToCellView)
        self.cell_view.backClicked.connect(self.switchToHistoView)

    def switchToCellView(self) -> None:
        """
        Switches the view from histogram to cell image.
        """
        # The size of the master window remains constant; only the inner widget changes.
        self.stacked_widget.setCurrentWidget(self.cell_view)

    def switchToHistoView(self) -> None:
        """
        Switches the view from cell image back to histogram.
        """
        self.stacked_widget.setCurrentWidget(self.histo_view)



