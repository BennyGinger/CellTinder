from __future__ import annotations
from typing import Callable

import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent, Event
from matplotlib.lines import Line2D


# Constants for figure size and DPI
FIG_SIZE = (5, 55)  # inches
DPI = 100  # dots per inch


class FlameView(QMainWindow):
    """
    Main window for the histogram GUI.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flame Filter")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Create a horizontal content split: controls on the left, display on the right.
        self.content_layout = QHBoxLayout()

        self.controls_widget = ThresholdPanel()
        self.display_widget = QWidget()
        self.display_layout = QVBoxLayout(self.display_widget)
        self.graph_widget = GraphWidget()

        self.count_widget = QWidget()
        self.count_layout = QVBoxLayout(self.count_widget)
        self.count_label = QLabel("Cell Count")
        self.count_display = QLabel("0")
        self.count_display.setFixedWidth(120)
        self.count_display.setStyleSheet("font-weight: bold;")
        self.count_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.count_layout.addWidget(self.count_display, alignment=Qt.AlignmentFlag.AlignCenter)

        self.display_layout.addWidget(self.graph_widget)
        self.display_layout.addWidget(self.count_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.content_layout.addWidget(self.controls_widget)
        self.content_layout.addWidget(self.display_widget)
        self.content_layout.setStretch(0, 1)
        self.content_layout.setStretch(1, 2)

        self.main_layout.addLayout(self.content_layout)

        # Create and add the bottom bar with the "Next" button
        self.bottom_bar = BottomBarWidget()
        self.main_layout.addWidget(self.bottom_bar)

    def update_plot(self, lower_val: float, upper_val: float, ratios: list) -> None:
        """
        Delegate plot updating to the GraphWidget.
        """
        self.graph_widget.update_plot(lower_val, upper_val, ratios, x_label=self.active_metric_label())

    def clear_plot(self) -> None:
        """
        Delegate plot clearing to the GraphWidget.
        """
        self.graph_widget.clear_plot()

    def update_count(self, count: int) -> None:
        """
        Update the centered count display under the graph.
        """
        self.count_display.setText(str(count))

    def get_threshold_values(self, metric: str, default_lower: float, default_upper: float) -> tuple[float, float]:
        """
        Delegate threshold value retrieval to the metric-specific controls.
        """
        return self.controls_widget.get_threshold_values(metric, default_lower, default_upper)

    def active_metric_label(self) -> str:
        """
        Return label of the currently active metric for x-axis display.
        """
        if self.ff0_checkbox.isChecked():
            return "F-F0"
        if self.f0_checkbox.isChecked():
            return "F0"
        return "Ratio"
    
    @property
    def lower_edit(self) -> QLineEdit:
        """
        Property to access the ratio lower threshold QLineEdit.
        """
        return self.controls_widget.ratio_lower_edit
    
    @property
    def upper_edit(self) -> QLineEdit:
        """
        Property to access the ratio upper threshold QLineEdit.
        """
        return self.controls_widget.ratio_upper_edit
    
    @property
    def next_button(self) -> QPushButton:
        """
        Property to access the "Next" button.
        """
        return self.bottom_bar.next_button

    @property
    def ratio_checkbox(self) -> QCheckBox:
        """
        Property to access the ratio display checkbox.
        """
        return self.controls_widget.ratio_checkbox

    @property
    def ff0_checkbox(self) -> QCheckBox:
        """
        Property to access the F-F0 display checkbox.
        """
        return self.controls_widget.ff0_checkbox

    @property
    def f0_checkbox(self) -> QCheckBox:
        """
        Property to access the F0 display checkbox.
        """
        return self.controls_widget.f0_checkbox

    @property
    def ff0_lower_edit(self) -> QLineEdit:
        """
        Property to access the F-F0 lower threshold QLineEdit.
        """
        return self.controls_widget.ff0_lower_edit

    @property
    def ff0_upper_edit(self) -> QLineEdit:
        """
        Property to access the F-F0 upper threshold QLineEdit.
        """
        return self.controls_widget.ff0_upper_edit

    @property
    def f0_lower_edit(self) -> QLineEdit:
        """
        Property to access the F0 lower threshold QLineEdit.
        """
        return self.controls_widget.f0_lower_edit

    @property
    def f0_upper_edit(self) -> QLineEdit:
        """
        Property to access the F0 upper threshold QLineEdit.
        """
        return self.controls_widget.f0_upper_edit


class DraggableLine:
    """
    Makes a matplotlib vertical Line2D artist draggable along the x-axis. Calls `callback(new_x)` whenever dragging moves the line.
    """
    def __init__(self, line: Line2D, callback: Callable[[float], None]) -> None:
        self.line = line
        self.callback = callback
        self.press = None
        canvas = line.figure.canvas
        canvas.mpl_connect('button_press_event', self.on_press)
        canvas.mpl_connect('button_release_event', self.on_release)
        canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event: Event) -> None:
        if not isinstance(event, MouseEvent):
            return
        # ignore clicks outside the axes
        if event.inaxes != self.line.axes:
            return
        # guard against a Line2D without a figure
        try:
            contains, _ = self.line.contains(event)
        except Exception:
            return
        if not contains:
            return
        xdata = self.line.get_xdata()
        # Ensure xdata is at least 1-D so indexing is safe
        xdata_arr = np.atleast_1d(xdata)
        x0 = float(xdata_arr[0])
        self.press = (x0, event.xdata)

    def on_motion(self, event: Event) -> None:
        if not isinstance(event, MouseEvent):
            return
        # ignore if not dragging, outside axes, or no xdata
        if (self.press is None or
            event.inaxes != self.line.axes or
            event.xdata is None):
            return
        x0, xpress = self.press
        if event.xdata is None or xpress is None:
            return
        dx = event.xdata - xpress
        newx = x0 + dx
        self.line.set_xdata([newx, newx])
        self.line.figure.canvas.draw_idle()
    def on_release(self, _event: Event) -> None:
        """
        Release the line and reset the press attribute.
        """
        if self.press is not None:
            xdata = np.atleast_1d(self.line.get_xdata())
            if xdata.size > 0 and self.callback is not None:
                self.callback(float(xdata[0]))
        self.press = None
        self.press = None
        self.press = None
    
    def set_line(self, line: Line2D) -> None:
        """
        Set a new line for the draggable line.
        """
        self.line = line


class GraphWidget(QWidget):
    """
    Widget that displays the matplotlib graph along with its navigation toolbar.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=FIG_SIZE, dpi=DPI)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(0, 0)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create a span selector for selecting ranges and connecting it to the canvas
        self._span_start = None
        self._span_rect = None
        self.canvas.mpl_connect('button_press_event', self._on_span_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_span_motion)
        self.canvas.mpl_connect('button_release_event', self._on_span_release)
        
        # Callbacks for the draggable lines
        self.draggable_lower = None
        self.draggable_upper = None
        self.on_lower_moved = None
        self.on_upper_moved = None
        self.on_span_select = None
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Create a toolbar layout with center alignment
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

    def update_plot(self, lower_val: float, upper_val: float, ratios: list, x_label: str = "Ratio") -> None:
        """
        Update the histogram plot with new threshold values.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self.ax = ax
        ax.hist(ratios, bins=50, color='blue', alpha=0.7)
        
        # Draw the threshold lines
        self.lower_line = ax.axvline(x=lower_val, color='red', linestyle='--', label='Lower Threshold')
        self.upper_line = ax.axvline(x=upper_val, color='green', linestyle='--', label='Upper Threshold')
        
        if self.draggable_lower is None:
            self.draggable_lower = DraggableLine(self.lower_line, lambda x: self.on_lower_moved(x) if self.on_lower_moved else None)
        else:
            if self.draggable_lower is not None:
                self.draggable_lower.set_line(self.lower_line)

        if self.draggable_upper is None:
            self.draggable_upper = DraggableLine(self.upper_line, lambda x: self.on_upper_moved(x) if self.on_upper_moved else None)
        else:
            if self.draggable_upper is not None:
                self.draggable_upper.set_line(self.upper_line)
        
        if self._span_rect is not None:
            self._span_rect.set_visible(False)
            self._span_rect = None
        
        ax.set_xlabel(x_label)
        ax.set_ylabel("Count")
        self.canvas.draw()

    def clear_plot(self) -> None:
        """
        Clear the graph area so no ratio histogram is displayed.
        """
        self.figure.clear()
        self.canvas.draw()

        # Existing draggable lines are no longer valid when the figure is cleared.
        self.draggable_lower = None
        self.draggable_upper = None
        self._span_start = None
        self._span_rect = None
        if hasattr(self, "ax"):
            del self.ax

    def _on_span_press(self, event: Event) -> None:
        """
        Start the span selection on right-click in the axes.
        """
        if not isinstance(event, MouseEvent):
            return
        if not hasattr(self, "ax"):
            return
        if event.inaxes is not self.ax or event.button != 3 or event.xdata is None:
            return
        self._span_start = event.xdata
        
        # make a new rectangle at y=axes bottom
        ymin, ymax = self.ax.get_ylim()
        # Use an orange translucent rectangle to indicate selection
        self._span_rect = Rectangle(
            (self._span_start, ymin),
            0,
            ymax - ymin,
            facecolor="#ffaa00",
            alpha=0.3,
            edgecolor=None,
            zorder=3,
        )
        self.ax.add_patch(self._span_rect)
        self.canvas.draw_idle()
    def _on_span_motion(self, event: Event) -> None:
        """
        Update the rectangle during the drag.
        """
        if not isinstance(event, MouseEvent):
            return
        if not hasattr(self, "ax"):
            return
        if self._span_start is None or event.inaxes is not self.ax or event.xdata is None:
            return
        start = self._span_start
        end = event.xdata
        
        # update rect x & width
        x0 = min(start, end)
        width = abs(end - start)
        if self._span_rect is not None:
            self._span_rect.set_x(x0)
            self._span_rect.set_width(width)
            # Repaint during drag so the rectangle is visible while moving
            self.canvas.draw_idle()
    def _on_span_release(self, event: Event) -> None:
        """
        Finish the span selection on right-release in the same axes.
        """
        if not isinstance(event, MouseEvent):
            return
        if not hasattr(self, "ax"):
            return
        if self._span_start is None or event.inaxes is not self.ax or event.button != 3 or event.xdata is None:
            return
        start = self._span_start
        end = event.xdata
        low, high = sorted((start, end))
        
        # fire your controller
        if self.on_span_select:
            self.on_span_select(low, high)
        # clean up
        self._span_start = None
        if self._span_rect is not None:
            self._span_rect.remove()
            self._span_rect = None
        self.canvas.draw_idle()
        # clean up
        self._span_start = None
        
        
class ThresholdPanel(QWidget):
    """
    Widget that contains the threshold input controls and cell count display.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Ratio controls
        self.ratio_checkbox = QCheckBox("ratio")
        self.ratio_checkbox.setChecked(True)
        layout.addWidget(self.ratio_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

        self.ratio_lower_label, self.ratio_lower_edit, ratio_lower_layout = self._create_threshold_input("Lower Threshold", "red")
        self.ratio_upper_label, self.ratio_upper_edit, ratio_upper_layout = self._create_threshold_input("Upper Threshold", "green")
        layout.addLayout(ratio_lower_layout)
        layout.addLayout(ratio_upper_layout)

        # Black divider line between metric sections
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setStyleSheet("color: black;")
        layout.addWidget(divider)

        # F-F0 controls
        self.ff0_checkbox = QCheckBox("F-F0")
        self.ff0_checkbox.setChecked(False)
        layout.addWidget(self.ff0_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

        self.ff0_lower_label, self.ff0_lower_edit, ff0_lower_layout = self._create_threshold_input("Lower Threshold", "red")
        self.ff0_upper_label, self.ff0_upper_edit, ff0_upper_layout = self._create_threshold_input("Upper Threshold", "green")
        layout.addLayout(ff0_lower_layout)
        layout.addLayout(ff0_upper_layout)

        # Black divider before F0 section
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setFrameShadow(QFrame.Shadow.Plain)
        divider2.setStyleSheet("color: black;")
        layout.addWidget(divider2)

        # F0 controls
        self.f0_checkbox = QCheckBox("F0")
        self.f0_checkbox.setChecked(False)
        layout.addWidget(self.f0_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

        self.f0_lower_label, self.f0_lower_edit, f0_lower_layout = self._create_threshold_input("Lower Threshold", "red")
        self.f0_upper_label, self.f0_upper_edit, f0_upper_layout = self._create_threshold_input("Upper Threshold", "green")
        layout.addLayout(f0_lower_layout)
        layout.addLayout(f0_upper_layout)

        layout.addStretch()

    def _create_threshold_input(self, text: str, color: str) -> tuple[QLabel, QLineEdit, QVBoxLayout]:
        """
        Helper to build one threshold input (label + line-edit) and return (label, edit, layout).
        """
        sub = QVBoxLayout()
        lbl = QLabel(text)
        edt = QLineEdit()
        edt.setFixedWidth(120)
        edt.setStyleSheet(f"color: {color};")
        edt.setValidator(QDoubleValidator(0.0, 1000.0, 2))
        sub.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        sub.addWidget(edt, alignment=Qt.AlignmentFlag.AlignCenter)
        return lbl, edt, sub
    
    def get_threshold_values(self, metric: str, default_lower: float, default_upper: float) -> tuple[float, float]:
        """
        Extract and validate threshold values from metric-specific input fields.
        """
        if metric == "F-F0":
            lower_edit = self.ff0_lower_edit
            upper_edit = self.ff0_upper_edit
        elif metric == "before_stim":
            lower_edit = self.f0_lower_edit
            upper_edit = self.f0_upper_edit
        else:
            lower_edit = self.ratio_lower_edit
            upper_edit = self.ratio_upper_edit

        try:
            lower_val = float(lower_edit.text())
        except ValueError:
            lower_val = round(default_lower, 2)
            lower_edit.setText(str(lower_val))
        try:
            upper_val = float(upper_edit.text())
        except ValueError:
            upper_val = round(default_upper, 2)
            upper_edit.setText(str(upper_val))

        if lower_val >= upper_val:
            upper_val = lower_val + 0.01
            upper_edit.setText(str(round(upper_val, 2)))
        return lower_val, upper_val


class BottomBarWidget(QWidget):
    """
    Widget that displays the bottom bar with a "Next" button.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addStretch()
        self.next_button = QPushButton("✅ Find your cell-mate")
        self.next_button.setFixedSize(180, 40)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #44aa44;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #338833;
            }
        """)
        layout.addWidget(self.next_button)




