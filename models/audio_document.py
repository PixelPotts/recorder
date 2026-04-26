"""Central data model for the audio recorder/editor."""

import numpy as np
import soundfile as sf
import json
import os


class AudioDocument:
    """Holds raw audio samples and effect parameters.

    Raw samples are never modified by effects. Effects are applied
    non-destructively via get_rendered().
    """

    SAMPLE_RATE = 44100
    DEFAULT_EFFECTS = {
        "gain_db": 0.0,
        "lowpass_hz": 20000.0,
        "highpass_hz": 20.0,
        "reverb_wet": 0.0,
        "delay_ms": 0.0,
        "compressor_ratio": 1.0,
        "gate_threshold_db": -80.0,
        "pitch_semitones": 0.0,
        "mid_eq_db": 0.0,
        "normalize_pct": 0.0,
    }

    def __init__(self):
        self.samples: np.ndarray = np.array([], dtype=np.float32)
        self.sample_rate: int = self.SAMPLE_RATE
        self.effect_params: dict = dict(self.DEFAULT_EFFECTS)
        self.file_path: str | None = None
        self.dirty: bool = False
        self.clipboard: np.ndarray | None = None

    @property
    def duration(self) -> float:
        if len(self.samples) == 0:
            return 0.0
        return len(self.samples) / self.sample_rate

    @property
    def num_samples(self) -> int:
        return len(self.samples)

    def new(self):
        self.samples = np.array([], dtype=np.float32)
        self.sample_rate = self.SAMPLE_RATE
        self.effect_params = dict(self.DEFAULT_EFFECTS)
        self.file_path = None
        self.dirty = False

    def load(self, path: str):
        data, sr = sf.read(path, dtype="float32", always_2d=True)
        # Convert stereo to mono
        if data.shape[1] > 1:
            data = data.mean(axis=1)
        else:
            data = data[:, 0]
        self.samples = data.astype(np.float32)
        self.sample_rate = sr
        self.file_path = path
        self.dirty = False
        self._load_effects_sidecar()

    def save(self, path: str | None = None):
        if path:
            self.file_path = path
        if not self.file_path:
            return False
        sf.write(self.file_path, self.samples, self.sample_rate, subtype="FLOAT")
        self._save_effects_sidecar()
        self.dirty = False
        return True

    def export_clean(self, path: str):
        from audio.effects import apply_all_effects
        rendered = apply_all_effects(self.samples, self.sample_rate, self.effect_params)
        sf.write(path, rendered, self.sample_rate, subtype="FLOAT")

    def append_samples(self, new_samples: np.ndarray):
        if len(self.samples) == 0:
            self.samples = new_samples.astype(np.float32)
        else:
            self.samples = np.concatenate([self.samples, new_samples.astype(np.float32)])
        self.dirty = True

    def get_rendered(self) -> np.ndarray:
        if len(self.samples) == 0:
            return self.samples
        from audio.effects import apply_all_effects
        return apply_all_effects(self.samples, self.sample_rate, self.effect_params)

    def get_selection(self, start_sample: int, end_sample: int) -> np.ndarray:
        start = max(0, start_sample)
        end = min(len(self.samples), end_sample)
        return self.samples[start:end].copy()

    def copy_selection(self, start_sample: int, end_sample: int):
        self.clipboard = self.get_selection(start_sample, end_sample)

    def paste(self, position: int) -> bool:
        if self.clipboard is None or len(self.clipboard) == 0:
            return False
        pos = max(0, min(position, len(self.samples)))
        self.samples = np.concatenate([
            self.samples[:pos],
            self.clipboard,
            self.samples[pos:]
        ]).astype(np.float32)
        self.dirty = True
        return True

    def delete_selection(self, start_sample: int, end_sample: int):
        start = max(0, start_sample)
        end = min(len(self.samples), end_sample)
        if start >= end:
            return
        self.samples = np.concatenate([
            self.samples[:start],
            self.samples[end:]
        ]).astype(np.float32)
        self.dirty = True

    def crop_to_selection(self, start_sample: int, end_sample: int):
        start = max(0, start_sample)
        end = min(len(self.samples), end_sample)
        self.samples = self.samples[start:end].copy()
        self.dirty = True

    def sample_to_time(self, sample_idx: int) -> float:
        return sample_idx / self.sample_rate

    def time_to_sample(self, time_sec: float) -> int:
        return int(time_sec * self.sample_rate)

    def _effects_sidecar_path(self) -> str | None:
        if not self.file_path:
            return None
        base, _ = os.path.splitext(self.file_path)
        return base + ".effects.json"

    def _save_effects_sidecar(self):
        path = self._effects_sidecar_path()
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.effect_params, f, indent=2)

    def _load_effects_sidecar(self):
        path = self._effects_sidecar_path()
        if not path or not os.path.exists(path):
            self.effect_params = dict(self.DEFAULT_EFFECTS)
            return
        with open(path, "r") as f:
            loaded = json.load(f)
        self.effect_params = dict(self.DEFAULT_EFFECTS)
        self.effect_params.update(loaded)

    def get_snapshot(self) -> np.ndarray:
        return self.samples.copy()

    def restore_snapshot(self, snapshot: np.ndarray):
        self.samples = snapshot.copy()
        self.dirty = True
