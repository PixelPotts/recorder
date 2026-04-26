"""Left-side filter panel with collapsible sections and parameter sliders."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from audio.filters import FILTER_DEFS

HEADER_STYLE = """
    QPushButton {
        background: #2a2a2a;
        color: #bbb;
        border: none;
        border-bottom: 1px solid #333;
        text-align: left;
        padding: 5px 8px;
        font-size: 12px;
    }
    QPushButton:hover { background: #333; }
"""

APPLY_STYLE = """
    QPushButton {
        background: #264f78;
        color: #ddd;
        border: none;
        border-radius: 3px;
        padding: 3px 10px;
        font-size: 11px;
    }
    QPushButton:hover { background: #2d6a9f; }
    QPushButton:pressed { background: #1a3a5c; }
"""

SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #333;
        height: 4px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #6a9fd8;
        width: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }
    QSlider::sub-page:horizontal {
        background: #4a7aaa;
        border-radius: 2px;
    }
"""

MASTER_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #333;
        height: 6px;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #e8a040;
        width: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #c07820;
        border-radius: 3px;
    }
"""


class ParamSlider(QWidget):
    """Single parameter: label + slider + value readout."""

    def __init__(self, label, min_val, max_val, default, step, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 1, 4, 1)
        layout.setSpacing(4)

        self._label = QLabel(label)
        self._label.setFixedWidth(60)
        self._label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._label)

        steps = int((max_val - min_val) / step)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, steps)
        self._slider.setValue(int((default - min_val) / step))
        self._slider.setStyleSheet(SLIDER_STYLE)
        self._slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._slider, stretch=1)

        self._readout = QLabel(self._fmt(default))
        self._readout.setFixedWidth(50)
        self._readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._readout.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(self._readout)

    @property
    def value(self):
        return self.min_val + self._slider.value() * self.step

    def _fmt(self, v):
        if self.step >= 1 and self.step == int(self.step):
            return str(int(v))
        return f"{v:.2f}"

    def _on_changed(self, _):
        self._readout.setText(self._fmt(self.value))


class CollapsibleFilter(QWidget):
    """One collapsible filter section: header button, param sliders, apply."""

    apply_requested = pyqtSignal(object, dict)  # fn, kwargs

    def __init__(self, label, fn, param_defs, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.param_defs = param_defs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = QPushButton(f"  {label}")
        self._header.setStyleSheet(HEADER_STYLE)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        self._body = QWidget()
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 2, 0, 4)
        body_layout.setSpacing(2)

        self._sliders: dict[str, ParamSlider] = {}
        for plabel, kwarg, mn, mx, default, step in param_defs:
            ps = ParamSlider(plabel, mn, mx, default, step)
            body_layout.addWidget(ps)
            self._sliders[kwarg] = ps

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 2, 4, 2)
        btn_row.addStretch()
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet(APPLY_STYLE)
        self._apply_btn.setFixedWidth(60)
        self._apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(self._apply_btn)
        body_layout.addLayout(btn_row)

        layout.addWidget(self._body)
        self._body.setVisible(False)
        self._expanded = False

    def _toggle(self):
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        arrow = "v" if self._expanded else ">"
        text = self._header.text().lstrip(" >v")
        self._header.setText(f" {arrow} {text}")

    def _on_apply(self):
        kwargs = {k: s.value for k, s in self._sliders.items()}
        self.apply_requested.emit(self.fn, kwargs)


class FilterPanel(QWidget):
    """Scrollable panel with master volume slider and 20 collapsible filters."""

    filter_apply = pyqtSignal(object, dict)  # fn, kwargs
    master_volume_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Master volume
        vol_frame = QWidget()
        vol_layout = QVBoxLayout(vol_frame)
        vol_layout.setContentsMargins(8, 6, 8, 6)
        vol_layout.setSpacing(2)

        vol_header = QLabel("Mix Volume")
        vol_header.setStyleSheet("color: #ccc; font-size: 12px; font-weight: bold;")
        vol_layout.addWidget(vol_header)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(6)
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 150)
        self._vol_slider.setValue(100)
        self._vol_slider.setStyleSheet(MASTER_SLIDER_STYLE)
        self._vol_slider.valueChanged.connect(self._on_vol_changed)
        slider_row.addWidget(self._vol_slider, stretch=1)

        self._vol_label = QLabel("100%")
        self._vol_label.setFixedWidth(40)
        self._vol_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._vol_label.setStyleSheet("color: #e8a040; font-size: 12px; font-weight: bold;")
        slider_row.addWidget(self._vol_label)
        vol_layout.addLayout(slider_row)

        outer.addWidget(vol_frame)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        outer.addWidget(sep)

        # Filter header
        filt_label = QLabel("  Filters")
        filt_label.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold; padding: 4px 0;")
        outer.addWidget(filt_label)

        # Scrollable filter list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #1a1a1a; }
            QScrollBar:vertical {
                background: #1a1a1a; width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #444; border-radius: 4px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        for label, fn, param_defs in FILTER_DEFS:
            section = CollapsibleFilter(label, fn, param_defs)
            section.apply_requested.connect(self._on_filter_apply)
            container_layout.addWidget(section)

        container_layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

    def _on_vol_changed(self, val):
        self._vol_label.setText(f"{val}%")
        self.master_volume_changed.emit(val / 100.0)

    def _on_filter_apply(self, fn, kwargs):
        self.filter_apply.emit(fn, kwargs)
