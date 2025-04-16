from celltinder.backend.data_loader import DataLoader
from celltinder.gui.views.histo_view import HistogramView


class HistogramController:
    def __init__(self, model: DataLoader, view: HistogramView):
        self.model = model
        self.view = view
        
        # Set default threshold values in the view
        self.view.lower_edit.setText(str(round(self.model.default_lower, 2)))
        self.view.upper_edit.setText(str(round(self.model.default_upper, 2)))
        
        # Initialize display with current cell count
        initial_count = self.model.get_cell_count(self.model.default_lower, self.model.default_upper)
        self.view.update_count(initial_count)
        
        # Connect view signals to controller methods
        self.view.lower_edit.editingFinished.connect(self.on_threshold_change)
        self.view.upper_edit.editingFinished.connect(self.on_threshold_change)
        self.view.next_button.clicked.connect(self.on_next_pressed)
        
        # Draw the initial plot
        self.view.update_plot(self.model.default_lower, self.model.default_upper, self.model.ratios)
    
    def on_threshold_change(self):
        """Update the cell count and plot when the threshold values change."""
        
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        count = self.model.get_cell_count(lower_val, upper_val)
        self.view.update_count(count)
        self.view.update_plot(lower_val, upper_val, self.model.ratios)

    def on_next_pressed(self):
        """Add a new column to the DataFrame based on the current threshold values."""
        
        # Get the threshold values from the view and create a column name
        lower_val, upper_val = self.view.get_threshold_values(self.model.default_lower, self.model.default_upper)
        column_name = f"{lower_val} < x < {upper_val}"
        
        # Find any column whose name contains "< x <", indicating a threshold column
        threshold_cols = [col for col in self.model.df.columns if "< x <" in col]
        
        if threshold_cols:
            # If found, drop them to ensure only one threshold column exists
            self.model.df.drop(columns=threshold_cols, inplace=True)
            print(f"Overwriting existing threshold columns {threshold_cols} with new column '{column_name}'.")
        else:
            print(f"New column '{column_name}' added to the DataFrame.")
            
        # Add a new column to the DataFrame based on the threshold values
        self.model.df[column_name] = self.model.df['ratio'].apply(lambda x: lower_val < x < upper_val)
        self.model.update_thresholds(lower_val, upper_val, column_name)
        self.model.save_csv()
        # Optionally: move to the next step in the workflow
