"""Custom waveform display with selection, cursor, zoom, and timeline."""

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QMouseEvent, QWheelEvent, QFont


class WaveformWidget(QWidget):
    """Draws waveform using envelope rendering (min/max per pixel column).

    Supports click-drag selection, playback cursor, mouse-wheel zoom,
    and a timeline with dotted grid lines.
    """

    selection_changed = pyqtSignal(int, int)  # start_sample, end_sample

    # Colors — dark navy + cyan theme
    BG_COLOR = QColor(10, 18, 28)
    WAVE_COLOR = QColor(0, 210, 170)
    WAVE_FILL_COLOR = QColor(0, 210, 170, 40)
    SELECTION_COLOR = QColor(0, 180, 160, 50)
    CURSOR_COLOR = QColor(255, 60, 60)
    CENTERLINE_COLOR = QColor(20, 40, 60)
    GRID_COLOR = QColor(25, 45, 65)
    GRID_TEXT_COLOR = QColor(80, 110, 140)
    GHOST_COLOR = QColor(200, 200, 100, 60)

    TIMELINE_HEIGHT = 22
    SAMPLE_RATE = 44100  # default, updated from doc

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._samples: np.ndarray = np.array([], dtype=np.float32)
        self._num_samples: int = 0
        self._sample_rate: int = self.SAMPLE_RATE

        # View range (which portion of the audio is visible)
        self._view_start: int = 0
        self._view_end: int = 0

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

    def set_samples(self, samples: np.ndarray, recording: bool = False):
        self._samples = samples
        self._num_samples = len(samples)
        if recording and self._num_samples > 0:
            window = self._sample_rate * 4
            if self._num_samples > window:
                self._view_start = self._num_samples - window
                self._view_end = self._num_samples
            else:
                self._view_start = 0
                self._view_end = self._num_samples
        elif self._view_end == 0 or self._view_end > self._num_samples:
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

    def _calc_grid_interval(self, view_seconds: float, width_px: int) -> float:
        """Pick a nice round time interval for grid lines."""
        if view_seconds <= 0 or width_px <= 0:
            return 1.0
        target_px = 100  # desired pixels between grid lines
        target_sec = view_seconds * target_px / width_px
        nice = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60]
        for n in nice:
            if n >= target_sec:
                return n
        return 60.0

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w = self.width()
        h = self.height()
        tl_h = self.TIMELINE_HEIGHT
        wave_h = h - tl_h
        mid_y = tl_h + wave_h // 2

        # Background
        p.fillRect(0, 0, w, h, self.BG_COLOR)

        # Timeline background
        p.fillRect(0, 0, w, tl_h, QColor(8, 14, 22))

        # Draw timeline and grid
        if self._num_samples > 0:
            view_start_sec = self._view_start / self._sample_rate
            view_end_sec = self._view_end / self._sample_rate
            view_dur = view_end_sec - view_start_sec
            interval = self._calc_grid_interval(view_dur, w)

            first_mark = int(view_start_sec / interval) * interval
            if first_mark < view_start_sec:
                first_mark += interval

            # Dotted grid pen
            grid_pen = QPen(self.GRID_COLOR, 1, Qt.PenStyle.DotLine)
            text_font = QFont("monospace", 8)
            p.setFont(text_font)

            t = first_mark
            while t <= view_end_sec:
                sample = int(t * self._sample_rate)
                px = self._sample_to_pixel(sample)

                # Dotted vertical line
                p.setPen(grid_pen)
                p.drawLine(px, tl_h, px, h)

                # Time label
                p.setPen(QPen(self.GRID_TEXT_COLOR))
                if t < 60:
                    label = f"{t:.1f}" if interval < 1 else f"0:{t:04.1f}"
                else:
                    m = int(t) // 60
                    s = t - m * 60
                    label = f"{m}:{s:04.1f}"
                p.drawText(px + 3, tl_h - 5, label)

                t += interval

            # End time in accent color
            p.setPen(QPen(QColor(0, 210, 170)))
            end_label = f"{view_end_sec:.1f}" if view_end_sec < 60 else f"{int(view_end_sec)//60}:{view_end_sec%60:04.1f}"
            end_w = p.fontMetrics().horizontalAdvance(end_label)
            p.drawText(w - end_w - 4, tl_h - 5, end_label)

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
            scale = (wave_h // 2) * 0.95
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
            p.fillRect(px_s, tl_h, px_e - px_s, wave_h, self.SELECTION_COLOR)
            # Selection edges
            edge_pen = QPen(QColor(0, 180, 160, 120), 1)
            p.setPen(edge_pen)
            p.drawLine(px_s, tl_h, px_s, h)
            p.drawLine(px_e, tl_h, px_e, h)

        # Ghost paste preview
        if self._ghost_samples is not None and self._ghost_pos >= 0:
            gx_start = self._sample_to_pixel(self._ghost_pos)
            gx_end = self._sample_to_pixel(self._ghost_pos + len(self._ghost_samples))
            p.fillRect(gx_start, tl_h, max(1, gx_end - gx_start), wave_h, self.GHOST_COLOR)

        # Playback cursor
        if 0 <= self._cursor_pos <= self._num_samples:
            cx = self._sample_to_pixel(self._cursor_pos)
            p.setPen(QPen(self.CURSOR_COLOR, 2))
            p.drawLine(cx, tl_h, cx, h)

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

        mouse_frac = mouse_x / max(1, self.width())
        new_start = int(mouse_sample - mouse_frac * new_len)
        new_start = max(0, min(new_start, self._num_samples - new_len))
        new_end = new_start + new_len

        self._view_start = new_start
        self._view_end = min(new_end, self._num_samples)
        self._invalidate_envelope()
        self.update()
