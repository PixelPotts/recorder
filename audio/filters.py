"""20 destructive filter functions applied to raw samples."""

import numpy as np
from scipy import signal as sig


def fade_in(samples: np.ndarray, sr: int) -> np.ndarray:
    """Linear fade in over first 0.5s."""
    n = min(int(sr * 0.5), len(samples))
    out = samples.copy()
    out[:n] *= np.linspace(0, 1, n).astype(np.float32)
    return out


def fade_out(samples: np.ndarray, sr: int) -> np.ndarray:
    """Linear fade out over last 0.5s."""
    n = min(int(sr * 0.5), len(samples))
    out = samples.copy()
    out[-n:] *= np.linspace(1, 0, n).astype(np.float32)
    return out


def reverse(samples: np.ndarray, sr: int) -> np.ndarray:
    return samples[::-1].copy()


def silence_selection(samples: np.ndarray, sr: int) -> np.ndarray:
    out = samples.copy()
    out[:] = 0.0
    return out


def amplify_2x(samples: np.ndarray, sr: int) -> np.ndarray:
    out = samples * 2.0
    np.clip(out, -1.0, 1.0, out=out)
    return out.astype(np.float32)


def reduce_half(samples: np.ndarray, sr: int) -> np.ndarray:
    return (samples * 0.5).astype(np.float32)


def bass_boost(samples: np.ndarray, sr: int) -> np.ndarray:
    """Boost frequencies below 300 Hz by +8dB."""
    nyq = sr / 2.0
    b, a = sig.butter(3, 300 / nyq, btype="low")
    low = sig.lfilter(b, a, samples).astype(np.float32)
    out = samples + low * 1.5
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out.astype(np.float32)


def treble_boost(samples: np.ndarray, sr: int) -> np.ndarray:
    """Boost frequencies above 4kHz by +6dB."""
    nyq = sr / 2.0
    b, a = sig.butter(3, 4000 / nyq, btype="high")
    high = sig.lfilter(b, a, samples).astype(np.float32)
    out = samples + high * 1.0
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out.astype(np.float32)


def telephone(samples: np.ndarray, sr: int) -> np.ndarray:
    """Bandpass 300-3400 Hz like a phone line."""
    nyq = sr / 2.0
    lo = max(300 / nyq, 0.001)
    hi = min(3400 / nyq, 0.999)
    b, a = sig.butter(4, [lo, hi], btype="band")
    out = sig.lfilter(b, a, samples).astype(np.float32)
    out *= 1.5
    np.clip(out, -1.0, 1.0, out=out)
    return out


def radio_static(samples: np.ndarray, sr: int) -> np.ndarray:
    """Simulate AM radio: bandpass + static crackle + dropouts."""
    nyq = sr / 2.0
    lo = max(400 / nyq, 0.001)
    hi = min(3000 / nyq, 0.999)
    b, a = sig.butter(3, [lo, hi], btype="band")
    out = sig.lfilter(b, a, samples).astype(np.float32)
    # Add static noise
    rng = np.random.RandomState(7)
    static = rng.randn(len(out)).astype(np.float32) * 0.06
    # Crackle bursts
    for _ in range(len(out) // sr):
        pos = rng.randint(0, max(1, len(out) - 200))
        static[pos:pos + rng.randint(20, 200)] += rng.randn() * 0.15
    # Random short dropouts
    for _ in range(max(1, len(out) // (sr * 2))):
        pos = rng.randint(0, max(1, len(out) - 2000))
        dur = rng.randint(400, 2000)
        out[pos:pos + dur] *= 0.05
    out = out + static
    out *= 1.4
    np.clip(out, -1.0, 1.0, out=out)
    return out


def white_noise_mix(samples: np.ndarray, sr: int) -> np.ndarray:
    """Mix in white noise at -18dB."""
    noise = np.random.RandomState(1).randn(len(samples)).astype(np.float32) * 0.12
    out = samples + noise
    np.clip(out, -1.0, 1.0, out=out)
    return out


def pink_noise_mix(samples: np.ndarray, sr: int) -> np.ndarray:
    """Mix in pink noise (1/f) at -18dB."""
    rng = np.random.RandomState(2)
    white = rng.randn(len(samples)).astype(np.float32)
    # Voss-McCartney approximation
    b = [0.049922035, -0.095993537, 0.050612699, -0.004709510]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    pink = sig.lfilter(b, a, white).astype(np.float32)
    pink *= 0.15 / (np.max(np.abs(pink)) + 1e-8)
    out = samples + pink
    np.clip(out, -1.0, 1.0, out=out)
    return out


def vinyl_crackle(samples: np.ndarray, sr: int) -> np.ndarray:
    """Add vinyl record crackle and pops."""
    rng = np.random.RandomState(3)
    out = samples.copy()
    # Low rumble
    rumble = rng.randn(len(out)).astype(np.float32) * 0.02
    b, a = sig.butter(2, 80 / (sr / 2), btype="low")
    rumble = sig.lfilter(b, a, rumble).astype(np.float32)
    out += rumble
    # Random pops
    num_pops = len(out) // 2000
    for _ in range(num_pops):
        pos = rng.randint(0, max(1, len(out) - 10))
        out[pos] += rng.choice([-1, 1]) * rng.uniform(0.1, 0.35)
    np.clip(out, -1.0, 1.0, out=out)
    return out


def bit_crush(samples: np.ndarray, sr: int) -> np.ndarray:
    """Reduce to 8-bit depth."""
    levels = 256
    out = np.round(samples * (levels / 2)) / (levels / 2)
    return out.astype(np.float32)


def downsample(samples: np.ndarray, sr: int) -> np.ndarray:
    """Downsample to 8kHz quality (sample-and-hold)."""
    factor = max(1, sr // 8000)
    out = samples.copy()
    for i in range(0, len(out), factor):
        out[i:i + factor] = out[i]
    return out


def robot_voice(samples: np.ndarray, sr: int) -> np.ndarray:
    """Ring modulation at 150Hz for robotic effect."""
    t = np.arange(len(samples), dtype=np.float32) / sr
    carrier = np.sin(2 * np.pi * 150 * t).astype(np.float32)
    out = samples * carrier
    return out.astype(np.float32)


def chorus(samples: np.ndarray, sr: int) -> np.ndarray:
    """Simple chorus: mix with pitch-wobbled copy."""
    t = np.arange(len(samples), dtype=np.float32) / sr
    mod = (np.sin(2 * np.pi * 1.5 * t) * 0.002 * sr).astype(np.float32)
    indices = np.arange(len(samples), dtype=np.float32) + mod
    np.clip(indices, 0, len(samples) - 1, out=indices)
    int_idx = indices.astype(int)
    frac = indices - int_idx
    safe = np.minimum(int_idx + 1, len(samples) - 1)
    delayed = samples[int_idx] * (1 - frac) + samples[safe] * frac
    out = (samples * 0.7 + delayed * 0.3).astype(np.float32)
    return out


def tremolo(samples: np.ndarray, sr: int) -> np.ndarray:
    """Amplitude modulation at 6Hz."""
    t = np.arange(len(samples), dtype=np.float32) / sr
    mod = (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)).astype(np.float32)
    return (samples * mod).astype(np.float32)


def distortion(samples: np.ndarray, sr: int) -> np.ndarray:
    """Soft clipping distortion."""
    drive = 4.0
    out = np.tanh(samples * drive).astype(np.float32)
    return out


# Registry: (menu_label, function)
FILTER_REGISTRY = [
    ("Fade In", fade_in),
    ("Fade Out", fade_out),
    ("Reverse", reverse),
    ("Silence", silence_selection),
    ("Amplify 2x", amplify_2x),
    ("Reduce 50%", reduce_half),
    ("Bass Boost", bass_boost),
    ("Treble Boost", treble_boost),
    ("Telephone", telephone),
    ("Radio Static", radio_static),
    ("White Noise", white_noise_mix),
    ("Pink Noise", pink_noise_mix),
    ("Vinyl Crackle", vinyl_crackle),
    ("Bit Crush (8-bit)", bit_crush),
    ("Downsample (8kHz)", downsample),
    ("Robot Voice", robot_voice),
    ("Chorus", chorus),
    ("Tremolo", tremolo),
    ("Distortion", distortion),
    ("Lo-Fi (Crush+Down)", lambda s, sr: downsample(bit_crush(s, sr), sr)),
]
