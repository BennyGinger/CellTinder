from pathlib import Path

import pandas as pd


class LoadData:
    """Class to load and filter data from a CSV file."""
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.csv_path: Path = csv_file
        self.df = pd.read_csv(csv_file)
        self.ratios = self.df['ratio']
        self.default_lower: float = self.ratios.min()
        self.default_upper: float = self.ratios.max()

    def filter_data(self, lower: float, upper: float) -> pd.DataFrame:
        """Filter the data based on the lower and upper thresholds."""
        
        return self.df[(self.df['ratio'] >= lower) & (self.df['ratio'] <= upper)]

    def get_cell_count(self, lower: float, upper: float) -> int:
        """Get the cell count based on the lower and upper thresholds."""
        
        filtered = self.filter_data(lower, upper)
        return len(filtered)
    
    def save_csv(self) -> None:
        """Save the data to a new CSV file."""
        
        self.df.to_csv(self.csv_path, index=False)
