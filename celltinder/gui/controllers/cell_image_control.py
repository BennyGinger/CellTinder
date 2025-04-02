from PIL import Image, ImageQt
from PyQt6.QtGui import QPixmap

from backend.data_loader import DataLoader
from gui.views.cell_image_view import CellImageView


class CellImageController:
    def __init__(self, data_loader: DataLoader, view: CellImageView) -> None:
        
        
        self.data = data_loader
        self.data.add_process_col()
        self.df = self.data.pos_df
        # Starting index for the positive cells
        self.current_idx = 0
        self.current_frame = 1            

        # Setup view and connect signals...
        self.view = view
        self.view.previousCellClicked.connect(self.on_previous_cell)
        self.view.skipCellClicked.connect(self.on_skip_cell)
        self.view.keepCellClicked.connect(self.on_keep_cell)
        self.view.processCellsClicked.connect(self.on_process_cells)
        self.view.frameChanged.connect(self.on_frame_changed)
        self.view.overlayToggled.connect(self.on_overlay_toggled)


        # Load the first cell using its index from the df.
        self._load_cell()

    def _load_cell(self) -> None:
        """Load the current cell based on the current index."""
        
        # Use the DataLoader to fetch the images and masks for the current cell.
        cell_image_set = self.data.loads_arrays(self.current_idx)
        # Update the view with new cell info.
        self.current_cell = cell_image_set
        self._update_view()
        
    def _update_view(self) -> None:
        """Update the view with the current cell information."""
        
        cell_ratio = self.df['ratio'].iloc[self.current_idx]
        self.view.set_cell_info(self.current_idx, self.total_cells, cell_ratio)
        self._update_image()

    def _update_image(self) -> None:
        """Update the image displayed in the view. If overlay is enabled, then overlay the mask array on top of the image."""
        
        img_array = self.current_cell.imgs[self.current_frame]
        base_pil = Image.fromarray(img_array)
        
        # Check if the overlay is enabled
        if getattr(self, "overlay_enabled", False):
            # Retrieve the corresponding mask array
            mask_array = self.current_cell.masks[self.current_frame]
            mask_pil = Image.fromarray(mask_array).convert("L")
            # Convert image to RGBA for blending
            base_rgba = base_pil.convert("RGBA")
            overlay = Image.new("RGBA", base_rgba.size, (255, 0, 0, 100))
            # Composite the overlay using the mask as the transparency map.
            blended = Image.composite(overlay, base_rgba, mask_pil)
            final_img = Image.alpha_composite(base_rgba, blended)
        else:
            final_img = base_pil
        
        qimage = ImageQt.ImageQt(final_img)
        pixmap = QPixmap.fromImage(qimage)
        self.view.setImage(pixmap)
    
    def on_frame_changed(self, frame: int) -> None:
        """Handle the event when the frame slider is changed. Update the current frame and refresh the image."""
        
        self.current_frame = frame
        self._update_image()

    def on_overlay_toggled(self, enabled: bool) -> None:
        """Handle the event when the overlay checkbox is toggled. Update the overlay status and refresh the image."""
        
        self.overlay_enabled = enabled
        self._update_image()
    
    def on_previous_cell(self) -> None:
        """Handle the event when the previous cell button is clicked. If the current index is greater than 0, decrement the index and load the previous cell."""
        
        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_cell()

    def on_skip_cell(self) -> None:
        """Handle the event when the skip cell button is clicked. Move to the next cell."""
        
        self._move_to_next_cell()

    def on_keep_cell(self) -> None:
        """Handle the event when the keep cell button is clicked. Mark the current cell for processing. Then move to the next cell."""
        
        # Mark current cell for processing.
        self.df.iloc[self.current_idx, self.df.columns.get_loc('process')] = True
        self._move_to_next_cell()

    def _move_to_next_cell(self) -> None:
        """Move to the next cell in the DataFrame. If at the end, loop back to the start."""
        
        if self.current_idx < len(self.df) - 1:
            self.current_idx += 1
        else:
            self.current_idx = 0
        self._load_cell()

    def on_process_cells(self) -> None:
        """Handle the event when the process cells button is clicked. This will finalize the process by updating the cell to process in the DataFrame and saving the modify CSV. It will then close the view."""
        
        # Finalize the process, for example saving the DataFrame.
        self.data.update_cell_to_process_in_df(self.df)
        self.data.save_csv()
        self.view.close()

    @property
    def total_cells(self) -> int:
        """Get the total number of positive cells."""
        return len(self.df)