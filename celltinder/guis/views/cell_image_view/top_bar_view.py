from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal


class TopBarWidget(QWidget):
    """Create the top bar area"""
    backClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create the top bar container (the "box") with an empty horizontal layout.
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addStretch()
        
        # Add the back button to the top bar.
        self._init_back_button()

    def _init_back_button(self) -> None:
        """
        Initializes and adds a back button to the top bar. This method can be called from __init__.
        """
        self.back_btn = QPushButton("Back to histo gui")
        self.back_btn.clicked.connect(self.backClicked.emit)
        # Insert the back button at the beginning of the layout.
        self.layout.insertWidget(0, self.back_btn)