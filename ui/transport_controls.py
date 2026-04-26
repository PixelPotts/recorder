"""Play/Record/Stop icon buttons and time display."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPainter, QColor, QPixmap, QPainterPath


def _make_icon(shape: str, color: QColor, size: int = 32) -> QIcon:
    """Draw simple transport icons as pixmaps."""
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    m = 6  # margin
    if shape == "record":
        r = (size - 2 * m) // 2
        p.drawEllipse(size // 2 - r, size // 2 - r, r * 2, r * 2)
    elif shape == "play":
        path = QPainterPath()
        path.moveTo(m + 2, m)
        path.lineTo(size - m, size // 2)
        path.lineTo(m + 2, size - m)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "stop":
        s = size - 2 * m
        p.drawRect(m, m, s, s)
    p.end()
    return QIcon(pix)


ICON_BTN_STYLE = """
    QPushButton {
        background: #2a2a2a;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 4px;
    }
    QPushButton:hover { background: #3a3a3a; }
    QPushButton:pressed { background: #444; }
"""

RECORD_ACTIVE_STYLE = """
    QPushButton {
        background: #8b0000;
        border: 1px solid #a00;
        border-radius: 4px;
        padding: 4px;
    }
"""

PLAY_ACTIVE_STYLE = """
    QPushButton {
        background: #006400;
        border: 1px solid #0a0;
        border-radius: 4px;
        padding: 4px;
    }
"""


class TransportControls(QWidget):
    """Transport bar with record/play/stop icons and time display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        icon_size = QSize(28, 28)

        self.btn_record = QPushButton()
        self.btn_record.setIcon(_make_icon("record", QColor(220, 40, 40)))
        self.btn_record.setIconSize(icon_size)
        self.btn_record.setFixedSize(38, 38)
        self.btn_record.setStyleSheet(ICON_BTN_STYLE)
        self.btn_record.setToolTip("Record (hold Space)")
        layout.addWidget(self.btn_record)

        self.btn_play = QPushButton()
        self.btn_play.setIcon(_make_icon("play", QColor(60, 200, 60)))
        self.btn_play.setIconSize(icon_size)
        self.btn_play.setFixedSize(38, 38)
        self.btn_play.setStyleSheet(ICON_BTN_STYLE)
        self.btn_play.setToolTip("Play (Enter)")
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(_make_icon("stop", QColor(180, 180, 180)))
        self.btn_stop.setIconSize(icon_size)
        self.btn_stop.setFixedSize(38, 38)
        self.btn_stop.setStyleSheet(ICON_BTN_STYLE)
        self.btn_stop.setToolTip("Stop")
        layout.addWidget(self.btn_stop)

        layout.addStretch()

        self.time_label = QLabel("0:00.000 / 0:00.000")
        self.time_label.setStyleSheet("color: #aaa; font-family: monospace; font-size: 14px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.time_label)

    def set_recording(self, active: bool):
        self.btn_record.setStyleSheet(RECORD_ACTIVE_STYLE if active else ICON_BTN_STYLE)

    def set_playing(self, active: bool):
        self.btn_play.setStyleSheet(PLAY_ACTIVE_STYLE if active else ICON_BTN_STYLE)

    def update_time(self, current_sec: float, total_sec: float):
        self.time_label.setText(f"{self._fmt(current_sec)} / {self._fmt(total_sec)}")

    @staticmethod
    def _fmt(sec: float) -> str:
        m = int(sec) // 60
        s = sec - m * 60
        return f"{m}:{s:06.3f}"
