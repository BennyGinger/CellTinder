from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from celltinder.backend.load_data import LoadData


class HistogramWindow(QMainWindow):
    """
    Main window for the histogram GUI.
    
    This window displays a histogram of ratio data and provides controls for the user to set 
    lower and upper threshold values. The GUI then updates the displayed cell count based on 
    the thresholds and redraws the histogram with vertical lines marking the thresholds.
    """

    def __init__(self, data: "LoadData") -> None:
        """
        Initialize the GUI window.
        
        Parameters:
            data (LoadData): A backend object that contains the ratio data, default thresholds,
                             and methods to get cell counts.
        """
        super().__init__()
        self.data = data
        self.setWindowTitle("Histogram GUI")

        # --- Create main widget and layout ---
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # --- Create and add the Matplotlib Figure and Canvas ---
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)

        # --- Add the Navigation Toolbar (for zooming, panning, etc.) ---
        self.toolbar = NavigationToolbar(self.canvas, self)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()           # Stretch on the left
        toolbar_layout.addWidget(self.toolbar)  # Place toolbar in center
        toolbar_layout.addStretch()           # Stretch on the right
        self.main_layout.addLayout(toolbar_layout)

        # --- Create the control area (threshold inputs and cell count display) ---
        self.create_controls()

        # --- Create the Next button at the bottom right ---
        self.create_next_button()

        # --- Connect signals to update the plot when thresholds change ---
        self.lower_edit.textChanged.connect(self.on_threshold_change)
        self.upper_edit.textChanged.connect(self.on_threshold_change)

        # Connect Next button to create the new column only when pressed
        self.next_button.clicked.connect(self.on_next_pressed)
        
        # --- Draw the initial plot ---
        self.update_plot()

    def create_controls(self) -> None:
        """Create and add threshold input boxes and the cell count display."""
        self.controls_layout = QHBoxLayout()

        # Lower Threshold Input
        self.lower_layout = QVBoxLayout()
        self.lower_label = QLabel("Lower Threshold")
        # Round default value for display
        low_threshold = round(self.data.default_lower, 2)
        self.lower_edit = QLineEdit(str(low_threshold))
        self.lower_edit.setFixedWidth(120)
        self.lower_edit.setStyleSheet("color: red;")
        self.lower_layout.addWidget(self.lower_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lower_layout.addWidget(self.lower_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Upper Threshold Input
        self.upper_layout = QVBoxLayout()
        self.upper_label = QLabel("Upper Threshold")
        up_threshold = round(self.data.default_upper, 2)
        self.upper_edit = QLineEdit(str(up_threshold))
        self.upper_edit.setFixedWidth(120)
        self.upper_edit.setStyleSheet("color: green;")
        self.upper_layout.addWidget(self.upper_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.upper_layout.addWidget(self.upper_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Cell Count Display (read-only)
        self.count_layout = QVBoxLayout()
        self.count_label = QLabel("Cell Count")
        # Get the initial cell count using the default thresholds
        initial_count = self.data.get_cell_count(self.data.default_lower, self.data.default_upper)
        self.count_display = QLabel(str(initial_count))
        self.count_display.setFixedWidth(120)
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_display, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add each control block into the main control layout
        self.controls_layout.addLayout(self.lower_layout)
        self.controls_layout.addLayout(self.upper_layout)
        self.controls_layout.addLayout(self.count_layout)
        self.main_layout.addLayout(self.controls_layout)

    def create_next_button(self) -> None:
        """Create and add the 'Next' button at the bottom right of the window."""
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()  # Pushes the button to the right
        self.next_button = QPushButton("Next")
        self.button_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.button_layout)

    def on_threshold_change(self) -> None:
        """Called when either threshold input is changed to update the plot."""
        self.update_plot()

    def update_plot(self) -> None:
        """
        Update the histogram plot, threshold lines, and cell count display.
        
        This method reads the current values from the threshold input boxes, updates their 
        text color (gray if default, black if modified), filters the data to count the cells 
        within the thresholds, and redraws the histogram with vertical lines showing the thresholds.
        """
        
        lower_val, upper_val = self._parse_threshold_values()

        # Set threshold input colors to match vertical line colors
        self.lower_edit.setStyleSheet("color: red;")
        self.upper_edit.setStyleSheet("color: green;")

        # --- Update cell count display using the backend logic ---
        count = self.data.get_cell_count(lower_val, upper_val)
        self.count_display.setText(str(count))

        # --- Redraw the histogram with updated thresholds ---
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # Plot histogram of ratios
        ax.hist(self.data.ratios, bins=50, color='blue', alpha=0.7)
        # Draw vertical lines for lower and upper thresholds
        ax.axvline(x=lower_val, color='red', linestyle='--', label='Lower Threshold')
        ax.axvline(x=upper_val, color='green', linestyle='--', label='Upper Threshold')
        # Set labels and title
        ax.set_xlabel("Ratio")
        ax.set_ylabel("Count")
        ax.set_title("Histogram of Ratio")
        # Set y-axis to log10 scale
        ax.set_yscale('log', base=10)
        # Draw the canvas with the updated plot
        self.canvas.draw()

    def _parse_threshold_values(self) -> tuple[float, float]:
        """Parse the threshold values from the input boxes, falling back to defaults if invalid."""
        
        try:
            lower_val = float(self.lower_edit.text())
        except ValueError:
            lower_val = self.data.default_lower

        try:
            upper_val = float(self.upper_edit.text())
        except ValueError:
            upper_val = self.data.default_upper
        return lower_val,upper_val
    
    def on_next_pressed(self) -> None:
        """
        Create a new column in the DataFrame with threshold information.
        
        The new column is named "lower_val < x < upper_val" and for each cell in the DataFrame's 
        'ratio' column, the value is True if the cell's ratio is strictly between the lower and upper
        thresholds, and False otherwise.
        """
        lower_val, upper_val = self._parse_threshold_values()

        # --- Construct column name and update the DataFrame ---
        column_name = f"{lower_val} < x < {upper_val}"
        self.data.df[column_name] = self.data.df['ratio'].apply(lambda x: lower_val < x < upper_val)
        print(f"New column '{column_name}' added to the DataFrame.")
        
        # --- Save the updated DataFrame to a new CSV file ---
        self.data.save_csv()
        
        # Optionally, proceed to the next step in your pipeline here.
        
