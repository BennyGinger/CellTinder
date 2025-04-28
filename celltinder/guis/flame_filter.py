from pathlib import Path
import sys

from PyQt6.QtWidgets import QApplication

from celltinder.backend.data_loader import DataLoader
from celltinder.guis.views.flame_view import FlameView


class FlameFilter:
    """
    Controller for the FlameFilter GUI, managing the interaction between the model (DataLoader) and the view (FlameView).
    """
    def __init__(self, model: DataLoader, view: FlameView) -> None:
        self.model = model
        self.view = view
        
        # Check if the DataFrame contains a threshold column that follows the pattern "float < x < float"
        displayed_lower, displayed_upper = self.model.load_threshold_bounds()
        
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
        self.model.save_csv()
        self.model.load_threshold_bounds()

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

    sys.exit(app.exec())


if __name__ == '__main__':
    
    csv_path = Path("/media/ben/Analysis/Python/CellTinder/ImagesTest/A1/A1_cell_data.csv")
    # csv_path = Path("/home/ben/Lab/Python/CellTinder/ImagesTest/20250320_test_short/A1/A1_cell_data.csv")
    run_flame_filter(csv_path)