from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal

from celltinder.gui.views.histogram_view.bottom_bar_view import BottomBarWidget
from celltinder.gui.views.histogram_view.controls_view import ControlsWidget
from celltinder.gui.views.histogram_view.graph_view import GraphWidget


class HistoViewWidget(QWidget):
    """
    Widget for the histogram GUI.
    """
    toCellViewClicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        
        # Set the window
        self.main_layout = QVBoxLayout(self)
        self._init_ui_components()
        self._connect_signals()

    def _init_ui_components(self) -> None:
        """
        Initialize the UI components.
        """
        self.graph_widget = GraphWidget()
        self.controls_widget = ControlsWidget()
        self.bottom_bar = BottomBarWidget()

        self.main_layout.addWidget(self.graph_widget)
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addWidget(self.bottom_bar)

    def _connect_signals(self) -> None:
        """
        Connect subwidget signals to the widget's signals.
        """
        self.bottom_bar.toCellViewClicked.connect(self.toCellViewClicked.emit)

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
        Property to access the lower threshold input field.
        """
        return self.controls_widget.lower_edit

    @property
    def upper_edit(self) -> QLineEdit:
        """
        Property to access the upper threshold input field.
        """
        return self.controls_widget.upper_edit

    @property
    def to_cellview_button(self) -> QPushButton:
        """
        Property to access the "To CellView" button.
        """
        return self.bottom_bar.to_cellview_button
