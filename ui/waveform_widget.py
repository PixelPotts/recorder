"""Custom waveform display with selection, cursor, and zoom."""

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QMouseEvent, QWheelEvent


class WaveformWidget(QWidget):
    """Draws waveform using envelope rendering (min/max per pixel column).

    Supports click-drag selection, playback cursor, and mouse-wheel zoom.
    """

    selection_changed = pyqtSignal(int, int)  # start_sample, end_sample

    # Colors
    BG_COLOR = QColor(30, 30, 30)
    WAVE_COLOR = QColor(0, 180, 100)
    SELECTION_COLOR = QColor(80, 150, 255, 80)
    CURSOR_COLOR = QColor(255, 60, 60)
    CENTERLINE_COLOR = QColor(60, 60, 60)
    GHOST_COLOR = QColor(200, 200, 100, 90)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._samples: np.ndarray = np.array([], dtype=np.float32)
        self._num_samples: int = 0

        # View range (which portion of the audio is visible)
        self._view_start: int = 0  # first visible sample
        self._view_end: int = 0    # last visible sample

        # Selection
        self._sel_start: int = -1
        self._sel_end: int = -1
        self._dragging: bool = False
        self._drag_origin: int = -1

        # Playback cursor
        self._cursor_pos: int = -1

        # Paste ghost preview
        self._ghost_samples: np.ndarray | None = None
        self._ghost_pos: int = -1

        # Envelope cache
        self._envelope_min: np.ndarray | None = None
        self._envelope_max: np.ndarray | None = None
        self._envelope_width: int = 0
        self._envelope_view: tuple[int, int] = (0, 0)

    def set_samples(self, samples: np.ndarray):
        self._samples = samples
        self._num_samples = len(samples)
        if self._view_end == 0 or self._view_end > self._num_samples:
            self._view_start = 0
            self._view_end = self._num_samples
        self._invalidate_envelope()
        self.update()

    def set_cursor(self, sample_pos: int):
        self._cursor_pos = sample_pos
        self.update()

    def clear_cursor(self):
        self._cursor_pos = -1
        self.update()

    def get_selection(self) -> tuple[int, int]:
        if self._sel_start < 0 or self._sel_end < 0:
            return (-1, -1)
        s = min(self._sel_start, self._sel_end)
        e = max(self._sel_start, self._sel_end)
        return (s, e)

    def clear_selection(self):
        self._sel_start = -1
        self._sel_end = -1
        self.update()

    def set_ghost(self, samples: np.ndarray, position: int):
        self._ghost_samples = samples
        self._ghost_pos = position
        self.update()

    def clear_ghost(self):
        self._ghost_samples = None
        self._ghost_pos = -1
        self.update()

    def zoom_to_fit(self):
        self._view_start = 0
        self._view_end = max(1, self._num_samples)
        self._invalidate_envelope()
        self.update()

    def _invalidate_envelope(self):
        self._envelope_min = None
        self._envelope_max = None

    def _pixel_to_sample(self, px: int) -> int:
        w = self.width()
        if w <= 0:
            return 0
        view_len = self._view_end - self._view_start
        if view_len <= 0:
            return self._view_start
        s = self._view_start + int(px / w * view_len)
        return max(0, min(s, self._num_samples))

    def _sample_to_pixel(self, sample: int) -> int:
        w = self.width()
        view_len = self._view_end - self._view_start
        if view_len <= 0:
            return 0
        return int((sample - self._view_start) / view_len * w)

    def _compute_envelope(self):
        w = self.width()
        if w <= 0 or self._num_samples == 0:
            return
        view = self._samples[self._view_start:self._view_end]
        n = len(view)
        if n == 0:
            return
        cols = max(1, w)
        env_min = np.zeros(cols, dtype=np.float32)
        env_max = np.zeros(cols, dtype=np.float32)
        samples_per_col = n / cols
        for i in range(cols):
            start = int(i * samples_per_col)
            end = max(start + 1, int((i + 1) * samples_per_col))
            end = min(end, n)
            block = view[start:end]
            if len(block) > 0:
                env_min[i] = block.min()
                env_max[i] = block.max()
        self._envelope_min = env_min
        self._envelope_max = env_max
        self._envelope_width = cols
        self._envelope_view = (self._view_start, self._view_end)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w = self.width()
        h = self.height()
        mid_y = h // 2

        # Background
        p.fillRect(0, 0, w, h, self.BG_COLOR)

        # Center line
        p.setPen(QPen(self.CENTERLINE_COLOR, 1))
        p.drawLine(0, mid_y, w, mid_y)

        if self._num_samples == 0:
            p.end()
            return

        # Recompute envelope if needed
        cache_valid = (
            self._envelope_min is not None
            and self._envelope_width == w
            and self._envelope_view == (self._view_start, self._view_end)
        )
        if not cache_valid:
            self._compute_envelope()

        # Draw waveform
        if self._envelope_min is not None:
            p.setPen(QPen(self.WAVE_COLOR, 1))
            scale = mid_y * 0.95
            for x in range(min(w, self._envelope_width)):
                y_min = int(mid_y - self._envelope_max[x] * scale)
                y_max = int(mid_y - self._envelope_min[x] * scale)
                if y_min == y_max:
                    y_max += 1
                p.drawLine(x, y_min, x, y_max)

        # Selection overlay
        sel_s, sel_e = self.get_selection()
        if sel_s >= 0 and sel_e > sel_s:
            px_s = self._sample_to_pixel(sel_s)
            px_e = self._sample_to_pixel(sel_e)
            p.fillRect(px_s, 0, px_e - px_s, h, self.SELECTION_COLOR)

        # Ghost paste preview
        if self._ghost_samples is not None and self._ghost_pos >= 0:
            gx_start = self._sample_to_pixel(self._ghost_pos)
            gx_end = self._sample_to_pixel(self._ghost_pos + len(self._ghost_samples))
            p.fillRect(gx_start, 0, max(1, gx_end - gx_start), h, self.GHOST_COLOR)

        # Playback cursor
        if 0 <= self._cursor_pos <= self._num_samples:
            cx = self._sample_to_pixel(self._cursor_pos)
            p.setPen(QPen(self.CURSOR_COLOR, 2))
            p.drawLine(cx, 0, cx, h)

        p.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            sample = self._pixel_to_sample(int(event.position().x()))
            self._dragging = True
            self._drag_origin = sample
            self._sel_start = sample
            self._sel_end = sample
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            sample = self._pixel_to_sample(int(event.position().x()))
            self._sel_start = min(self._drag_origin, sample)
            self._sel_end = max(self._drag_origin, sample)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            sample = self._pixel_to_sample(int(event.position().x()))
            self._sel_start = min(self._drag_origin, sample)
            self._sel_end = max(self._drag_origin, sample)
            if self._sel_end - self._sel_start < 10:
                # Click without drag = set cursor position, clear selection
                self._cursor_pos = self._sel_start
                self._sel_start = -1
                self._sel_end = -1
            else:
                self.selection_changed.emit(self._sel_start, self._sel_end)
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        if self._num_samples == 0:
            return
        delta = event.angleDelta().y()
        mouse_x = int(event.position().x())
        mouse_sample = self._pixel_to_sample(mouse_x)

        view_len = self._view_end - self._view_start
        factor = 0.85 if delta > 0 else 1.0 / 0.85

        new_len = int(view_len * factor)
        new_len = max(100, min(new_len, self._num_samples))

        # Keep mouse position anchored
        mouse_frac = mouse_x / max(1, self.width())
        new_start = int(mouse_sample - mouse_frac * new_len)
        new_start = max(0, min(new_start, self._num_samples - new_len))
        new_end = new_start + new_len

        self._view_start = new_start
        self._view_end = min(new_end, self._num_samples)
        self._invalidate_envelope()
        self.update()
