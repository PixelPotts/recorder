"""Left-side filter panel with collapsible sections and parameter sliders."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal


FILTER_HEADER_STYLE = """
    QPushButton {
        background: transparent;
        color: #bec8d2;
        border: none;
        text-align: left;
        padding: 6px 8px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover { color: #fff; }
"""

DOTS_BTN_STYLE = """
    QPushButton {
        background: transparent;
        color: #556677;
        border: none;
        font-size: 16px;
        font-weight: bold;
        padding: 0 4px;
    }
    QPushButton:hover { color: #bec8d2; }
"""

POWER_BTN_STYLE = """
    QPushButton {
        background: transparent;
        color: #00d4ff;
        border: 1px solid #1a3855;
        border-radius: 10px;
        font-size: 11px;
        padding: 0;
    }
    QPushButton:hover { border-color: #00d4ff; }
"""

APPLY_STYLE = """
    QPushButton {
        background: #0a3a3a;
        color: #4ae8ff;
        border: 1px solid #1a5050;
        border-radius: 4px;
        padding: 3px 12px;
        font-size: 11px;
    }
    QPushButton:hover { background: #0f4a4a; border-color: #4ae8ff; }
    QPushButton:pressed { background: #084040; }
"""

SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #1a3050;
        height: 4px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #00bce8;
        width: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #00a0d0;
        border-radius: 2px;
    }
"""

MASTER_SLIDER_STYLE = """
    QSlider::groove:horizontal {
        background: #1a3050;
        height: 5px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #00d4ff;
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }
    QSlider::sub-page:horizontal {
        background: #00bce8;
        border-radius: 2px;
    }
"""

CARD_STYLE = """
    QFrame {
        background: #0f1f30;
        border: 1px solid #1a3050;
        border-radius: 6px;
        margin: 3px 6px;
    }
"""


class ParamSlider(QWidget):
    """Single parameter: label + slider + value readout + tick labels."""

    def __init__(self, label, min_val, max_val, default, step, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 2, 8, 0)
        outer.setSpacing(0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel(label)
        self._label.setFixedWidth(55)
        self._label.setStyleSheet("color: #7a8a9a; font-size: 11px;")
        layout.addWidget(self._label)

        steps = int((max_val - min_val) / step)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, steps)
        self._slider.setValue(int((default - min_val) / step))
        self._slider.setStyleSheet(SLIDER_STYLE)
        self._slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._slider, stretch=1)

        self._readout = QLabel(self._fmt(default))
        self._readout.setFixedWidth(45)
        self._readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._readout.setStyleSheet("color: #8899aa; font-size: 11px;")
        layout.addWidget(self._readout)

        outer.addLayout(layout)

        # Tick labels row
        tick_style = "color: #4a5a6a; font-size: 9px;"
        tick_row = QHBoxLayout()
        tick_row.setContentsMargins(55, 0, 45, 0)
        tick_row.setSpacing(0)
        min_lbl = QLabel(self._fmt(min_val))
        min_lbl.setStyleSheet(tick_style)
        tick_row.addWidget(min_lbl)
        tick_row.addStretch()
        mid_val = (min_val + max_val) / 2
        mid_lbl = QLabel(self._fmt(mid_val))
        mid_lbl.setStyleSheet(tick_style)
        mid_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tick_row.addWidget(mid_lbl)
        tick_row.addStretch()
        max_lbl = QLabel(self._fmt(max_val))
        max_lbl.setStyleSheet(tick_style)
        max_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        tick_row.addWidget(max_lbl)
        outer.addLayout(tick_row)

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
    """One collapsible filter section in a card frame."""

    apply_requested = pyqtSignal(object, dict)  # fn, kwargs

    def __init__(self, label, fn, param_defs, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.param_defs = param_defs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Card frame
        self._card = QFrame()
        self._card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Header row: arrow + label + dots menu
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        self._power_btn = QPushButton("\u23fb")
        self._power_btn.setFixedSize(20, 20)
        self._power_btn.setStyleSheet(POWER_BTN_STYLE)
        self._power_btn.setToolTip("Toggle filter")
        header_row.addWidget(self._power_btn)

        self._header = QPushButton(f"\u2304  {label}")
        self._header.setStyleSheet(FILTER_HEADER_STYLE)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self._toggle)
        header_row.addWidget(self._header, stretch=1)

        self._dots_btn = QPushButton("\u22ee")
        self._dots_btn.setFixedSize(24, 24)
        self._dots_btn.setStyleSheet(DOTS_BTN_STYLE)
        header_row.addWidget(self._dots_btn)

        card_layout.addLayout(header_row)

        # Body with sliders
        self._body = QWidget()
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 2, 0, 6)
        body_layout.setSpacing(2)

        self._sliders: dict[str, ParamSlider] = {}
        for plabel, kwarg, mn, mx, default, step in param_defs:
            ps = ParamSlider(plabel, mn, mx, default, step)
            body_layout.addWidget(ps)
            self._sliders[kwarg] = ps

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(10, 4, 8, 2)
        btn_row.addStretch()
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet(APPLY_STYLE)
        self._apply_btn.setFixedWidth(60)
        self._apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(self._apply_btn)
        body_layout.addLayout(btn_row)

        card_layout.addWidget(self._body)
        self._body.setVisible(False)
        self._expanded = False

        layout.addWidget(self._card)

    def _toggle(self):
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        arrow = "\u2304" if self._expanded else "\u203a"
        text = self._header.text()
        # Strip old arrow
        for ch in ("\u2304", "\u203a"):
            text = text.replace(ch, "")
        text = text.strip()
        self._header.setText(f"{arrow}  {text}")

    def _on_apply(self):
        kwargs = {k: s.value for k, s in self._sliders.items()}
        self.apply_requested.emit(self.fn, kwargs)


class FilterPanel(QWidget):
    """Scrollable panel with master volume slider and user-selected filters."""

    filter_apply = pyqtSignal(object, dict)  # fn, kwargs
    master_volume_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_widgets: dict[str, CollapsibleFilter] = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Master volume
        vol_frame = QWidget()
        vol_layout = QVBoxLayout(vol_frame)
        vol_layout.setContentsMargins(8, 8, 8, 6)
        vol_layout.setSpacing(4)

        vol_header = QLabel("MIX VOLUME")
        vol_header.setStyleSheet(
            "color: #8899aa; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
        )
        vol_layout.addWidget(vol_header)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(8)
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 150)
        self._vol_slider.setValue(100)
        self._vol_slider.setStyleSheet(MASTER_SLIDER_STYLE)
        self._vol_slider.valueChanged.connect(self._on_vol_changed)
        slider_row.addWidget(self._vol_slider, stretch=1)

        self._vol_label = QLabel("100%")
        self._vol_label.setFixedWidth(40)
        self._vol_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._vol_label.setStyleSheet("color: #bec8d2; font-size: 12px; font-weight: bold;")
        slider_row.addWidget(self._vol_label)
        vol_layout.addLayout(slider_row)

        outer.addWidget(vol_frame)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a3050;")
        outer.addWidget(sep)

        # Filter header with chevron
        filt_header_row = QHBoxLayout()
        filt_header_row.setContentsMargins(8, 6, 8, 2)
        filt_label = QLabel("FILTERS")
        filt_label.setStyleSheet(
            "color: #8899aa; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
        )
        filt_header_row.addWidget(filt_label)
        filt_header_row.addStretch()
        filt_chevron = QLabel("\u2303")
        filt_chevron.setStyleSheet("color: #556677; font-size: 13px;")
        filt_header_row.addWidget(filt_chevron)
        outer.addLayout(filt_header_row)

        # Scrollable filter list (starts empty)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #0d1b2a; }
            QScrollBar:vertical {
                background: #0d1b2a; width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #1a3050; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)
        self._container_layout.addStretch()

        scroll.setWidget(self._container)
        outer.addWidget(scroll, stretch=1)

    def add_filter(self, label, fn, param_defs):
        """Add a filter to the panel (called when user picks from menu)."""
        if label in self._filter_widgets:
            return  # already added
        section = CollapsibleFilter(label, fn, param_defs)
        section.apply_requested.connect(self._on_filter_apply)
        # Insert before the stretch
        self._container_layout.insertWidget(
            self._container_layout.count() - 1, section
        )
        self._filter_widgets[label] = section

    def _on_vol_changed(self, val):
        self._vol_label.setText(f"{val}%")
        self.master_volume_changed.emit(val / 100.0)

    def _on_filter_apply(self, fn, kwargs):
        self.filter_apply.emit(fn, kwargs)
