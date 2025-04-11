# Main Controller coordinating both GUIs and iteration
from pathlib import Path

import pandas as pd

from backend.data_loader import DataLoader
from celltinder.gui.controllers.cell_image_control import CellImageController
from celltinder.gui.controllers.histo_control import HistogramController
from celltinder.gui.views.cell_image_view import CellImageView
from celltinder.gui.views.histo_view import HistogramView
from gui.main_window import MainWindow


class MainController:
    def __init__(self, csv_path: Path):
        self.model = DataLoader(csv_path)
        self.current_cell_index = 0

        # Create the main window with a QStackedWidget
        self.main_window = MainWindow()
        self.stack = self.main_window.stack

        # --- Histogram GUI Setup ---
        self.histo_view = HistogramView()
        # The HistogramController now receives the shared model so it can update thresholds.
        self.histo_controller = HistogramController(self.model, self.histo_view)
        # When "Next" is pressed, we want to filter the data and load the first cell.
        self.histo_view.next_button.clicked.connect(self.on_next_from_histo)

        # --- Cell Image GUI Setup ---
        # Load initial cell data from the filtered DataFrame (initially, full DataFrame)
        
        
        
        cell_data = self.model.get_cell_data(self.current_cell_index)
        if cell_data is None:
            # In case no cell is returned, create a dummy cell data for demonstration.
            cell_data = pd.Series({'centroid_y': 100, 'centroid_x': 100, 'fov_ID': 'dummy_fov', 'ratio': 0.75})
        self.cell_image_set = self.model.loads_arrays(csv_path, cell_data, n_frames=2, crop_size=150)
        self.cell_ratio = cell_data.get('ratio', 0.75)
        total_cells = self.model.total_filtered() if self.model.total_filtered() > 0 else 1
        self.cell_image_view = CellImageView(n_frames=2, cell_number=self.current_cell_index+1,
                                             total_cells=total_cells, cell_ratio=self.cell_ratio)
        self.cell_image_controller = CellImageController(self.cell_image_set, cell_number=self.current_cell_index+1,
                                                         total_cells=total_cells, cell_ratio=self.cell_ratio,
                                                         data_df=self.model.df)
        # Connect the back signal so that pressing "Back to histo gui" returns to histogram view.
        self.cell_image_view.backClicked.connect(self.on_back_to_histo)

        # Add views to the stack (using their central widgets)
        self.stack.addWidget(self.histo_view.centralWidget())  # index 0: Histogram view
        self.stack.addWidget(self.cell_image_view.centralWidget())  # index 1: Cell image view

        # Start by showing the histogram view.
        self.stack.setCurrentIndex(0)

    def on_next_from_histo(self):
        # Retrieve the current threshold values from the histogram view.
        lower, upper = self.histo_view.get_threshold_values(default_lower=0.0, default_upper=1.0)
        # Filter the data based on these thresholds.
        self.model.filter_cells(lower, upper)
        self.current_cell_index = 0  # Reset to the first filtered cell.
        self.load_current_cell()
        # Switch to the cell image view.
        self.stack.setCurrentIndex(1)

    def on_back_to_histo(self):
        # When returning to the histogram view, you might want to re-read the thresholds.
        self.stack.setCurrentIndex(0)
        # Optionally, you could also re-run filtering if needed.

    def load_current_cell(self):
        # Load cell data for the current cell index from the filtered DataFrame.
        cell_data = self.model.get_cell_data(self.current_cell_index)
        if cell_data is not None:
            self.cell_ratio = cell_data.get('ratio', 0.75)
            # Create a new cell image set from the updated cell data.
            self.cell_image_set = load_cell_image_set(self.model.csv_path, cell_data, n_frames=2, box_size=150)
            total_cells = self.model.total_filtered()
            # Create a new CellImageView and its controller with the updated data.
            self.cell_image_view = CellImageView(n_frames=2, cell_number=self.current_cell_index+1,
                                                 total_cells=total_cells, cell_ratio=self.cell_ratio)
            self.cell_image_controller = CellImageController(self.cell_image_set,
                                                             cell_number=self.current_cell_index+1,
                                                             total_cells=total_cells,
                                                             cell_ratio=self.cell_ratio,
                                                             data_df=self.model.df)
            # Reconnect the back signal.
            self.cell_image_view.backClicked.connect(self.on_back_to_histo)
            # Replace the cell image view widget in the stack.
            self.stack.removeWidget(self.stack.widget(1))
            self.stack.addWidget(self.cell_image_view.centralWidget())
            self.stack.setCurrentIndex(1)
