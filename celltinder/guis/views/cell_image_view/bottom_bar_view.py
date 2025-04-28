from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal


class BottomBarWidget(QWidget):
    """Create the bottom bar area"""
    previousCellClicked = pyqtSignal()
    skipCellClicked = pyqtSignal()
    keepCellClicked = pyqtSignal()
    processCellsClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create the bottom bar container (the "box") with an empty horizontal layout.
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # Optionally add an initial stretch.
        self.layout.addStretch()
        
        # Add each button using dedicated methods.
        self._init_prev_cell_button()
        self._init_skip_cell_button()
        self._init_keep_cell_button()
        self._init_process_cells_button()

    def _setup_button_layout(self, button: QPushButton) -> None:
        """
        Configures the button's size policy and adds it to the layout.
        """
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout.addWidget(button)
        self.layout.addStretch()
    
    def _init_prev_cell_button(self) -> None:
        """
        Initializes and adds the 'Previous cell' button.
        """
        self.prev_cell_btn = QPushButton("Previous cell")
        self._setup_button_layout(self.prev_cell_btn)
        # Connect the button to the signal.
        self.prev_cell_btn.clicked.connect(self.previousCellClicked.emit)

    def _init_skip_cell_button(self) -> None:
        """
        Initializes and adds the 'Reject cell' button.
        """
        self.skip_cell_btn = QPushButton("Reject cell")
        self._setup_button_layout(self.skip_cell_btn)
        # Connect the button to the signal.
        self.skip_cell_btn.clicked.connect(self.skipCellClicked.emit)

    def _init_keep_cell_button(self) -> None:
        """
        Initializes and adds the 'Keep cell' button.
        """
        self.keep_cell_btn = QPushButton("Keep cell")
        self._setup_button_layout(self.keep_cell_btn)
        # Connect the button to the signal.
        self.keep_cell_btn.clicked.connect(self.keepCellClicked.emit)

    def _init_process_cells_button(self) -> None:
        """
        Initializes and adds the 'Process cells' button.
        """
        self.process_cells_btn = QPushButton("Process cells")
        self._setup_button_layout(self.process_cells_btn)
        # Connect the button to the signal.
        self.process_cells_btn.clicked.connect(self.processCellsClicked.emit)

