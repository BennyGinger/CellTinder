from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt


class BaseView(QMainWindow):
    def __init__(self, title: str = "Base View") -> None:
        """
        Initialize the base view with a title and main layout.
        
        Args:
            title: Title of the window.
        """
        
        super().__init__()
        self.setWindowTitle(title)
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
    
    def create_top_bar(self, left_widget: QWidget = None, center_widget: QWidget = None) -> None:
        """
        Create a top bar layout. Optional left or center widget can be provided.
        """
        
        top_layout = QHBoxLayout()
        if left_widget:
            top_layout.addWidget(left_widget)
        if center_widget:
            top_layout.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch()
        self.main_layout.addLayout(top_layout)
    
    def create_bottom_bar(self, buttons: list[QPushButton], alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> None:
        """
        Create a bottom bar layout with buttons. The alignment can be set to left or right.
        """
        # Create a horizontal layout for the bottom bar
        bottom_layout = QHBoxLayout()
        if alignment == Qt.AlignmentFlag.AlignRight:
            bottom_layout.addStretch()
            for btn in buttons:
                bottom_layout.addWidget(btn)
        else:
            for btn in buttons:
                bottom_layout.addWidget(btn)
            bottom_layout.addStretch()
        self.main_layout.addLayout(bottom_layout)

