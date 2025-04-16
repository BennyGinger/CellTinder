from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from celltinder.backend.data_loader import DataLoader

class GraphWidget(QWidget):
    """
    Widget that displays the matplotlib graph along with its navigation toolbar.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 4))
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


class ControlsWidget(QWidget):
    """
    Widget that contains the threshold input controls and cell count display.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)

        # Lower Threshold Input
        lower_layout = QVBoxLayout()
        self.lower_label = QLabel("Lower Threshold")
        self.lower_edit = QLineEdit()
        self.lower_edit.setFixedWidth(120)
        self.lower_edit.setStyleSheet("color: red;")
        self.lower_edit.setValidator(QDoubleValidator(0.0, 1000.0, 2))
        lower_layout.addWidget(self.lower_label, alignment=Qt.AlignmentFlag.AlignCenter)
        lower_layout.addWidget(self.lower_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Upper Threshold Input
        upper_layout = QVBoxLayout()
        self.upper_label = QLabel("Upper Threshold")
        self.upper_edit = QLineEdit()
        self.upper_edit.setFixedWidth(120)
        self.upper_edit.setStyleSheet("color: green;")
        self.upper_edit.setValidator(QDoubleValidator(0.0, 1000.0, 2))
        upper_layout.addWidget(self.upper_label, alignment=Qt.AlignmentFlag.AlignCenter)
        upper_layout.addWidget(self.upper_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Cell Count Display
        count_layout = QVBoxLayout()
        self.count_label = QLabel("Cell Count")
        self.count_display = QLabel("0")
        self.count_display.setFixedWidth(120)
        self.count_display.setStyleSheet("font-weight: bold;")
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        count_layout.addWidget(self.count_display, alignment=Qt.AlignmentFlag.AlignCenter)

        # Combine the three sublayouts into a single controls layout
        layout.addLayout(lower_layout)
        layout.addLayout(upper_layout)
        layout.addLayout(count_layout)

    def update_count(self, count: int) -> None:
        """
        Update the cell count display.
        """
        self.count_display.setText(str(count))

    def get_threshold_values(self, default_lower: float, default_upper: float) -> tuple[float, float]:
        """
        Extract and validate threshold values from the input fields.
        """
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


class BottomBarWidget(QWidget):
    """
    Widget that displays the bottom bar with a "Next" button.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addStretch()
        self.next_button = QPushButton("Next")
        layout.addWidget(self.next_button)


class HistogramView(QMainWindow):
    """
    Main window for the histogram GUI.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Histogram GUI")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.resize(500, 500)

        # Create and add the graph area (graph and toolbar)
        self.graph_widget = GraphWidget()
        self.main_layout.addWidget(self.graph_widget)

        # Create and add the controls area (threshold inputs and cell count)
        self.controls_widget = ControlsWidget()
        self.main_layout.addWidget(self.controls_widget)

        # Create and add the bottom bar with the "Next" button
        self.bottom_bar = BottomBarWidget()
        self.main_layout.addWidget(self.bottom_bar)

    def update_plot(self, lower_val: float, upper_val: float, ratios: list) -> None:
        """
        Delegate plot updating to the GraphWidget.
        """
        self.graph_widget.update_plot(lower_val, upper_val, ratios)

    def update_count(self, count: int) -> None:
        """
        Delegate count update to the ControlsWidget.
        """
        self.controls_widget.update_count(count)

    def get_threshold_values(self, default_lower: float, default_upper: float) -> tuple[float, float]:
        """
        Delegate threshold value retrieval to the ControlsWidget.
        """
        return self.controls_widget.get_threshold_values(default_lower, default_upper)
    
    @property
    def lower_edit(self) -> QLineEdit:
        """
        Property to access the lower threshold QLineEdit.
        """
        return self.controls_widget.lower_edit
    
    @property
    def upper_edit(self) -> QLineEdit:
        """
        Property to access the upper threshold QLineEdit.
        """
        return self.controls_widget.upper_edit
    
    @property
    def next_button(self) -> QPushButton:
        """
        Property to access the "Next" button.
        """
        return self.bottom_bar.next_button

class HistogramController:
    def __init__(self, model: DataLoader, view: HistogramView) -> None:
        self.model = model
        self.view = view
        
        # Check if the DataFrame contains a threshold column that follows the pattern "float < x < float"
        displayed_lower, displayed_upper = self.model.retrieve_threshold_range()
        
        # Set default threshold values in the view
        self.view.lower_edit.setText(str(round(displayed_lower, 2)))
        self.view.upper_edit.setText(str(round(displayed_upper, 2)))
        
        # Initialize display with current cell count
        initial_count = self.model.get_cell_count(displayed_lower, displayed_upper)
        self.view.update_count(initial_count)
        
        # Connect view signals to controller methods
        self.view.lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.next_button.clicked.connect(self.on_next_pressed)
        
        # Draw the initial plot
        self.view.update_plot(displayed_lower, displayed_upper, self.model.ratios)
    
    def on_threshold_change(self) -> None:
        """
        Update the cell count and plot when the threshold values change.
        """
        
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        count = self.model.get_cell_count(lower_val, upper_val)
        self.view.update_count(count)
        self.view.update_plot(lower_val, upper_val, self.model.ratios)

    def on_next_pressed(self) -> None:
        """
        Add a new column to the DataFrame based on the current threshold values.
        """
        
        # Get the threshold values from the view and create a column name
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        column_name = f"{lower_val} < x < {upper_val}"
        
        # Find any column whose name contains "< x <", indicating a threshold column
        threshold_cols = [col for col in self.model.df.columns if "< x <" in col]
        
        if threshold_cols:
            # If found, drop them to ensure only one threshold column exists
            self.model.df.drop(columns=threshold_cols, inplace=True)
            print(f"Overwriting existing threshold columns {threshold_cols} with new column '{column_name}'.")
        else:
            print(f"New column '{column_name}' added to the DataFrame.")
            
        # Add a new column to the DataFrame based on the threshold values
        self.model.df[column_name] = self.model.df['ratio'].apply(lambda x: lower_val < x < upper_val)
        self.model.update_thresholds(lower_val, upper_val, column_name)
        self.model.save_csv()