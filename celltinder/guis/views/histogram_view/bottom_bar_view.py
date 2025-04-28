from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal


class BottomBarWidget(QWidget):
    """
    Widget that displays the bottom bar with a "To CellView" button.
    """
    toCellViewClicked = pyqtSignal()
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addStretch()
        
        # Add the "To CellView" button to the bottom bar.
        self._init_to_cellview_button()
        
    def _init_to_cellview_button(self) -> None:
        """
        Initializes and adds the "To CellView" button.
        """
        self.to_cellview_button = QPushButton("To CellView")
        self.to_cellview_button.clicked.connect(self.toCellViewClicked.emit)
        # Insert the button at the end of the layout.
        self.layout.insertWidget(-1, self.to_cellview_button)
