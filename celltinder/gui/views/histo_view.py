from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class HistogramView(QMainWindow):
    """Main window for the histogram GUI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Histogram GUI")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        
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
        
        # Create controls for thresholds and cell count display
        self._create_controls()
        # Create the Next button
        self._create_next_button()

    def _create_controls(self):
        """Create the controls for setting thresholds and displaying cell count."""
        
        self.controls_layout = QHBoxLayout()
        
        # Lower Threshold Input
        self.lower_layout = QVBoxLayout()
        self.lower_label = QLabel("Lower Threshold")
        self.lower_edit = QLineEdit()
        self.lower_edit.setFixedWidth(120)
        self.lower_edit.setStyleSheet("color: red;")
        self.lower_layout.addWidget(self.lower_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lower_layout.addWidget(self.lower_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Upper Threshold Input
        self.upper_layout = QVBoxLayout()
        self.upper_label = QLabel("Upper Threshold")
        self.upper_edit = QLineEdit()
        self.upper_edit.setFixedWidth(120)
        self.upper_edit.setStyleSheet("color: green;")
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
        
        # Combine layouts
        self.controls_layout.addLayout(self.lower_layout)
        self.controls_layout.addLayout(self.upper_layout)
        self.controls_layout.addLayout(self.count_layout)
        self.main_layout.addLayout(self.controls_layout)
    
    def _create_next_button(self):
        """Create the 'Next' button."""
        
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.next_button = QPushButton("Next")
        self.button_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.button_layout)

    # Public methods to update UI elements
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
        """Extract the threshold values from the input fields. If invalid, reset to default. It will also enforce that lower is less than upper."""
        
        try:
            lower_val = float(self.lower_edit.text())
        except ValueError:
            lower_val = round(default_lower, 2)
            self.lower_edit.setText(str(lower_val))
        try:
            upper_val = float(self.upper_edit.text())
        except ValueError:
            upper_val = round(default_upper, 2)
            self.upper_edit.setText(str(upper_val))  # Update text to default
        
        # Enforce that lower is less than upper
        sender = self.sender()
        match sender:
            case self.lower_edit:
                if lower_val >= upper_val:
                    lower_val = upper_val - 0.01
                    self.lower_edit.setText(str(round(lower_val, 2)))
            case self.upper_edit:
                if upper_val <= lower_val:
                    upper_val = lower_val + 0.01
                    self.upper_edit.setText(str(round(upper_val, 2)))
        
        return lower_val, upper_val
