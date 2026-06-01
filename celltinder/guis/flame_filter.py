from pathlib import Path
import sys
from typing import Any, cast

from PyQt6.QtWidgets import QApplication

from celltinder.backend.data_loader import DataLoader, RATIO, F_MINUS_F0, F0
from celltinder.guis.views.flame_view import FlameView


class FlameFilter:
    """
    Controller for the FlameFilter GUI, managing the interaction between the model (DataLoader) and the view (FlameView).
    """
    def __init__(self, model: DataLoader, view: FlameView) -> None:
        self.model = model
        self.view = view
        
        # Load persisted thresholds if present, otherwise defaults.
        ratio_lower, ratio_upper = self.model.load_threshold_bounds(RATIO)
        ff0_available = self.model.has_metric(F_MINUS_F0)
        ff0_lower, ff0_upper = self.model.load_threshold_bounds(F_MINUS_F0) if ff0_available else (0.0, 1.0)
        f0_available = self.model.has_metric(F0)
        f0_lower, f0_upper = self.model.load_threshold_bounds(F0) if f0_available else (0.0, 1.0)
        
        # Set default threshold values in the view for both metrics
        self.view.lower_edit.setText(str(round(ratio_lower, 2)))
        self.view.upper_edit.setText(str(round(ratio_upper, 2)))
        self.view.ff0_lower_edit.setText(str(round(ff0_lower, 2)))
        self.view.ff0_upper_edit.setText(str(round(ff0_upper, 2)))
        self.view.ff0_checkbox.setEnabled(ff0_available)
        self.view.ff0_lower_edit.setEnabled(ff0_available)
        self.view.ff0_upper_edit.setEnabled(ff0_available)
        self.view.f0_lower_edit.setText(str(round(f0_lower, 2)))
        self.view.f0_upper_edit.setText(str(round(f0_upper, 2)))
        self.view.f0_checkbox.setEnabled(f0_available)
        self.view.f0_lower_edit.setEnabled(f0_available)
        self.view.f0_upper_edit.setEnabled(f0_available)
        
        # Initialize valid-cell count from all three threshold sets.
        initial_count = self.model.apply_thresholds(
            ratio_lower,
            ratio_upper,
            ff0_lower,
            ff0_upper,
            f0_lower,
            f0_upper,
            persist=False,
        )
        self.view.update_count(initial_count)
        
        # Connect view signals to controller methods
        self.view.lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.ff0_lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.ff0_upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.f0_lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.f0_upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.ratio_checkbox.toggled.connect(self.on_ratio_toggled)
        self.view.ff0_checkbox.toggled.connect(self.on_ff0_toggled)
        self.view.f0_checkbox.toggled.connect(self.on_f0_toggled)
        self.view.next_button.clicked.connect(self.on_next_pressed)
        
        # Draw the initial plot for ratio by default.
        self.view.update_plot(ratio_lower, ratio_upper, self.model.get_metric_values(RATIO).tolist())
        # hook up the two drag callbacks:
        gw = cast(Any, self.view.graph_widget)
        gw.on_lower_moved = self.on_lower_moved
        gw.on_upper_moved = self.on_upper_moved
        
        # hook up the span selector callback
        gw.on_span_select = self._on_span_selected

    def on_threshold_change(self) -> None:
        """
        Update the cell count and plot when the threshold values change.
        """
        ratio_lower, ratio_upper = self.view.get_threshold_values(
            RATIO,
            *self.model.get_default_bounds(RATIO),
        )

        if self.model.has_metric(F_MINUS_F0):
            ff0_lower, ff0_upper = self.view.get_threshold_values(
                F_MINUS_F0,
                *self.model.get_default_bounds(F_MINUS_F0),
            )
        else:
            ff0_lower, ff0_upper = (0.0, 1.0)

        if self.model.has_metric(F0):
            f0_lower, f0_upper = self.view.get_threshold_values(
                F0,
                *self.model.get_default_bounds(F0),
            )
        else:
            f0_lower, f0_upper = (0.0, 1.0)

        valid_count = self.model.apply_thresholds(
            ratio_lower,
            ratio_upper,
            ff0_lower,
            ff0_upper,
            f0_lower,
            f0_upper,
            persist=False,
        )
        self.view.update_count(valid_count)

        metric = self._active_metric()
        if metric is None:
            self.view.clear_plot()
            return

        if metric == RATIO:
            lower_val, upper_val = ratio_lower, ratio_upper
        elif metric == F_MINUS_F0:
            lower_val, upper_val = ff0_lower, ff0_upper
        else:
            lower_val, upper_val = f0_lower, f0_upper
        self.view.update_plot(lower_val, upper_val, self.model.get_metric_values(metric).tolist())

    def on_ratio_toggled(self, checked: bool) -> None:
        """
        Toggle ratio mode and keep metric checkboxes mutually exclusive.
        """
        if checked:
            self.view.ff0_checkbox.blockSignals(True)
            self.view.ff0_checkbox.setChecked(False)
            self.view.ff0_checkbox.blockSignals(False)
            self.view.f0_checkbox.blockSignals(True)
            self.view.f0_checkbox.setChecked(False)
            self.view.f0_checkbox.blockSignals(False)
        self.on_threshold_change()

    def on_ff0_toggled(self, checked: bool) -> None:
        """
        Toggle F-F0 mode and keep metric checkboxes mutually exclusive.
        """
        if checked:
            self.view.ratio_checkbox.blockSignals(True)
            self.view.ratio_checkbox.setChecked(False)
            self.view.ratio_checkbox.blockSignals(False)
            self.view.f0_checkbox.blockSignals(True)
            self.view.f0_checkbox.setChecked(False)
            self.view.f0_checkbox.blockSignals(False)
        self.on_threshold_change()

    def on_f0_toggled(self, checked: bool) -> None:
        """
        Toggle F0 mode and keep metric checkboxes mutually exclusive.
        """
        if checked:
            self.view.ratio_checkbox.blockSignals(True)
            self.view.ratio_checkbox.setChecked(False)
            self.view.ratio_checkbox.blockSignals(False)
            self.view.ff0_checkbox.blockSignals(True)
            self.view.ff0_checkbox.setChecked(False)
            self.view.ff0_checkbox.blockSignals(False)
        self.on_threshold_change()

    def on_next_pressed(self) -> None:
        """
        Persist current threshold columns and valid_cell into CSV.
        """
        ratio_lower, ratio_upper = self.view.get_threshold_values(
            RATIO,
            *self.model.get_default_bounds(RATIO),
        )
        if self.model.has_metric(F_MINUS_F0):
            ff0_lower, ff0_upper = self.view.get_threshold_values(
                F_MINUS_F0,
                *self.model.get_default_bounds(F_MINUS_F0),
            )
        else:
            ff0_lower, ff0_upper = (0.0, 1.0)
        if self.model.has_metric(F0):
            f0_lower, f0_upper = self.view.get_threshold_values(
                F0,
                *self.model.get_default_bounds(F0),
            )
        else:
            f0_lower, f0_upper = (0.0, 1.0)

        valid_count = self.model.apply_thresholds(
            ratio_lower,
            ratio_upper,
            ff0_lower,
            ff0_upper,
            f0_lower,
            f0_upper,
            persist=True,
        )
        self.view.update_count(valid_count)
        self.model.load_threshold_bounds(RATIO)
        if self.model.has_metric(F_MINUS_F0):
            self.model.load_threshold_bounds(F_MINUS_F0)
        if self.model.has_metric(F0):
            self.model.load_threshold_bounds(F0)

    def on_lower_moved(self, new_lower: float) -> None:
        # enforce lower < upper
        metric = self._active_metric()
        if metric is None:
            return
        if metric == RATIO:
            upper_edit, lower_edit = self.view.upper_edit, self.view.lower_edit
        elif metric == F_MINUS_F0:
            upper_edit, lower_edit = self.view.ff0_upper_edit, self.view.ff0_lower_edit
        else:
            upper_edit, lower_edit = self.view.f0_upper_edit, self.view.f0_lower_edit
        upper = float(upper_edit.text())
        if new_lower >= upper:
            new_lower = upper - 0.01
        lower_edit.setText(f"{new_lower:.2f}")
        self.on_threshold_change()

    def on_upper_moved(self, new_upper: float) -> None:
        metric = self._active_metric()
        if metric is None:
            return
        if metric == RATIO:
            upper_edit, lower_edit = self.view.upper_edit, self.view.lower_edit
        elif metric == F_MINUS_F0:
            upper_edit, lower_edit = self.view.ff0_upper_edit, self.view.ff0_lower_edit
        else:
            upper_edit, lower_edit = self.view.f0_upper_edit, self.view.f0_lower_edit
        lower = float(lower_edit.text())
        if new_upper <= lower:
            new_upper = lower + 0.01
        upper_edit.setText(f"{new_upper:.2f}")
        self.on_threshold_change()

    def _on_span_selected(self, lower: float, upper: float) -> None:
        # push values into the edits and redraw
        metric = self._active_metric()
        if metric is None:
            return
        if metric == RATIO:
            lower_edit, upper_edit = self.view.lower_edit, self.view.upper_edit
        elif metric == F_MINUS_F0:
            lower_edit, upper_edit = self.view.ff0_lower_edit, self.view.ff0_upper_edit
        else:
            lower_edit, upper_edit = self.view.f0_lower_edit, self.view.f0_upper_edit
        lower_edit.setText(f"{lower:.2f}")
        upper_edit.setText(f"{upper:.2f}")
        self.on_threshold_change()

    def _active_metric(self) -> str | None:
        if self.view.ff0_checkbox.isChecked() and self.model.has_metric(F_MINUS_F0):
            return F_MINUS_F0
        if self.view.f0_checkbox.isChecked() and self.model.has_metric(F0):
            return F0
        if self.view.ratio_checkbox.isChecked():
            return RATIO
        return None


def run_flame_filter(csv_path: Path, n_frames: int = 2, crop_size: int = 151) -> None:
    """
    Run the FlameFilter GUI application.
    Args:
        csv_path (Path): Path to the CSV file containing cell data.
        n_frames (int): Number of frames to load.
        crop_size (int): Size of the cropped images.
    """
    app = QApplication(sys.argv)
    data = DataLoader(csv_path, n_frames, crop_size)
    view = FlameView()
    
    controller = FlameFilter(data, view)
    controller.view.show()

    app.exec()


if __name__ == '__main__':
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    run_flame_filter(csv_path)