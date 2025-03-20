import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class HistogramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Histogram GUI")
        
        # Load CSV data (ensure data.csv exists with a 'ratio' column)
        self.df = pd.read_csv("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
        self.ratios = self.df['ratio']
        self.default_lower = self.ratios.min()
        self.default_upper = self.ratios.max()

        # Set up the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Create the Matplotlib Figure and Canvas
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)

        # Create the control area (threshold inputs and cell count)
        self.controls_layout = QHBoxLayout()

        # Lower Threshold Input
        self.lower_layout = QVBoxLayout()
        self.lower_label = QLabel("Lower Threshold")
        self.lower_edit = QLineEdit(str(self.default_lower))
        self.lower_edit.setFixedWidth(120)
        # Set default text color (gray) to indicate default value
        self.lower_edit.setStyleSheet("color: gray;")
        self.lower_layout.addWidget(self.lower_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lower_layout.addWidget(self.lower_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Upper Threshold Input
        self.upper_layout = QVBoxLayout()
        self.upper_label = QLabel("Upper Threshold")
        self.upper_edit = QLineEdit(str(self.default_upper))
        self.upper_edit.setFixedWidth(120)
        self.upper_edit.setStyleSheet("color: gray;")
        self.upper_layout.addWidget(self.upper_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.upper_layout.addWidget(self.upper_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Cell Count Display (read-only)
        self.count_layout = QVBoxLayout()
        self.count_label = QLabel("Cell Count")
        initial_count = len(self.df[(self.df['ratio'] >= self.default_lower) & (self.df['ratio'] <= self.default_upper)])
        self.count_display = QLabel(str(initial_count))
        self.count_display.setFixedWidth(120)
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_display, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add each of the control layouts to the main controls layout
        self.controls_layout.addLayout(self.lower_layout)
        self.controls_layout.addLayout(self.upper_layout)
        self.controls_layout.addLayout(self.count_layout)
        self.main_layout.addLayout(self.controls_layout)

        # Next button at bottom right
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.next_button = QPushButton("Next")
        self.button_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.button_layout)

        # Connect signals for threshold changes
        self.lower_edit.textChanged.connect(self.update_plot)
        self.upper_edit.textChanged.connect(self.update_plot)

        # Draw the initial plot
        self.update_plot()

    def update_plot(self):
        # Retrieve threshold values (fallback to defaults if not valid)
        try:
            lower_val = float(self.lower_edit.text())
        except ValueError:
            lower_val = self.default_lower
        try:
            upper_val = float(self.upper_edit.text())
        except ValueError:
            upper_val = self.default_upper

        # Update text color based on whether the value is the default or modified
        if self.lower_edit.text() == str(self.default_lower):
            self.lower_edit.setStyleSheet("color: gray;")
        else:
            self.lower_edit.setStyleSheet("color: black;")
        if self.upper_edit.text() == str(self.default_upper):
            self.upper_edit.setStyleSheet("color: gray;")
        else:
            self.upper_edit.setStyleSheet("color: black;")

        # Filter data based on the thresholds and update cell count
        filtered_df = self.df[(self.df['ratio'] >= lower_val) & (self.df['ratio'] <= upper_val)]
        self.count_display.setText(str(len(filtered_df)))

        # Clear the previous plot and create a new one
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.hist(self.ratios, bins=50, color='blue', alpha=0.7)
        # Add vertical threshold lines
        ax.axvline(x=lower_val, color='red', linestyle='--', label='Lower Threshold')
        ax.axvline(x=upper_val, color='green', linestyle='--', label='Upper Threshold')
        ax.set_xlabel("Ratio")
        ax.set_ylabel("Count")
        ax.set_title("Histogram of Ratio")
        ax.legend()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HistogramWindow()
    window.show()
    sys.exit(app.exec())
