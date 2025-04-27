from __future__ import annotations
from enum import Enum
from typing import Callable, Protocol

from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

# from celltinder.gui.cell_crush.cell_view_manager import CellCrush


class Shortcuts(Enum):
    NEXT_CELL      = ("6", "Move to next cell",     "on_next_cell")
    PREVIOUS_CELL  = ("4", "Move to previous cell", "on_previous_cell")
    KEEP_CELL      = ("s", "Keep cell",             "on_keep_cell")
    REJECT_CELL    = ("r", "Reject cell",           "on_reject_cell")
    TOGGLE_OVERLAY = ("m", "Toggle overlay mask",   "_toggle_overlay")
    NEXT_FRAME     = ("8", "Advance frame",         "_bump_frame")

    def __init__(self, key: str, desc: str, method_name: str):
        self._key = key
        self._desc = desc
        self._method = method_name
    
    @property
    def key(self) -> str:
        return self._key

    @property
    def desc(self) -> str:
        return self._desc

    @property
    def method(self) -> str:
        return self._method

class ShortcutController(Protocol):
    """
    Protocol for the controller that will handle shortcuts.
    It should have a view attribute that is a QWidget.
    The controller should implement the methods defined in the Shortcuts enum.
    """
    view: QWidget

    def on_next_cell(self)      -> None: ...
    def on_previous_cell(self)  -> None: ...
    def on_keep_cell(self)      -> None: ...
    def on_reject_cell(self)    -> None: ...
    def _toggle_overlay(self)   -> None: ...
    def _bump_frame(self)       -> None: ...


class ShortcutManager:
    """
    Centralize all shortcut bindings (from Shortcuts enum)
    and show a help dialog.
    """
    def __init__(self, controller: ShortcutController) -> None:
        self._shortcuts: list[QShortcut] = []
        self._ctrl = controller

        def bind(key: str, slot: Callable) -> None:
            sc = QShortcut(QKeySequence(key), controller.view)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(slot)
            self._shortcuts.append(sc)

        # bind each enum entry to the matching controller method
        for sc in Shortcuts:
            bind(sc.key, getattr(controller, sc.method))

    def show_shortcuts(self):
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self._ctrl.view)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText("\n".join(f"{sc.key} : {sc.desc}" for sc in Shortcuts))
        msg.exec()
