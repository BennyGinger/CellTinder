from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from celltinder.backend.cell_image_set import CellImageSet

# FIXME: Modify the column names when calling the data, according to the changes in gem_screening
# Define constants for column names
RATIO = 'ratio'
F_MINUS_F0 = 'F-F0'
DF_LABEL = 'DF'
F0 = 'before_stim'
F0_LABEL = 'F0'
VALID_CELL = 'valid_cell'
CELL_LABEL = 'cell_numb'
FOV_ID = 'fov_ID'  # Changed from 'fov_ID' to match gem_screening output
CENTROID_X = 'centroid_x'
CENTROID_Y = 'centroid_y'
BEFORE_STIM = 'before_stim'
AFTER_STIM = 'after_stim'
PROCESS = 'process'
TIFF_SUFFIXES = ('.tif', '.tiff')

class DataLoader:
    """
    Class to load and filter data from a CSV file. Specific to your our pipeline.
    """
    
    def __init__(self, csv_file: Path, n_frames: int, crop_size: int) -> None:
        """Initialize the LoadData object with a CSV file."""
        
        self.n_frames = n_frames
        self.crop_size = crop_size
        
        self.csv_path: Path = csv_file
        self._tiff_path_cache: dict[tuple[str, str], list[Path]] = {}
        self.df = pd.read_csv(csv_file)
        if 'Unnamed: 0' in self.df.columns:
            self.df.drop(columns=['Unnamed: 0'], inplace=True)
        self.ensure_ff0_column()
        self.ratios = self.df[RATIO]
        self.ff0 = self.df[F_MINUS_F0] if F_MINUS_F0 in self.df.columns else pd.Series(dtype=float)
        
        # Set default thresholds
        self.load_threshold_bounds(RATIO)
        self.load_threshold_bounds(F_MINUS_F0)
        self.load_threshold_bounds(F0)

    def filter_ratio(self, lower: float, upper: float, col_name: str = 'ratio') -> pd.DataFrame:
        """
        Filter the data based on the lower and upper thresholds.
        Args:
            lower: Lower threshold
            upper: Upper threshold
            col_name: Column name to filter on
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        return self.df[(self.df[col_name] >= lower) & (self.df[col_name] <= upper)]

    def get_cell_count(self, lower: float, upper: float, col_name: str = RATIO) -> int:
        """
        Get the cell count based on the lower and upper thresholds.
        Args:
            lower: Lower threshold
            upper: Upper threshold
            col_name: Column name used for thresholding
        Returns:
            int: Number of cells within the thresholds
        """
        filtered = self.filter_ratio(lower, upper, col_name=col_name)
        return len(filtered)

    def get_metric_values(self, col_name: str) -> pd.Series:
        """Return values for a metric column used in the histogram."""
        return self.df[col_name]

    def has_metric(self, col_name: str) -> bool:
        """Return whether a metric column exists in the DataFrame."""
        return col_name in self.df.columns

    def get_default_bounds(self, col_name: str) -> tuple[float, float]:
        """Return min and max defaults for a metric column."""
        values = self.df[col_name]
        return float(values.min()), float(values.max())

    def threshold_column_name(self, metric: str, lower: float, upper: float) -> str:
        """Build persisted threshold column names for each metric."""
        if metric == RATIO:
            return f"{lower:.2f}<ratio<{upper:.2f}"
        if metric == F_MINUS_F0:
            return f"{lower:.2f}<{DF_LABEL}<{upper:.2f}"
        if metric == F0:
            return f"{lower:.2f}<{F0_LABEL}<{upper:.2f}"
        raise ValueError(f"Unsupported metric: {metric}")

    def threshold_column_candidates(self, metric: str) -> list[str]:
        """Return all threshold columns in the dataframe for a metric."""
        if metric == RATIO:
            return [c for c in self.df.columns if '<ratio<' in c or '< x <' in c]
        if metric == F_MINUS_F0:
            return [c for c in self.df.columns if f'<{DF_LABEL}<' in c]
        if metric == F0:
            return [c for c in self.df.columns if f'<{F0_LABEL}<' in c]
        return []

    def apply_thresholds(
        self,
        ratio_lower: float,
        ratio_upper: float,
        df_lower: float,
        df_upper: float,
        f0_lower: float,
        f0_upper: float,
        persist: bool = False,
    ) -> int:
        """
        Create/update threshold columns and valid_cell using current bounds.
        Returns the number of valid cells.
        """
        ratio_col = self.threshold_column_name(RATIO, ratio_lower, ratio_upper)
        df_col = self.threshold_column_name(F_MINUS_F0, df_lower, df_upper)
        f0_col = self.threshold_column_name(F0, f0_lower, f0_upper)

        for col in self.threshold_column_candidates(RATIO):
            if col != ratio_col:
                self.df.drop(columns=[col], inplace=True)
        for col in self.threshold_column_candidates(F_MINUS_F0):
            if col != df_col:
                self.df.drop(columns=[col], inplace=True)
        for col in self.threshold_column_candidates(F0):
            if col != f0_col:
                self.df.drop(columns=[col], inplace=True)

        self.df[ratio_col] = self.df[RATIO].apply(lambda x: ratio_lower < x < ratio_upper)

        if self.has_metric(F_MINUS_F0):
            self.df[df_col] = self.df[F_MINUS_F0].apply(lambda x: df_lower < x < df_upper)
        else:
            self.df[df_col] = False

        if self.has_metric(F0):
            self.df[f0_col] = self.df[F0].apply(lambda x: f0_lower < x < f0_upper)
        else:
            self.df[f0_col] = False

        self.df[VALID_CELL] = self.df[ratio_col] & self.df[df_col] & self.df[f0_col]
        self.ratio_threshold_col = ratio_col
        self.df_threshold_col = df_col
        self.f0_threshold_col = f0_col

        if persist:
            self.save_csv()

        return int(self.df[VALID_CELL].sum())

    def ensure_ff0_column(self) -> None:
        """
        Ensure the F-F0 column exists in the CSV and DataFrame.
        F-F0 is computed as after_stim - before_stim.
        """
        if F_MINUS_F0 in self.df.columns:
            return
        if AFTER_STIM not in self.df.columns or BEFORE_STIM not in self.df.columns:
            return
        self.df[F_MINUS_F0] = self.df[AFTER_STIM] - self.df[BEFORE_STIM]
        self.save_csv()
    
    def save_csv(self) -> None:
        """
        Save the data to a new CSV file.
        """
        self.df.to_csv(self.csv_path, index=False)

    def loads_arrays(self, cell_idx: int, img_label: str = 'measure', mask_label: str = 'mask', refseg_label: str = 'refseg') -> CellImageSet:
        """
        Load and crop all images or masks for a specific cell.
        Supports both new CSV format (with path columns) and legacy format.
        
        Args:
            cell_idx: Index of the cell to load from the dataframe
            img_label: Label of the image files (used for legacy format)
            mask_label: Label of the mask files (used for legacy format)
        
        Returns:
            CellImageSet: A CellImageSet object containing the loaded and cropped images and masks
        """
        # Get the positive cells
        pos_df = self.pos_df
        
        # Extract cell specific parameters
        cell_centroid: tuple[float, float] = tuple(pos_df[[CENTROID_Y, CENTROID_X]].iloc[cell_idx].values)
        cell_mask_value = pos_df[CELL_LABEL].iloc[cell_idx]
        
        # Check if CSV has new format with path columns
        # img_cols = [col for col in pos_df.columns if col.endswith('_path') and 'img' in col]
        # mask_cols = [col for col in pos_df.columns if col.endswith('_path') and 'mask' in col]
        img_cols = []
        mask_cols = []
        
        if img_cols and mask_cols:
            # New format: extract paths from CSV
            img_paths = []
            refseg_paths = []
            mask_paths = []
            
            # Extract paths for this cell
            for col in img_cols:
                path_value = pos_df[col].iloc[cell_idx]
                if pd.notna(path_value):
                    img_paths.append(Path(path_value))
            
            for col in mask_cols:
                path_value = pos_df[col].iloc[cell_idx]
                if pd.notna(path_value):
                    mask_paths.append(Path(path_value))

            # Keep refseg aligned with measure images for legacy CSV path mode.
            refseg_paths = img_paths
            
            return CellImageSet(cell_centroid, img_paths, mask_paths, refseg_paths, cell_mask_value, self.crop_size)
        
        else:
            # Legacy format: discover files from current project structure.
            fov_id = pos_df[FOV_ID].iloc[cell_idx]

            img_paths = self._discover_tiff_paths(fov_id, img_label)
            refseg_paths = self._discover_tiff_paths(fov_id, refseg_label)
            mask_paths = self._discover_tiff_paths(fov_id, mask_label)

            if img_paths and mask_paths:
                if not refseg_paths:
                    refseg_paths = img_paths
                return CellImageSet(cell_centroid, img_paths, mask_paths, refseg_paths, cell_mask_value, self.crop_size)

            # Fallback to old directory-based loading when no files were discovered.
            img_dir, mask_dir = self._build_image_mask_dirs(fov_id)
            pre_img_path = img_dir.joinpath(f"{fov_id}_{img_label}.tif")
            pre_refseg_path = img_dir.joinpath(f"{fov_id}_{refseg_label}.tif")
            pre_mask_path = mask_dir.joinpath(f"{fov_id}_{mask_label}.tif")

            return CellImageSet(cell_centroid, pre_img_path, pre_mask_path, pre_refseg_path, cell_mask_value, self.n_frames, self.crop_size)

    def _discover_tiff_paths(self, fov_id: str, label: str) -> list[Path]:
        """
        Discover TIFF files from well-specific folders, with caching.

        Expected filename format: {fov_id}_{label}_{frame}.tif(f), where label can
        be 'measure', 'refseg', or 'mask'.
        """
        cache_key = (str(fov_id), label.lower())
        if cache_key in self._tiff_path_cache:
            return self._tiff_path_cache[cache_key]

        base_path = self.csv_path.parent
        fov_id = str(fov_id)
        well_id = self._extract_well_id(fov_id)
        label = label.lower()
        frame_pattern = re.compile(
            rf"^{re.escape(fov_id)}_{re.escape(label)}_(\d+)\.(?:tif|tiff)$",
            re.IGNORECASE,
        )

        # New expected structure is <csv_parent>/well/<well>/<well>_images|<well>_masks.
        suffix = 'masks' if label == 'mask' else 'images'
        candidate_dirs = [
            base_path.joinpath('well', well_id, f"{well_id}_{suffix}"),
            base_path.joinpath(well_id, f"{well_id}_{suffix}"),
        ]

        discovered: list[tuple[int, Path]] = []
        for candidate_dir in candidate_dirs:
            if not candidate_dir.exists() or not candidate_dir.is_dir():
                continue
            for path in candidate_dir.iterdir():
                if not path.is_file() or path.suffix.lower() not in TIFF_SUFFIXES:
                    continue

                match = frame_pattern.match(path.name)
                if match is None:
                    continue

                discovered.append((int(match.group(1)), path))

            if discovered:
                break

        # Fallback for compatibility with unexpected layouts.
        if not discovered:
            for path in base_path.rglob(f"{fov_id}_{label}_*"):
                if not path.is_file() or path.suffix.lower() not in TIFF_SUFFIXES:
                    continue

                match = frame_pattern.match(path.name)
                if match is None:
                    continue

                discovered.append((int(match.group(1)), path))

        discovered.sort(key=lambda item: item[0])
        result = [path for _, path in discovered]
        self._tiff_path_cache[cache_key] = result
        return result

    @staticmethod
    def _extract_well_id(fov_id: str) -> str:
        """Extract well ID from fov_id for both old and new naming formats."""
        if '_P' in fov_id:
            return fov_id.split('_P')[0]
        return fov_id.split('P')[0]

    def _build_image_mask_dirs(self, fov_id: str) -> tuple[Path, Path]:
        """
        Build the image and mask directories based on the fov_id (legacy support).
        """
        # Build the folder names
        # Extract well ID from fov_id, handling both formats:
        # Old format: A1_P1 -> A1
        # New format: A1P1 -> A1
        if '_P' in fov_id:
            well_ID = fov_id.split('_P')[0]
        else:
            well_ID = fov_id.split('P')[0]
        img_folder_name = f"{well_ID}_images"
        mask_folder_name = f"{well_ID}_masks"
        # Build the folder paths
        project_path = self.csv_path.parent
        img_path = project_path.joinpath(img_folder_name)
        mask_path = project_path.joinpath(mask_folder_name)
        return img_path, mask_path

    def add_process_col(self) -> None:
        """Add a PROCESS column to the DataFrame."""
        
        if PROCESS not in self.df.columns:
            self.df[PROCESS] = False
    
    def update_cell_to_process_in_df(self, pos_df: pd.DataFrame) -> None:
        """Update the DataFrame with the cells to process."""
        
        self.df.update(pos_df)
    
    def load_threshold_bounds(self, metric: str = RATIO) -> tuple[float, float]:
        """
        Load threshold bounds from persisted threshold columns per metric.
        Falls back to metric min/max when no matching threshold column is present.
        """
        if metric == RATIO:
            pattern = r"([\d\.]+)\s*<\s*ratio\s*<\s*([\d\.]+)"
            legacy_pattern = r"([\d\.]+)\s*<\s*x\s*<\s*([\d\.]+)"
            cols = self.threshold_column_candidates(RATIO)
            lower, upper = self.get_default_bounds(RATIO)
            col_name = None

            if cols:
                col_name = cols[0]
                m = re.match(pattern, col_name)
                if m is None:
                    m = re.match(legacy_pattern, col_name)
                if m:
                    lower, upper = float(m.group(1)), float(m.group(2))

            self.lower, self.upper, self.column_thresholds = lower, upper, col_name
            self.ratio_threshold_col = col_name
            return lower, upper

        if metric == F_MINUS_F0 and self.has_metric(F_MINUS_F0):
            pattern = rf"([\d\.]+)\s*<\s*{DF_LABEL}\s*<\s*([\d\.]+)"
            cols = self.threshold_column_candidates(F_MINUS_F0)
            lower, upper = self.get_default_bounds(F_MINUS_F0)
            col_name = None

            if cols:
                col_name = cols[0]
                m = re.match(pattern, col_name)
                if m:
                    lower, upper = float(m.group(1)), float(m.group(2))

            self.df_lower, self.df_upper = lower, upper
            self.df_threshold_col = col_name
            return lower, upper

        if metric == F_MINUS_F0:
            return 0.0, 1.0

        if metric == F0 and self.has_metric(F0):
            pattern = rf"([\d\.]+)\s*<\s*{F0_LABEL}\s*<\s*([\d\.]+)"
            cols = self.threshold_column_candidates(F0)
            lower, upper = self.get_default_bounds(F0)
            col_name = None

            if cols:
                col_name = cols[0]
                m = re.match(pattern, col_name)
                if m:
                    lower, upper = float(m.group(1)), float(m.group(2))

            self.f0_lower, self.f0_upper = lower, upper
            self.f0_threshold_col = col_name
            return lower, upper

        if metric == F0:
            return 0.0, 1.0

        raise ValueError(f"Unsupported metric: {metric}")
    
    @property
    def default_lower(self) -> float:
        """Return the default lower threshold."""
        return self.ratios.min()
    
    @property
    def default_upper(self) -> float:
        """Return the default upper threshold."""
        return self.ratios.max()
    
    @property
    def pos_df(self) -> pd.DataFrame:
        """Return the DataFrame containing positive cells sorted by ratio."""
        if VALID_CELL in self.df.columns:
            return self.df.loc[self.df[VALID_CELL] == True].sort_values(by='ratio', ascending=False)
        if hasattr(self, 'column_thresholds') and self.column_thresholds is not None:
            return self.df.loc[self.df[self.column_thresholds] == True].sort_values(by='ratio', ascending=False)
        raise ValueError("No valid_cell or threshold column found. Please set thresholds first.")
