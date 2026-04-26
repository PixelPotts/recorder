"""20-level undo/redo with JSON sidecar persistence."""

import numpy as np
import json
import zlib
import base64
import os


class UndoManager:
    """Manages undo/redo stacks of audio snapshots.

    Snapshots are stored as zlib-compressed base64-encoded numpy arrays.
    Persisted per file in filename.undo.json.
    """

    MAX_LEVELS = 20

    def __init__(self):
        self._undo_stack: list[np.ndarray] = []
        self._redo_stack: list[np.ndarray] = []

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def push(self, snapshot: np.ndarray):
        """Push current state before making a change."""
        self._undo_stack.append(snapshot.copy())
        if len(self._undo_stack) > self.MAX_LEVELS:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self, current: np.ndarray) -> np.ndarray | None:
        if not self._undo_stack:
            return None
        self._redo_stack.append(current.copy())
        return self._undo_stack.pop()

    def redo(self, current: np.ndarray) -> np.ndarray | None:
        if not self._redo_stack:
            return None
        self._undo_stack.append(current.copy())
        return self._redo_stack.pop()

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def save_to_file(self, wav_path: str):
        path = self._sidecar_path(wav_path)
        if not path:
            return
        data = {
            "undo": [self._encode(s) for s in self._undo_stack],
            "redo": [self._encode(s) for s in self._redo_stack],
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load_from_file(self, wav_path: str):
        path = self._sidecar_path(wav_path)
        if not path or not os.path.exists(path):
            self.clear()
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._undo_stack = [self._decode(s) for s in data.get("undo", [])]
            self._redo_stack = [self._decode(s) for s in data.get("redo", [])]
        except (json.JSONDecodeError, Exception):
            self.clear()

    @staticmethod
    def _sidecar_path(wav_path: str) -> str | None:
        if not wav_path:
            return None
        base, _ = os.path.splitext(wav_path)
        return base + ".undo.json"

    @staticmethod
    def _encode(arr: np.ndarray) -> str:
        raw = arr.astype(np.float32).tobytes()
        compressed = zlib.compress(raw)
        return base64.b64encode(compressed).decode("ascii")

    @staticmethod
    def _decode(s: str) -> np.ndarray:
        compressed = base64.b64decode(s)
        raw = zlib.decompress(compressed)
        return np.frombuffer(raw, dtype=np.float32).copy()
