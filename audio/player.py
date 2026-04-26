"""Audio playback using sounddevice.OutputStream."""

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal


class AudioPlayer(QObject):
    """Plays back audio samples through the default output device.

    Emits position updates as Qt signals for cursor animation.
    """

    position_changed = pyqtSignal(int)  # current sample index
    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()

    def __init__(self, sample_rate: int = 44100, block_size: int = 1024,
                 parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.block_size = block_size
        self._stream: sd.OutputStream | None = None
        self._samples: np.ndarray | None = None
        self._position: int = 0
        self._is_playing = False

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def position(self) -> int:
        return self._position

    def play(self, samples: np.ndarray, start_sample: int = 0):
        self.stop()
        if len(samples) == 0:
            return
        self._samples = samples
        self._position = max(0, min(start_sample, len(samples)))
        self._is_playing = True

        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            blocksize=self.block_size,
            dtype="float32",
            callback=self._audio_callback,
            finished_callback=self._on_stream_finished,
        )
        self._stream.start()
        self.playback_started.emit()

    def stop(self):
        self._is_playing = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _audio_callback(self, outdata, frames, time_info, status):
        if not self._is_playing or self._samples is None:
            outdata.fill(0)
            raise sd.CallbackStop()

        end = self._position + frames
        if end > len(self._samples):
            valid = len(self._samples) - self._position
            outdata[:valid, 0] = self._samples[self._position:self._position + valid]
            outdata[valid:, 0] = 0
            self._position = len(self._samples)
            self.position_changed.emit(self._position)
            raise sd.CallbackStop()
        else:
            outdata[:, 0] = self._samples[self._position:end]
            self._position = end
            self.position_changed.emit(self._position)

    def _on_stream_finished(self):
        self._is_playing = False
        self.playback_finished.emit()
