"""Main application window — layout, menus, key events, signal wiring."""

import os
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QMessageBox, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from models.audio_document import AudioDocument
from audio.recorder import AudioRecorder
from audio.player import AudioPlayer
from audio.undo_manager import UndoManager
from audio.filters import FILTER_REGISTRY, FILTER_DEFS
from ui.waveform_widget import WaveformWidget
from ui.file_browser import FileBrowser
from ui.filter_panel import FilterPanel
from ui.effects_panel import EffectsPanel
from ui.transport_controls import TransportControls

WAVS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wavs")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recorder")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("background: #0d1b2a; color: #bec8d2;")

        self.doc = AudioDocument()
        self.recorder = AudioRecorder(parent=self)
        self.player = AudioPlayer(parent=self)
        self.undo_mgr = UndoManager()

        self._space_held = False
        self._paste_pos: int = -1

        os.makedirs(WAVS_DIR, exist_ok=True)

        self._build_ui()
        self._build_menus()
        self._connect_signals()
        self._start_cursor_timer()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #1a3050; width: 1px; }"
        )

        # Left panel: file browser (top) + filter panel (bottom)
        left = QWidget()
        left.setStyleSheet("background: #0d1b2a;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.file_browser = FileBrowser(WAVS_DIR)
        self.file_browser.setMaximumHeight(160)
        left_layout.addWidget(self.file_browser)

        self.filter_panel = FilterPanel()
        left_layout.addWidget(self.filter_panel, stretch=1)

        left.setMinimumWidth(200)
        left.setMaximumWidth(300)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.waveform = WaveformWidget()
        right_layout.addWidget(self.waveform, stretch=1)

        self.transport = TransportControls()
        right_layout.addWidget(self.transport)

        self.effects_panel = EffectsPanel()
        right_layout.addWidget(self.effects_panel)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)

        main_layout.addWidget(splitter)

    def _build_menus(self):
        menu = self.menuBar()
        menu.setStyleSheet(
            "QMenuBar { background: #0a1520; color: #8899aa; font-size: 13px; padding: 2px 0; }"
            "QMenuBar::item { padding: 4px 10px; }"
            "QMenuBar::item:selected { color: #fff; background: #162a3e; }"
            "QMenu { background: #0f2030; color: #bec8d2; border: 1px solid #1a3050; }"
            "QMenu::item { padding: 5px 24px; }"
            "QMenu::item:selected { background: #1a3a55; }"
            "QMenu::separator { height: 1px; background: #1a3050; margin: 4px 8px; }"
        )
        file_menu = menu.addMenu("File")

        self._add_action(file_menu, "New", "Ctrl+N", self._on_new)
        self._add_action(file_menu, "Open...", "Ctrl+O", self._on_open)
        self._add_action(file_menu, "Save", "Ctrl+S", self._on_save)
        self._add_action(file_menu, "Save As...", "Ctrl+Shift+S", self._on_save_as)
        self._add_action(file_menu, "Export Clean WAV...", "Ctrl+E", self._on_export)
        file_menu.addSeparator()
        self._add_action(file_menu, "Quit", "Ctrl+Q", self.close)

        edit_menu = menu.addMenu("Edit")
        self._add_action(edit_menu, "Undo", "Ctrl+Z", self._on_undo)
        self._add_action(edit_menu, "Redo", "Ctrl+Y", self._on_redo)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Copy", "Ctrl+C", self._on_copy)
        self._add_action(edit_menu, "Paste", "Ctrl+V", self._on_paste)
        self._add_action(edit_menu, "Delete Selection", "Delete", self._on_delete)
        self._add_action(edit_menu, "Crop to Selection", "Ctrl+Shift+X", self._on_crop)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Select All", "Ctrl+A", self._on_select_all)
        self._add_action(edit_menu, "Zoom to Fit", "Ctrl+0", lambda: self.waveform.zoom_to_fit())

        filter_menu = menu.addMenu("Filter")
        for label, fn, param_defs in FILTER_DEFS:
            self._add_filter_action(filter_menu, label, fn, param_defs)

    def _add_filter_action(self, menu, label, fn, param_defs):
        action = QAction(label, self)
        action.triggered.connect(
            lambda checked, l=label, f=fn, p=param_defs: self._on_filter_menu_select(l, f, p)
        )
        menu.addAction(action)

    def _on_filter_menu_select(self, label, fn, param_defs):
        """Add filter to the panel and apply it."""
        self.filter_panel.add_filter(label, fn, param_defs)
        self._apply_filter(fn)

    def _add_action(self, menu, text, shortcut, callback):
        action = QAction(text, self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        menu.addAction(action)

    def _connect_signals(self):
        # Recorder
        self.recorder.samples_ready.connect(self._on_samples_recorded)
        self.recorder.recording_started.connect(lambda: self.transport.set_recording(True))
        self.recorder.recording_stopped.connect(lambda: self.transport.set_recording(False))

        # Player
        self.player.position_changed.connect(self._on_playback_position)
        self.player.playback_started.connect(lambda: self.transport.set_playing(True))
        self.player.playback_finished.connect(self._on_playback_finished)

        # File browser
        self.file_browser.file_selected.connect(self._load_file)
        self.file_browser._add_btn.clicked.connect(self._on_open)

        # Effects
        self.effects_panel.effect_changed.connect(self._on_effect_changed)

        # Filter panel
        self.filter_panel.filter_apply.connect(self._on_filter_panel_apply)
        self.filter_panel.master_volume_changed.connect(self._on_master_volume)

        # Transport buttons
        self.transport.btn_record.clicked.connect(self._toggle_record)
        self.transport.btn_play.clicked.connect(self._toggle_play)
        self.transport.btn_stop.clicked.connect(self._stop_all)

    def _start_cursor_timer(self):
        self._cursor_timer = QTimer(self)
        self._cursor_timer.setInterval(33)  # ~30fps
        self._cursor_timer.timeout.connect(self._update_cursor)
        self._cursor_timer.start()

    # ── Key Events ───────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() == Qt.Key.Key_Space:
            self._space_held = True
            self._start_recording()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._play_always()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() == Qt.Key.Key_Space:
            self._space_held = False
            self._stop_recording()
        else:
            super().keyReleaseEvent(event)

    # ── Recording ────────────────────────────────────────────────────

    def _start_recording(self):
        self.player.stop()
        self.undo_mgr.push(self.doc.get_snapshot())
        self.recorder.start()

    def _stop_recording(self):
        self.recorder.stop()
        self._refresh_waveform()

    def _toggle_record(self):
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _on_samples_recorded(self, chunk):
        self.doc.append_samples(chunk)
        self.waveform.set_samples(self.doc.samples, recording=True)
        self.transport.update_time(self.doc.duration, self.doc.duration)

    # ── Playback ─────────────────────────────────────────────────────

    def _start_playback(self):
        if self.doc.num_samples == 0:
            return
        self.recorder.stop()
        rendered = self.doc.get_rendered()
        sel = self.waveform.get_selection()
        start = sel[0] if sel[0] >= 0 else 0
        self.player.play(rendered, start)

    def _play_always(self):
        """Enter key handler — always play, from beginning if no selection."""
        if self.doc.num_samples == 0:
            return
        self.recorder.stop()
        rendered = self.doc.get_rendered()
        sel = self.waveform.get_selection()
        if sel[0] >= 0:
            self.player.play(rendered, sel[0])
        else:
            self.player.play(rendered, 0)

    def _toggle_play(self):
        if self.player.is_playing:
            self.player.stop()
            self.transport.set_playing(False)
        else:
            self._start_playback()

    def _stop_all(self):
        self.recorder.stop()
        self.player.stop()
        self.transport.set_recording(False)
        self.transport.set_playing(False)
        self.waveform.clear_cursor()

    def _on_playback_position(self, pos):
        self.waveform.set_cursor(pos)

    def _on_playback_finished(self):
        self.transport.set_playing(False)
        self.waveform.clear_cursor()

    def _update_cursor(self):
        if self.player.is_playing:
            pos = self.player.position
            cur_time = pos / self.doc.sample_rate if self.doc.sample_rate else 0
            self.transport.update_time(cur_time, self.doc.duration)

    # ── File Operations ──────────────────────────────────────────────

    def _on_new(self):
        if not self._check_save():
            return
        self.doc.new()
        self.undo_mgr.clear()
        self.effects_panel.set_params(self.doc.effect_params)
        self._refresh_waveform()
        self.setWindowTitle("Recorder")

    def _on_open(self):
        if not self._check_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open WAV", WAVS_DIR, "WAV Files (*.wav)")
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        try:
            self.doc.load(path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load: {e}")
            return
        self.undo_mgr.load_from_file(path)
        self.effects_panel.set_params(self.doc.effect_params)
        self._refresh_waveform()
        self.setWindowTitle(f"Recorder — {os.path.basename(path)}")

    def _on_save(self):
        if not self.doc.file_path:
            self._on_save_as()
            return
        self.doc.save()
        self.undo_mgr.save_to_file(self.doc.file_path)
        self.file_browser.refresh()

    def _on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", WAVS_DIR, "WAV Files (*.wav)")
        if path:
            if not path.lower().endswith(".wav"):
                path += ".wav"
            self.doc.save(path)
            self.undo_mgr.save_to_file(path)
            self.file_browser.refresh()
            self.setWindowTitle(f"Recorder — {os.path.basename(path)}")

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Clean WAV", WAVS_DIR, "WAV Files (*.wav)")
        if path:
            if not path.lower().endswith(".wav"):
                path += ".wav"
            self.doc.export_clean(path)
            self.file_browser.refresh()

    def _check_save(self) -> bool:
        if not self.doc.dirty:
            return True
        ret = QMessageBox.question(
            self, "Unsaved Changes",
            "Save changes before continuing?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        if ret == QMessageBox.StandardButton.Yes:
            self._on_save()
            return True
        elif ret == QMessageBox.StandardButton.No:
            return True
        return False

    # ── Edit Operations ──────────────────────────────────────────────

    def _on_undo(self):
        result = self.undo_mgr.undo(self.doc.get_snapshot())
        if result is not None:
            self.doc.restore_snapshot(result)
            self._refresh_waveform()

    def _on_redo(self):
        result = self.undo_mgr.redo(self.doc.get_snapshot())
        if result is not None:
            self.doc.restore_snapshot(result)
            self._refresh_waveform()

    def _on_copy(self):
        sel = self.waveform.get_selection()
        if sel[0] >= 0:
            self.doc.copy_selection(sel[0], sel[1])

    def _on_paste(self):
        if self.doc.clipboard is None:
            return
        # Paste at cursor or selection start
        sel = self.waveform.get_selection()
        pos = sel[0] if sel[0] >= 0 else (
            self.waveform._cursor_pos if self.waveform._cursor_pos >= 0 else self.doc.num_samples
        )
        self.undo_mgr.push(self.doc.get_snapshot())
        self.doc.paste(pos)
        self._refresh_waveform()

    def _on_delete(self):
        sel = self.waveform.get_selection()
        if sel[0] < 0:
            return
        self.undo_mgr.push(self.doc.get_snapshot())
        self.doc.delete_selection(sel[0], sel[1])
        self.waveform.clear_selection()
        self._refresh_waveform()

    def _on_crop(self):
        sel = self.waveform.get_selection()
        if sel[0] < 0:
            return
        self.undo_mgr.push(self.doc.get_snapshot())
        self.doc.crop_to_selection(sel[0], sel[1])
        self.waveform.clear_selection()
        self._refresh_waveform()

    def _on_filter_panel_apply(self, fn, kwargs):
        self._apply_filter(fn, **kwargs)

    def _on_master_volume(self, vol):
        self.doc.effect_params["gain_db"] = 20.0 * np.log10(max(vol, 0.001))
        self.effects_panel.set_params(self.doc.effect_params)

    def _apply_filter(self, fn, **kwargs):
        if self.doc.num_samples == 0:
            return
        self.undo_mgr.push(self.doc.get_snapshot())
        sel = self.waveform.get_selection()
        if sel[0] >= 0 and sel[1] > sel[0]:
            segment = self.doc.samples[sel[0]:sel[1]].copy()
            filtered = fn(segment, self.doc.sample_rate, **kwargs)
            self.doc.samples[sel[0]:sel[0] + len(filtered)] = filtered
        else:
            self.doc.samples = fn(self.doc.samples, self.doc.sample_rate, **kwargs)
        self.doc.dirty = True
        self._refresh_waveform()

    def _on_select_all(self):
        if self.doc.num_samples == 0:
            return
        self.waveform._sel_start = 0
        self.waveform._sel_end = self.doc.num_samples
        self.waveform.update()
        self.waveform.selection_changed.emit(0, self.doc.num_samples)

    # ── Effects ──────────────────────────────────────────────────────

    def _on_effect_changed(self, key: str, val: float):
        self.doc.effect_params[key] = val
        self.doc.dirty = True
        if self.doc.file_path:
            self.doc._save_effects_sidecar()

    # ── Helpers ──────────────────────────────────────────────────────

    def _refresh_waveform(self):
        self.waveform.set_samples(self.doc.samples)
        self.waveform.zoom_to_fit()
        self.transport.update_time(0, self.doc.duration)

    def closeEvent(self, event):
        if self.doc.dirty and self.doc.num_samples > 0:
            if not self.doc.file_path:
                default_path = os.path.join(WAVS_DIR, "untitled.wav")
                self.doc.save(default_path)
            else:
                self.doc.save()
            if self.doc.file_path:
                self.undo_mgr.save_to_file(self.doc.file_path)
        self.player.stop()
        self.recorder.stop()
        event.accept()
