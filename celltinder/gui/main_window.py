from pathlib import Path

from PyQt6.QtWidgets import QStackedWidget, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CellTinder GUI")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)


# class MainWindow(QMainWindow):
#     """Main window for the CellTinder GUI application."""
    
#     def __init__(self, csv_path: Path):
#         super().__init__()
#         self.setWindowTitle("CellTinder GUI")
        
#         # Create a stacked widget to hold the different views.
#         self.stack = QStackedWidget()
#         self.setCentralWidget(self.stack)
        
#         # --- Histogram View Setup ---
#         self.data = DataLoader(csv_path)
#         self.histo_view = HistogramView()
#         self.histo_controller = HistogramController(self.data, self.histo_view)
        
#         # --- Cell Image View Setup ---
#         # Extract the cell data
#         pos_df = self.data.pos_df
#         print(f"Number of cells: {len(pos_df)}")
#         cell_idx = 0
#         cell_data = pos_df.iloc[cell_idx]
#         cell_ratio = cell_data['ratio']
#         cell_image_set = self.data.loads_arrays(cell_idx=0)
        
#         # Create the cell image set and controller.
#         self.cell_image_view = CellImageView(n_frames=2, cell_number=cell_idx+1, total_cells=len(pos_df), cell_ratio=cell_ratio)
#         self.cell_image_controller = CellImageController(cell_image_set,
#                                                          cell_number=cell_idx+1,
#                                                          total_cells=len(pos_df),
#                                                          cell_ratio=cell_ratio,
#                                                          data_df=pos_df)
        
#         # Add the central widgets (from each QMainWindow) to the stack.
#         # Note: We use centralWidget() so that the inner widget is added.
#         self.stack.addWidget(self.histo_view.centralWidget())  # index 0: histogram view
#         self.stack.addWidget(self.cell_image_view.centralWidget())  # index 1: cell image view
        
#         # --- Navigation: connect the signals for switching views ---
#         # When "Next" is pressed in the histogram view, show the cell image view.
#         self.histo_view.next_button.clicked.connect(self.show_cell_image_view)
#         # When "Back to histo gui" is pressed in the cell image view, return to the histogram view.
#         self.cell_image_view.backClicked.connect(self.show_histo_view)
    
#     def show_cell_image_view(self):
#         self.stack.setCurrentIndex(1)
    
#     def show_histo_view(self):
#         self.stack.setCurrentIndex(0)