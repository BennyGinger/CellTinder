from PyQt6.QtGui import QPixmap
from PIL import Image, ImageQt

from gui.views.cell_image_view import CellImageView


class CellImageController:
    def __init__(self, cell_image_set, cell_number, total_cells, cell_ratio, data_df):
        """
        Args:
            cell_image_set: Model instance (e.g. an instance of CellImageSet) holding image and mask arrays.
            cell_number: Identifier for the current cell.
            total_cells: Total number of cells.
            cell_ratio: Ratio or extra info for the current cell.
            data_df: A DataFrame to track processing decisions.
        """
        self.cell_image_set = cell_image_set
        self.cell_number = cell_number
        self.total_cells = total_cells
        self.cell_ratio = cell_ratio
        self.data_df = data_df

        self.n_frames = len(cell_image_set.imgs)
        self.current_frame = 1
        self.overlay_enabled = False

        # Create and set up the view.
        self.view = CellImageView(self.n_frames, cell_number, total_cells, cell_ratio)
        self.view.backClicked.connect(self.on_back)
        self.view.previousCellClicked.connect(self.on_previous_cell)
        self.view.skipCellClicked.connect(self.on_skip_cell)
        self.view.keepCellClicked.connect(self.on_keep_cell)
        self.view.processCellsClicked.connect(self.on_process_cells)
        self.view.frameChanged.connect(self.on_frame_changed)
        self.view.overlayToggled.connect(self.on_overlay_toggled)

        # Initial update.
        self.update_image()

    def update_image(self):
        # Get the image for the current frame.
        img_array = self.cell_image_set.imgs[self.current_frame]
        base_pil = Image.fromarray(img_array)

        if self.overlay_enabled:
            mask_array = self.cell_image_set.masks[self.current_frame]
            mask_pil = Image.fromarray(mask_array).convert("L")
            base_rgba = base_pil.convert("RGBA")
            overlay = Image.new("RGBA", base_rgba.size, (255, 0, 0, 100))
            blended = Image.composite(overlay, base_rgba, mask_pil)
            final_img = Image.alpha_composite(base_rgba, blended)
        else:
            final_img = base_pil

        # Convert the PIL image to a QPixmap.
        qimage = ImageQt.ImageQt(final_img)
        pixmap = QPixmap.fromImage(qimage)
        self.view.setImage(pixmap)

    def on_frame_changed(self, value):
        self.current_frame = value
        self.update_image()

    def on_overlay_toggled(self, enabled):
        self.overlay_enabled = enabled
        self.update_image()

    def on_back(self):
        print("Back to histo gui")
        self.view.close()

    def on_previous_cell(self):
        print("Previous cell pressed")
        # Insert logic to load the previous cell.
        
    def on_skip_cell(self):
        self.data_df.loc[self.cell_number, 'process'] = False
        print("Cell skipped")

    def on_keep_cell(self):
        self.data_df.loc[self.cell_number, 'process'] = True
        print("Cell kept")

    def on_process_cells(self):
        self.data_df.to_csv("cell_data.csv", index=False)
        print("Cells processed and data saved.")
        self.view.close()

    def show(self):
        self.view.show()

