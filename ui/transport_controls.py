"""Play/Record/Stop circular buttons and time display."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPainter, QColor, QPixmap, QPainterPath, QPen


def _make_icon(shape: str, color: QColor, size: int = 28) -> QIcon:
    """Draw simple transport icons as pixmaps."""
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    m = 7
    if shape == "record":
        r = (size - 2 * m) // 2
        p.drawEllipse(size // 2 - r, size // 2 - r, r * 2, r * 2)
    elif shape == "play":
        path = QPainterPath()
        path.moveTo(m + 3, m)
        path.lineTo(size - m, size // 2)
        path.lineTo(m + 3, size - m)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "stop":
        s = size - 2 * m - 2
        p.drawRoundedRect(m + 1, m + 1, s, s, 2, 2)
    p.end()
    return QIcon(pix)


CIRCLE_BTN = """
    QPushButton {{
        background: transparent;
        border: 2px solid {border};
        border-radius: {radius}px;
        padding: 0;
    }}
    QPushButton:hover {{ background: rgba(255, 255, 255, 8); }}
    QPushButton:pressed {{ background: rgba(255, 255, 255, 15); }}
"""

RECORD_ACTIVE = """
    QPushButton {
        background: rgba(180, 30, 30, 40);
        border: 2px solid #cc3333;
        border-radius: 22px;
        padding: 0;
    }
"""

PLAY_ACTIVE = """
    QPushButton {
        background: rgba(0, 180, 160, 30);
        border: 2px solid #00b4a0;
        border-radius: 22px;
        padding: 0;
    }
"""


class TransportControls(QWidget):
    """Transport bar with circular record/play/stop icons and time display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet("background: #0d1b2a;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        btn_size = 44
        icon_size = QSize(24, 24)
        radius = btn_size // 2

        self.btn_record = QPushButton()
        self.btn_record.setIcon(_make_icon("record", QColor(220, 50, 50)))
        self.btn_record.setIconSize(icon_size)
        self.btn_record.setFixedSize(btn_size, btn_size)
        self._record_default_style = CIRCLE_BTN.format(border="#553333", radius=radius)
        self.btn_record.setStyleSheet(self._record_default_style)
        self.btn_record.setToolTip("Record (hold Space)")
        layout.addWidget(self.btn_record)

        self.btn_play = QPushButton()
        self.btn_play.setIcon(_make_icon("play", QColor(0, 200, 160)))
        self.btn_play.setIconSize(icon_size)
        self.btn_play.setFixedSize(btn_size, btn_size)
        self._play_default_style = CIRCLE_BTN.format(border="#2a4a4a", radius=radius)
        self.btn_play.setStyleSheet(self._play_default_style)
        self.btn_play.setToolTip("Play (Enter)")
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(_make_icon("stop", QColor(140, 150, 160)))
        self.btn_stop.setIconSize(icon_size)
        self.btn_stop.setFixedSize(btn_size, btn_size)
        self.btn_stop.setStyleSheet(CIRCLE_BTN.format(border="#333d48", radius=radius))
        self.btn_stop.setToolTip("Stop")
        layout.addWidget(self.btn_stop)

        layout.addStretch()

        # Time display: current in red/orange, total in gray
        self._current_time = QLabel("0:00.000")
        self._current_time.setStyleSheet(
            "color: #e85040; font-family: monospace; font-size: 16px; font-weight: bold;"
        )
        self._current_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._current_time)

        sep = QLabel("/")
        sep.setStyleSheet("color: #3a4a5a; font-family: monospace; font-size: 16px;")
        layout.addWidget(sep)

        self._total_time = QLabel("0:00.000")
        self._total_time.setStyleSheet(
            "color: #8899aa; font-family: monospace; font-size: 16px;"
        )
        self._total_time.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._total_time)

        # Keep old label ref for compat
        self.time_label = self._current_time

    def set_recording(self, active: bool):
        self.btn_record.setStyleSheet(RECORD_ACTIVE if active else self._record_default_style)

    def set_playing(self, active: bool):
        self.btn_play.setStyleSheet(PLAY_ACTIVE if active else self._play_default_style)

    def update_time(self, current_sec: float, total_sec: float):
        self._current_time.setText(self._fmt(current_sec))
        self._total_time.setText(self._fmt(total_sec))

    @staticmethod
    def _fmt(sec: float) -> str:
        m = int(sec) // 60
        s = sec - m * 60
        return f"{m}:{s:06.3f}"
