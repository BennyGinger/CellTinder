from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from gui.views.base_view import BaseView


class HistogramView(BaseView):
    """View class for the histogram GUI."""
    
    def __init__(self) -> None:
        """Initialize the HistogramView with a layout and controls."""
        
        super().__init__("Histogram GUI")
        
        # Set up the matplotlib figure and canvas
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)
        
        # Add the navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addStretch()
        self.main_layout.addLayout(toolbar_layout)
        
        # Create the threshold and cell count controls
        self._create_controls()
        
        # Create the Next button in the bottom bar
        self.next_button = QPushButton("Next")
        self.create_bottom_bar([self.next_button], alignment=Qt.AlignmentFlag.AlignRight)

    
    def _create_controls(self) -> None:
        """Create controls for threshold inputs and cell count display."""
        
        self.controls_layout = QHBoxLayout()
        
        # Lower Threshold Input
        self.lower_layout = QVBoxLayout()
        self.lower_label = QLabel("Lower Threshold")
        self.lower_edit = QLineEdit()
        self.lower_edit.setFixedWidth(120)
        self.lower_edit.setStyleSheet("color: red;")
        self.lower_edit.setValidator(QDoubleValidator(0.0, 1000.0, 2))
        self.lower_layout.addWidget(self.lower_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lower_layout.addWidget(self.lower_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Upper Threshold Input
        self.upper_layout = QVBoxLayout()
        self.upper_label = QLabel("Upper Threshold")
        self.upper_edit = QLineEdit()
        self.upper_edit.setFixedWidth(120)
        self.upper_edit.setStyleSheet("color: green;")
        self.upper_edit.setValidator(QDoubleValidator(0.0, 1000.0, 2))
        self.upper_layout.addWidget(self.upper_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.upper_layout.addWidget(self.upper_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Cell Count Display
        self.count_layout = QVBoxLayout()
        self.count_label = QLabel("Cell Count")
        self.count_display = QLabel("0")
        self.count_display.setFixedWidth(120)
        self.count_display.setStyleSheet("font-weight: bold;")
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_display, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Combine into the controls layout
        self.controls_layout.addLayout(self.lower_layout)
        self.controls_layout.addLayout(self.upper_layout)
        self.controls_layout.addLayout(self.count_layout)
        self.main_layout.addLayout(self.controls_layout)
    
    # Public methods for updating UI elements
    def update_count(self, count: int) -> None:
        self.count_display.setText(str(count))
    
    def update_plot(self, lower_val: float, upper_val: float, ratios: list) -> None:
        """Update the histogram plot with new threshold values."""
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
    
    def get_threshold_values(self, default_lower: float, default_upper: float) -> tuple[float, float]:
        """Extract and validate threshold values from the input fields."""
        try:
            lower_val = float(self.lower_edit.text())
        except ValueError:
            lower_val = round(default_lower, 2)
            self.lower_edit.setText(str(lower_val))
        try:
            upper_val = float(self.upper_edit.text())
        except ValueError:
            upper_val = round(default_upper, 2)
            self.upper_edit.setText(str(upper_val))
        
        if lower_val >= upper_val:
            upper_val = lower_val + 0.01
            self.upper_edit.setText(str(round(upper_val, 2)))
        return lower_val, upper_val
