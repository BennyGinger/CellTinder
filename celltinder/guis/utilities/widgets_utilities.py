from typing import Iterable

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal


class BaseToolBar(QWidget):
    """
    HBox toolbar whose buttons & signals are declared in a list.
    """
    
    def __init__(self, buttons: Iterable[tuple[str, str]], parent=None):
        """
        buttons: iterable of (text, attr_name)  
        An attr named *attr_name* is created to host the button **and** a
        pyqtSignal with the same name + "Clicked".
        """
        super().__init__(parent)
        self._box = QHBoxLayout(self)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.addStretch()

        for text, name in buttons:
            self._add_button(text, name)

    def __getattr__(self, item) -> pyqtSignal:
        """
        Create a signal when the attribute is accessed for the first time.
        """
        if item.endswith("Clicked"):
            self.__dict__[item] = pyqtSignal()
            return self.__dict__[item]
        raise AttributeError(item)

    def _add_button(self, text: str, name: str) -> None:
        """
        Create a button with the given text and name, and connect it to the signal.
        """
        btn = QPushButton(text, self)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sig = getattr(self, f"{name}Clicked")
        btn.clicked.connect(sig.emit)
        setattr(self, name, btn)
        self._box.addWidget(btn)
        self._box.addStretch()

