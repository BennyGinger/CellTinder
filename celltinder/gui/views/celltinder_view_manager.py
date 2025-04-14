from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from celltinder.gui.views.cell_image_view.cell_view_manager import CellViewManager
from celltinder.gui.views.histogram_view.histo_view_manager import HistoViewManager


class MasterView(QMainWindow):
    """
    Master view that holds two different GUIs and swaps between them.
    """
    def __init__(self, n_frames: int) -> None:
        super().__init__()
        self.setWindowTitle("Combined GUI")
        # Set an initial size that fits both GUIs.
        self.resize(1200, 800)

        # Create a QStackedWidget to serve as the container for both GUIs.
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instantiate the two view managers.
        self.histo_view = HistoViewManager()
        self.cell_view = CellViewManager(n_frames)

        # Instead of using the QMainWindow instances directly (which are full windows),
        # we add their central widgets to our stacked widget.
        self.stacked_widget.addWidget(self.histo_view.centralWidget())
        self.stacked_widget.addWidget(self.cell_view.centralWidget())

        # Show the histogram view first.
        self.stacked_widget.setCurrentWidget(self.histo_view.centralWidget())

        # Wire up signals between your views.
        # For example, when the histogram view emits its signal to switch to the cell view,
        # the master view will change the active widget.
        self.histo_view.toCellViewClicked.connect(self.switchToCellView)
        self.cell_view.backClicked.connect(self.switchToHistoView)

    def switchToCellView(self) -> None:
        """
        Switches the view from histogram to cell image.
        """
        # The size of the master window remains constant; only the inner widget changes.
        self.stacked_widget.setCurrentWidget(self.cell_view.centralWidget())

    def switchToHistoView(self) -> None:
        """
        Switches the view from cell image back to histogram.
        """
        self.stacked_widget.setCurrentWidget(self.histo_view.centralWidget())



