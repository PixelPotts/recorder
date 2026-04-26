"""Microphone capture using sounddevice.InputStream."""

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal


class AudioRecorder(QObject):
    """Records audio from the default microphone.

    Emits Qt signals from the sounddevice callback thread
    so the GUI can safely update.
    """

    samples_ready = pyqtSignal(np.ndarray)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    def __init__(self, sample_rate: int = 44100, channels: int = 1,
                 block_size: int = 1024, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self._stream: sd.InputStream | None = None
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self):
        if self._is_recording:
            return
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_recording = True
        self.recording_started.emit()

    def stop(self):
        if not self._is_recording:
            return
        self._is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.recording_stopped.emit()

    def _audio_callback(self, indata, frames, time_info, status):
        if not self._is_recording:
            return
        chunk = indata[:, 0].copy()
        self.samples_ready.emit(chunk)
