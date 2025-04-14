from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


FIG_SIZE = (4, 4)

class GraphWidget(QWidget):
    """
    Widget that displays the matplotlib graph along with its navigation toolbar.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=FIG_SIZE)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Create a toolbar layout with center alignment
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

    def update_plot(self, lower_val: float, upper_val: float, ratios: list) -> None:
        """
        Update the histogram plot with new threshold values.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.hist(ratios, bins=50, color='blue', alpha=0.7)
        ax.axvline(x=lower_val, color='red', linestyle='--', label='Lower Threshold')
        ax.axvline(x=upper_val, color='green', linestyle='--', label='Upper Threshold')
        ax.set_xlabel("Ratio")
        ax.set_ylabel("Count")
        ax.set_title("Histogram of Ratio")
        ax.set_yscale('log', base=10)
        self.canvas.draw()