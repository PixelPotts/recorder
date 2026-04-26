"""Play/Record/Stop buttons and time display."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

BUTTON_STYLE = """
    QPushButton {
        background: #2a2a2a;
        color: #ccc;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        min-width: 70px;
    }
    QPushButton:hover { background: #3a3a3a; }
    QPushButton:pressed { background: #444; }
"""

RECORD_ACTIVE_STYLE = """
    QPushButton {
        background: #8b0000;
        color: #fff;
        border: 1px solid #a00;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        min-width: 70px;
    }
"""

PLAY_ACTIVE_STYLE = """
    QPushButton {
        background: #006400;
        color: #fff;
        border: 1px solid #0a0;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        min-width: 70px;
    }
"""


class TransportControls(QWidget):
    """Transport bar with record/play/stop and time display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.btn_record = QPushButton("Record")
        self.btn_record.setStyleSheet(BUTTON_STYLE)
        layout.addWidget(self.btn_record)

        self.btn_play = QPushButton("Play")
        self.btn_play.setStyleSheet(BUTTON_STYLE)
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet(BUTTON_STYLE)
        layout.addWidget(self.btn_stop)

        layout.addStretch()

        self.time_label = QLabel("0:00.000 / 0:00.000")
        self.time_label.setStyleSheet("color: #aaa; font-family: monospace; font-size: 14px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.time_label)

    def set_recording(self, active: bool):
        self.btn_record.setStyleSheet(RECORD_ACTIVE_STYLE if active else BUTTON_STYLE)

    def set_playing(self, active: bool):
        self.btn_play.setStyleSheet(PLAY_ACTIVE_STYLE if active else BUTTON_STYLE)

    def update_time(self, current_sec: float, total_sec: float):
        self.time_label.setText(f"{self._fmt(current_sec)} / {self._fmt(total_sec)}")

    @staticmethod
    def _fmt(sec: float) -> str:
        m = int(sec) // 60
        s = sec - m * 60
        return f"{m}:{s:06.3f}"
