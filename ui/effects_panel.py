"""Effects panel with custom-painted knobs and labels."""

import math
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QConicalGradient, QMouseEvent


class KnobWidget(QWidget):
    """Custom-painted rotary knob with cyan accent arc."""

    value_changed = pyqtSignal(float)  # 0.0 - 1.0

    # Arc range: 225° to -45° (270° sweep), measured from Qt's 0=3 o'clock
    ARC_START = 225  # degrees
    ARC_SPAN = 270   # degrees

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.5
        self._dragging = False
        self._drag_start_y = 0
        self._drag_start_val = 0.0
        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float):
        self._value = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 3

        # Outer ring (dark)
        p.setPen(QPen(QColor(30, 50, 70), 2))
        p.setBrush(QColor(15, 25, 38))
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Inner knob body
        inner_r = radius - 5
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(25, 40, 55))
        p.drawEllipse(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2))

        # Value arc (cyan glow)
        arc_rect = QRectF(cx - radius + 1, cy - radius + 1,
                          (radius - 1) * 2, (radius - 1) * 2)
        value_span = self._value * self.ARC_SPAN
        arc_pen = QPen(QColor(0, 210, 180), 3)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        # Qt arcs: start angle in 1/16 degree, positive = counter-clockwise
        start_16 = int(self.ARC_START * 16)
        span_16 = int(-value_span * 16)
        p.drawArc(arc_rect, start_16, span_16)

        # Indicator line
        angle_deg = self.ARC_START - self._value * self.ARC_SPAN
        angle_rad = math.radians(angle_deg)
        line_inner = inner_r * 0.35
        line_outer = inner_r * 0.75
        x1 = cx + line_inner * math.cos(angle_rad)
        y1 = cy - line_inner * math.sin(angle_rad)
        x2 = cx + line_outer * math.cos(angle_rad)
        y2 = cy - line_outer * math.sin(angle_rad)
        p.setPen(QPen(QColor(200, 220, 240), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        p.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start_y = int(event.position().y())
            self._drag_start_val = self._value

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            dy = self._drag_start_y - int(event.position().y())
            sensitivity = 200.0
            new_val = self._drag_start_val + dy / sensitivity
            new_val = max(0.0, min(1.0, new_val))
            if new_val != self._value:
                self._value = new_val
                self.update()
                self.value_changed.emit(self._value)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        step = 0.02 if delta > 0 else -0.02
        new_val = max(0.0, min(1.0, self._value + step))
        if new_val != self._value:
            self._value = new_val
            self.update()
            self.value_changed.emit(self._value)


class EffectKnob(QWidget):
    """Single labeled knob for one effect parameter."""

    value_changed = pyqtSignal(str, float)  # param_key, mapped_value

    def __init__(self, label: str, param_key: str,
                 min_val: float, max_val: float, default_val: float,
                 unit: str = "", decimals: int = 1, parent=None):
        super().__init__(parent)
        self.param_key = param_key
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.decimals = decimals

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #7a8a9a; font-size: 10px;")
        layout.addWidget(self._label)

        self._knob = KnobWidget()
        default_pos = (default_val - min_val) / (max_val - min_val) if max_val != min_val else 0
        self._knob.value = max(0.0, min(1.0, default_pos))
        self._knob.value_changed.connect(self._on_changed)
        layout.addWidget(self._knob, alignment=Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel(self._format(default_val))
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet("color: #556677; font-size: 10px;")
        layout.addWidget(self._value_label)

    def mapped_value(self) -> float:
        return self.min_val + self._knob.value * (self.max_val - self.min_val)

    def set_mapped_value(self, val: float):
        if self.max_val != self.min_val:
            pos = (val - self.min_val) / (self.max_val - self.min_val)
            self._knob.value = max(0.0, min(1.0, pos))
        self._value_label.setText(self._format(val))

    def _format(self, val: float) -> str:
        return f"{val:.{self.decimals}f}{self.unit}"

    def _on_changed(self, norm_val: float):
        val = self.min_val + norm_val * (self.max_val - self.min_val)
        self._value_label.setText(self._format(val))
        self.value_changed.emit(self.param_key, val)


EFFECT_DEFS = [
    ("Gain",       "gain_db",           -24,     24, 0,    "dB", 1),
    ("Low-Pass",   "lowpass_hz",        200,  20000, 20000, "Hz", 0),
    ("High-Pass",  "highpass_hz",        20,   8000, 20,    "Hz", 0),
    ("Reverb",     "reverb_wet",          0,    100, 0,     "%",  0),
    ("Delay",      "delay_ms",            0,    500, 0,     "ms", 0),
    ("Compress",   "compressor_ratio",  1.0,   10.0, 1.0,   ":1", 1),
    ("Gate",       "gate_threshold_db",  -80,   -20, -80,   "dB", 0),
    ("Pitch",      "pitch_semitones",    -12,    12, 0,     "st", 1),
    ("Mid EQ",     "mid_eq_db",          -12,    12, 0,     "dB", 1),
    ("Normalize",  "normalize_pct",        0,   100, 0,     "%",  0),
]


class EffectsPanel(QWidget):
    """Row of 10 custom effect knobs."""

    effect_changed = pyqtSignal(str, float)  # param_key, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(105)
        self.setStyleSheet("background: #0a1520; border-top: 1px solid #1a3050;")
        self._knobs: dict[str, EffectKnob] = {}
        self._setup_ui()

    def _setup_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(4)

        for label, key, mn, mx, default, unit, dec in EFFECT_DEFS:
            knob = EffectKnob(label, key, mn, mx, default, unit, dec)
            knob.value_changed.connect(self._on_knob_changed)
            row.addWidget(knob)
            self._knobs[key] = knob

    def _on_knob_changed(self, key: str, val: float):
        self.effect_changed.emit(key, val)

    def set_params(self, params: dict):
        for key, knob in self._knobs.items():
            if key in params:
                knob.set_mapped_value(params[key])

    def get_params(self) -> dict:
        return {key: knob.mapped_value() for key, knob in self._knobs.items()}
