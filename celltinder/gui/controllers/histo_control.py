from celltinder.backend.load_data import LoadData
from celltinder.gui.views.histo_view import HistogramView


class HistogramController:
    def __init__(self, model: LoadData, view: HistogramView):
        self.model = model
        self.view = view
        
        # Set default threshold values in the view
        self.view.lower_edit.setText(str(round(self.model.default_lower, 2)))
        self.view.upper_edit.setText(str(round(self.model.default_upper, 2)))
        
        # Initialize display with current cell count
        initial_count = self.model.get_cell_count(self.model.default_lower, self.model.default_upper)
        self.view.update_count(initial_count)
        
        # Connect view signals to controller methods
        self.view.lower_edit.textChanged.connect(self.on_threshold_change)
        self.view.upper_edit.textChanged.connect(self.on_threshold_change)
        self.view.next_button.clicked.connect(self.on_next_pressed)
        
        # Draw the initial plot
        self.view.update_plot(self.model.default_lower, self.model.default_upper, self.model.ratios)
    
    def on_threshold_change(self):
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        count = self.model.get_cell_count(lower_val, upper_val)
        self.view.update_count(count)
        self.view.update_plot(lower_val, upper_val, self.model.ratios)

    def on_next_pressed(self):
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        column_name = f"{lower_val} < x < {upper_val}"
        self.model.df[column_name] = self.model.df['ratio'].apply(lambda x: lower_val < x < upper_val)
        print(f"New column '{column_name}' added to the DataFrame.")
        self.model.save_csv()
        # Optionally: move to the next step in the workflow
