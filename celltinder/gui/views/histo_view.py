from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


from celltinder.backend.data_loader import DataLoader


class DraggableLine:
    """
    Makes a matplotlib vertical Line2D artist draggable along the x-axis. Calls `callback(new_x)` whenever dragging moves the line.
    """
    def __init__(self, line, callback):
        self.line = line
        self.callback = callback
        self.press = None
        canvas = line.figure.canvas
        canvas.mpl_connect('button_press_event', self.on_press)
        canvas.mpl_connect('button_release_event', self.on_release)
        canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
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
        x0 = self.line.get_xdata()[0]
        self.press = (x0, event.xdata)

    def on_motion(self, event):
        # ignore if not dragging, outside axes, or no xdata
        if (self.press is None or
            event.inaxes != self.line.axes or
            event.xdata is None):
            return
        x0, xpress = self.press
        dx = event.xdata - xpress
        newx = x0 + dx
        self.line.set_xdata([newx, newx])
        self.line.figure.canvas.draw_idle()
        self.callback(newx)
    
    def on_release(self, event):
        self.press = None
    
    def set_line(self, line):
        # re-bind to the new Line2D instance
        self.line = line


class GraphWidget(QWidget):
    """
    Widget that displays the matplotlib graph along with its navigation toolbar.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6))
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
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Create a toolbar layout with center alignment
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

    def update_plot(self, lower_val: float, upper_val: float, ratios: list) -> None:
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
            self.draggable_upper = DraggableLine(self.upper_line, lambda x: self.on_upper_moved(x) if self.on_upper_moved else None)
        else:
            self.draggable_lower.set_line(self.lower_line)
            self.draggable_upper.set_line(self.upper_line)
        
        if self._span_rect is not None:
            self._span_rect.set_visible(False)
            self._span_rect = None
        
        ax.set_xlabel("Ratio")
        ax.set_ylabel("Count")
        ax.set_title("Histogram of Ratio")
        ax.set_yscale('log', base=10)
        self.canvas.draw()

    def _on_span_press(self, event) -> None:
        """
        Start the span selection on right-click in the axes.
        """
        if event.inaxes is not self.ax or event.button != 3 or event.xdata is None:
            return
        self._span_start = event.xdata
        
        # make a new rectangle at y=axes bottom
        ymin, ymax = self.ax.get_ylim()
        self._span_rect = Rectangle((self._span_start, ymin), 0, ymax - ymin, facecolor='yellow', alpha=0.3, edgecolor=None)
        self.ax.add_patch(self._span_rect)
        self.canvas.draw_idle()

    def _on_span_motion(self, event) -> None:
        """
        Update the rectangle during the drag.
        """
        if self._span_start is None or event.inaxes is not self.ax or event.xdata is None:
            return
        start = self._span_start
        end = event.xdata
        
        # update rect x & width
        x0 = min(start, end)
        w = abs(end - start)
        self._span_rect.set_x(x0)
        self._span_rect.set_width(w)
        self.canvas.draw_idle()

    def _on_span_release(self, event) -> None:
        """
        Finish the span selection on right-release in the same axes.
        """
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
        
        
class ControlsWidget(QWidget):
    """
    Widget that contains the threshold input controls and cell count display.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)

        # Lower and Upper Threshold Inputs
        self.lower_label, self.lower_edit, lower_layout = self._create_threshold_input("Lower Threshold", "red")
        self.upper_label, self.upper_edit, upper_layout = self._create_threshold_input("Upper Threshold", "green")

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

    def _create_threshold_input(self, text: str, color: str):
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

class BottomBarWidget(QWidget):
    """
    Widget that displays the bottom bar with a "Next" button.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addStretch()
        self.next_button = QPushButton("Next")
        layout.addWidget(self.next_button)

class HistogramView(QMainWindow):
    """
    Main window for the histogram GUI.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Histogram GUI")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Create and add the graph area (graph and toolbar)
        self.graph_widget = GraphWidget()
        self.main_layout.addWidget(self.graph_widget)

        # Create and add the controls area (threshold inputs and cell count)
        self.controls_widget = ControlsWidget()
        self.main_layout.addWidget(self.controls_widget)

        # Create and add the bottom bar with the "Next" button
        self.bottom_bar = BottomBarWidget()
        self.main_layout.addWidget(self.bottom_bar)

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
        Property to access the lower threshold QLineEdit.
        """
        return self.controls_widget.lower_edit
    
    @property
    def upper_edit(self) -> QLineEdit:
        """
        Property to access the upper threshold QLineEdit.
        """
        return self.controls_widget.upper_edit
    
    @property
    def next_button(self) -> QPushButton:
        """
        Property to access the "Next" button.
        """
        return self.bottom_bar.next_button

class HistogramController:
    def __init__(self, model: DataLoader, view: HistogramView) -> None:
        self.model = model
        self.view = view
        
        # Check if the DataFrame contains a threshold column that follows the pattern "float < x < float"
        displayed_lower, displayed_upper = self.model.retrieve_threshold_range()
        
        # Set default threshold values in the view
        self.view.lower_edit.setText(str(round(displayed_lower, 2)))
        self.view.upper_edit.setText(str(round(displayed_upper, 2)))
        
        # Initialize display with current cell count
        initial_count = self.model.get_cell_count(displayed_lower, displayed_upper)
        self.view.update_count(initial_count)
        
        # Connect view signals to controller methods
        self.view.lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.next_button.clicked.connect(self.on_next_pressed)
        
        # Draw the initial plot
        self.view.update_plot(displayed_lower, displayed_upper, self.model.ratios)

        # hook up the two drag callbacks:
        self.view.graph_widget.on_lower_moved = self.on_lower_moved
        self.view.graph_widget.on_upper_moved = self.on_upper_moved
        
        # hook up the span selector callback
        self.view.graph_widget.on_span_select = self._on_span_selected

    def on_threshold_change(self) -> None:
        """
        Update the cell count and plot when the threshold values change.
        """
        
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        count = self.model.get_cell_count(lower_val, upper_val)
        self.view.update_count(count)
        self.view.update_plot(lower_val, upper_val, self.model.ratios)

    def on_next_pressed(self) -> None:
        """
        Add a new column to the DataFrame based on the current threshold values.
        """
        
        # Get the threshold values from the view and create a column name
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        column_name = f"{lower_val} < x < {upper_val}"
        
        # Find any column whose name contains "< x <", indicating a threshold column
        threshold_cols = [col for col in self.model.df.columns if "< x <" in col]
        
        if threshold_cols:
            # If found, drop them to ensure only one threshold column exists
            self.model.df.drop(columns=threshold_cols, inplace=True)
            
        # Add a new column to the DataFrame based on the threshold values
        self.model.df[column_name] = self.model.df['ratio'].apply(lambda x: lower_val < x < upper_val)
        self.model.update_thresholds(lower_val, upper_val, column_name)
        self.model.save_csv()

    def on_lower_moved(self, new_lower: float) -> None:
        # enforce lower < upper
        upper = float(self.view.upper_edit.text())
        if new_lower >= upper:
            new_lower = upper - 0.01
        self.view.lower_edit.setText(f"{new_lower:.2f}")
        self.on_threshold_change()

    def on_upper_moved(self, new_upper: float) -> None:
        lower = float(self.view.lower_edit.text())
        if new_upper <= lower:
            new_upper = lower + 0.01
        self.view.upper_edit.setText(f"{new_upper:.2f}")
        self.on_threshold_change()

    def _on_span_selected(self, lower: float, upper: float) -> None:
        # push values into the edits and redraw
        self.view.lower_edit.setText(f"{lower:.2f}")
        self.view.upper_edit.setText(f"{upper:.2f}")
        self.on_threshold_change()
    