"""10 DSP effect functions applied non-destructively."""

import numpy as np
from scipy import signal as sig


def apply_gain(samples: np.ndarray, gain_db: float) -> np.ndarray:
    if gain_db == 0.0:
        return samples
    return samples * (10.0 ** (gain_db / 20.0))


def apply_lowpass(samples: np.ndarray, sr: int, cutoff_hz: float) -> np.ndarray:
    if cutoff_hz >= 20000.0:
        return samples
    nyq = sr / 2.0
    freq = min(cutoff_hz, nyq * 0.99) / nyq
    b, a = sig.butter(4, freq, btype="low")
    return sig.lfilter(b, a, samples).astype(np.float32)


def apply_highpass(samples: np.ndarray, sr: int, cutoff_hz: float) -> np.ndarray:
    if cutoff_hz <= 20.0:
        return samples
    nyq = sr / 2.0
    freq = min(cutoff_hz, nyq * 0.99) / nyq
    b, a = sig.butter(4, freq, btype="high")
    return sig.lfilter(b, a, samples).astype(np.float32)


def apply_reverb(samples: np.ndarray, sr: int, wet_pct: float) -> np.ndarray:
    if wet_pct <= 0.0:
        return samples
    wet = wet_pct / 100.0
    decay_time = 1.5
    ir_len = int(sr * decay_time)
    ir = np.random.RandomState(42).randn(ir_len).astype(np.float32)
    ir *= np.exp(-np.linspace(0, 8, ir_len)).astype(np.float32)
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-8
    reverb = np.convolve(samples, ir, mode="full")[:len(samples)].astype(np.float32)
    return ((1 - wet) * samples + wet * reverb).astype(np.float32)


def apply_delay(samples: np.ndarray, sr: int, delay_ms: float) -> np.ndarray:
    if delay_ms <= 0.0:
        return samples
    delay_samples = int(sr * delay_ms / 1000.0)
    if delay_samples == 0:
        return samples
    out = samples.copy()
    decay = 0.5
    for tap in range(1, 4):
        offset = delay_samples * tap
        if offset >= len(samples):
            break
        gain = decay ** tap
        end = min(len(samples), len(samples) - offset)
        out[offset:offset + end] += samples[:end] * gain
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out.astype(np.float32)


def apply_compressor(samples: np.ndarray, ratio: float) -> np.ndarray:
    if ratio <= 1.0:
        return samples
    threshold = 0.3
    out = samples.copy()
    mask = np.abs(out) > threshold
    signs = np.sign(out[mask])
    magnitudes = np.abs(out[mask])
    compressed = threshold + (magnitudes - threshold) / ratio
    out[mask] = signs * compressed
    return out.astype(np.float32)


def apply_noise_gate(samples: np.ndarray, threshold_db: float) -> np.ndarray:
    if threshold_db <= -80.0:
        return samples
    threshold_linear = 10.0 ** (threshold_db / 20.0)
    out = samples.copy()
    # Simple gate with 256-sample window
    window = 256
    for i in range(0, len(out), window):
        block = out[i:i + window]
        rms = np.sqrt(np.mean(block ** 2))
        if rms < threshold_linear:
            out[i:i + window] *= 0.01
    return out.astype(np.float32)


def apply_pitch_shift(samples: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    if abs(semitones) < 0.01:
        return samples
    factor = 2.0 ** (semitones / 12.0)
    # Simple resampling approach
    indices = np.arange(0, len(samples), factor)
    indices = indices[indices < len(samples) - 1].astype(np.float64)
    int_idx = indices.astype(int)
    frac = (indices - int_idx).astype(np.float32)
    out = samples[int_idx] * (1 - frac) + samples[int_idx + 1] * frac
    return out.astype(np.float32)


def apply_mid_eq(samples: np.ndarray, sr: int, gain_db: float) -> np.ndarray:
    if abs(gain_db) < 0.1:
        return samples
    center_hz = 1000.0
    q = 1.0
    nyq = sr / 2.0
    w0 = center_hz / nyq
    if w0 >= 1.0:
        return samples
    b, a = sig.iirpeak(w0, q)
    linear_gain = 10.0 ** (gain_db / 20.0) - 1.0
    peaked = sig.lfilter(b, a, samples).astype(np.float32)
    return (samples + linear_gain * peaked).astype(np.float32)


def apply_normalize(samples: np.ndarray, target_pct: float) -> np.ndarray:
    if target_pct <= 0.0:
        return samples
    peak = np.max(np.abs(samples))
    if peak < 1e-8:
        return samples
    target = target_pct / 100.0
    return (samples * (target / peak)).astype(np.float32)


def apply_all_effects(samples: np.ndarray, sr: int, params: dict) -> np.ndarray:
    """Apply all effects in order. Returns new array."""
    out = samples.copy()
    out = apply_gain(out, params.get("gain_db", 0.0))
    out = apply_lowpass(out, sr, params.get("lowpass_hz", 20000.0))
    out = apply_highpass(out, sr, params.get("highpass_hz", 20.0))
    out = apply_reverb(out, sr, params.get("reverb_wet", 0.0))
    out = apply_delay(out, sr, params.get("delay_ms", 0.0))
    out = apply_compressor(out, params.get("compressor_ratio", 1.0))
    out = apply_noise_gate(out, params.get("gate_threshold_db", -80.0))
    out = apply_pitch_shift(out, sr, params.get("pitch_semitones", 0.0))
    out = apply_mid_eq(out, sr, params.get("mid_eq_db", 0.0))
    out = apply_normalize(out, params.get("normalize_pct", 0.0))
    return out
