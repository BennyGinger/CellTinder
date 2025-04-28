from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator


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