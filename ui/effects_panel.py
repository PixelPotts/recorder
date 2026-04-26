"""Effects panel with 10 QDials and labels."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QDial, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal


class EffectKnob(QWidget):
    """Single labeled dial for one effect parameter."""

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
        self._label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self._label)

        self._dial = QDial()
        self._dial.setRange(0, 1000)
        self._dial.setNotchesVisible(True)
        self._dial.setFixedSize(40, 40)
        self._dial.setStyleSheet("QDial { background: #2a2a2a; }")
        # Set default position
        default_pos = int((default_val - min_val) / (max_val - min_val) * 1000)
        self._dial.setValue(max(0, min(1000, default_pos)))
        self._dial.valueChanged.connect(self._on_changed)
        layout.addWidget(self._dial, alignment=Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel(self._format(default_val))
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._value_label)

    def mapped_value(self) -> float:
        raw = self._dial.value() / 1000.0
        return self.min_val + raw * (self.max_val - self.min_val)

    def set_mapped_value(self, val: float):
        pos = int((val - self.min_val) / (self.max_val - self.min_val) * 1000)
        self._dial.setValue(max(0, min(1000, pos)))

    def _format(self, val: float) -> str:
        return f"{val:.{self.decimals}f}{self.unit}"

    def _on_changed(self, _):
        val = self.mapped_value()
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
    """Grid of 10 effect knobs."""

    effect_changed = pyqtSignal(str, float)  # param_key, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self._knobs: dict[str, EffectKnob] = {}
        self._setup_ui()

    def _setup_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(2)

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
