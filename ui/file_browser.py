"""File browser listing WAV files from the wavs/ directory."""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel
from PyQt6.QtCore import pyqtSignal


class FileBrowser(QWidget):
    """Lists .wav files in the wavs/ directory. Emits signal on selection."""

    file_selected = pyqtSignal(str)  # full path

    def __init__(self, wavs_dir: str, parent=None):
        super().__init__(parent)
        self.wavs_dir = wavs_dir
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._label = QLabel("Files")
        self._label.setStyleSheet("color: #aaa; font-weight: bold; padding: 2px;")
        layout.addWidget(self._label)

        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                color: #ccc;
                border: 1px solid #333;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background: #264f78;
            }
            QListWidget::item:hover {
                background: #2a2d2e;
            }
        """)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def refresh(self):
        self._list.clear()
        if not os.path.isdir(self.wavs_dir):
            return
        files = sorted(
            f for f in os.listdir(self.wavs_dir)
            if f.lower().endswith(".wav")
        )
        for f in files:
            self._list.addItem(f)

    def _on_item_clicked(self, item):
        name = item.text()
        full_path = os.path.join(self.wavs_dir, name)
        self.file_selected.emit(full_path)
