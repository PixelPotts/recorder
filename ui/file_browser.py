"""File browser listing WAV files from the wavs/ directory."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QPushButton, QListWidgetItem,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen


def _make_wave_icon(size: int = 18) -> QIcon:
    """Draw a small waveform icon."""
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(0, 200, 160))
    pen.setWidth(2)
    p.setPen(pen)
    mid = size // 2
    # Simple waveform squiggle
    points = [(2, mid), (4, mid - 4), (6, mid + 3), (8, mid - 5),
              (10, mid + 4), (12, mid - 3), (14, mid + 2), (16, mid)]
    for i in range(len(points) - 1):
        p.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
    p.end()
    return QIcon(pix)


HEADER_STYLE = """
    QLabel {
        color: #8899aa;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 0;
    }
"""

ADD_BTN_STYLE = """
    QPushButton {
        background: transparent;
        color: #8899aa;
        border: 1px solid #1a3050;
        border-radius: 3px;
        font-size: 14px;
        font-weight: bold;
        padding: 0;
    }
    QPushButton:hover { color: #00d4aa; border-color: #00d4aa; }
"""

LIST_STYLE = """
    QListWidget {
        background: #0a1520;
        color: #bec8d2;
        border: none;
        font-size: 13px;
        outline: none;
    }
    QListWidget::item {
        padding: 4px 6px;
        border: none;
    }
    QListWidget::item:selected {
        background: #0f3d3a;
        color: #4aecd4;
    }
    QListWidget::item:hover:!selected {
        background: #112233;
    }
"""


class FileBrowser(QWidget):
    """Lists .wav files in the wavs/ directory. Emits signal on selection."""

    file_selected = pyqtSignal(str)  # full path

    def __init__(self, wavs_dir: str, parent=None):
        super().__init__(parent)
        self.wavs_dir = wavs_dir
        self._wave_icon = _make_wave_icon()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(4)

        # Header row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("FILES")
        self._label.setStyleSheet(HEADER_STYLE)
        header_row.addWidget(self._label)

        header_row.addStretch()

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(20, 20)
        self._add_btn.setStyleSheet(ADD_BTN_STYLE)
        self._add_btn.setToolTip("Open file")
        header_row.addWidget(self._add_btn)

        layout.addLayout(header_row)

        self._list = QListWidget()
        self._list.setStyleSheet(LIST_STYLE)
        self._list.setIconSize(QSize(18, 18))
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
            item = QListWidgetItem(self._wave_icon, f)
            self._list.addItem(item)

    def _on_item_clicked(self, item):
        name = item.text()
        full_path = os.path.join(self.wavs_dir, name)
        self.file_selected.emit(full_path)
