from pathlib import Path

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget



class CsvPathDialog(QDialog):
    """Simple dialog to choose or paste the CSV path before launching the app."""

    def __init__(self, n_frames: int = 2, crop_size: int = 151, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select CellTinder CSV")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select or paste the CSV file path:"))

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("/path/to/cell_data.csv")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_button)
        layout.addLayout(path_row)

        form_layout = QFormLayout()
        self.n_frames_spin = QSpinBox()
        self.n_frames_spin.setRange(1, 999)
        self.n_frames_spin.setValue(n_frames)
        self.crop_size_spin = QSpinBox()
        self.crop_size_spin.setRange(1, 10000)
        self.crop_size_spin.setValue(crop_size)
        form_layout.addRow("n_frames", self.n_frames_spin)
        form_layout.addRow("crop_size", self.crop_size_spin)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV file",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if selected_path:
            self.path_edit.setText(selected_path)

    def selected_path(self) -> Path | None:
        text = self.path_edit.text().strip()
        if not text:
            return None
        return Path(text).expanduser()

    def selected_values(self) -> tuple[Path | None, int, int]:
        return self.selected_path(), self.n_frames_spin.value(), self.crop_size_spin.value()


def prompt_for_csv_path(n_frames: int = 2, crop_size: int = 151, parent: QWidget | None = None) -> tuple[Path | None, int, int] | None:
    dialog = CsvPathDialog(n_frames=n_frames, crop_size=crop_size, parent=parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_values()