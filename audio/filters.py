"""20 parameterized destructive filter functions."""

import numpy as np
from scipy import signal as sig


def fade_in(samples, sr, duration=0.5):
    n = min(int(sr * duration), len(samples))
    out = samples.copy()
    out[:n] *= np.linspace(0, 1, n).astype(np.float32)
    return out


def fade_out(samples, sr, duration=0.5):
    n = min(int(sr * duration), len(samples))
    out = samples.copy()
    out[-n:] *= np.linspace(1, 0, n).astype(np.float32)
    return out


def reverse(samples, sr):
    return samples[::-1].copy()


def silence_selection(samples, sr):
    out = samples.copy()
    out[:] = 0.0
    return out


def amplify(samples, sr, gain=2.0):
    out = samples * gain
    np.clip(out, -1.0, 1.0, out=out)
    return out.astype(np.float32)


def reduce_vol(samples, sr, amount=50):
    return (samples * (amount / 100.0)).astype(np.float32)


def bass_boost(samples, sr, freq=300, gain_db=8):
    nyq = sr / 2.0
    f = min(freq, nyq * 0.99) / nyq
    b, a = sig.butter(3, f, btype="low")
    low = sig.lfilter(b, a, samples).astype(np.float32)
    linear = 10 ** (gain_db / 20.0) - 1.0
    out = samples + low * linear
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out.astype(np.float32)


def treble_boost(samples, sr, freq=4000, gain_db=6):
    nyq = sr / 2.0
    f = min(freq, nyq * 0.99) / nyq
    b, a = sig.butter(3, f, btype="high")
    high = sig.lfilter(b, a, samples).astype(np.float32)
    linear = 10 ** (gain_db / 20.0) - 1.0
    out = samples + high * linear
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out.astype(np.float32)


def telephone(samples, sr, lo_hz=300, hi_hz=3400):
    nyq = sr / 2.0
    lo = max(lo_hz / nyq, 0.001)
    hi = min(hi_hz / nyq, 0.999)
    b, a = sig.butter(4, [lo, hi], btype="band")
    out = sig.lfilter(b, a, samples).astype(np.float32)
    out *= 1.5
    np.clip(out, -1.0, 1.0, out=out)
    return out


def radio_static(samples, sr, static_level=60, dropout_rate=50):
    nyq = sr / 2.0
    lo = max(400 / nyq, 0.001)
    hi = min(3000 / nyq, 0.999)
    b, a = sig.butter(3, [lo, hi], btype="band")
    out = sig.lfilter(b, a, samples).astype(np.float32)
    rng = np.random.RandomState(7)
    noise_amp = static_level / 1000.0
    static = rng.randn(len(out)).astype(np.float32) * noise_amp
    for _ in range(len(out) // sr):
        pos = rng.randint(0, max(1, len(out) - 200))
        static[pos:pos + rng.randint(20, 200)] += rng.randn() * noise_amp * 2.5
    n_drops = max(1, int(len(out) / (sr * 2) * dropout_rate / 50))
    for _ in range(n_drops):
        pos = rng.randint(0, max(1, len(out) - 2000))
        dur = rng.randint(400, 2000)
        out[pos:pos + dur] *= 0.05
    out = out + static
    out *= 1.4
    np.clip(out, -1.0, 1.0, out=out)
    return out


def white_noise_mix(samples, sr, level=12):
    noise = np.random.RandomState(1).randn(len(samples)).astype(np.float32) * (level / 100.0)
    out = samples + noise
    np.clip(out, -1.0, 1.0, out=out)
    return out


def pink_noise_mix(samples, sr, level=15):
    rng = np.random.RandomState(2)
    white = rng.randn(len(samples)).astype(np.float32)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004709510]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    pink = sig.lfilter(b, a, white).astype(np.float32)
    pink *= (level / 100.0) / (np.max(np.abs(pink)) + 1e-8)
    out = samples + pink
    np.clip(out, -1.0, 1.0, out=out)
    return out


def vinyl_crackle(samples, sr, intensity=50):
    rng = np.random.RandomState(3)
    out = samples.copy()
    rumble = rng.randn(len(out)).astype(np.float32) * 0.02 * (intensity / 50)
    b, a = sig.butter(2, 80 / (sr / 2), btype="low")
    rumble = sig.lfilter(b, a, rumble).astype(np.float32)
    out += rumble
    num_pops = int(len(out) / 2000 * intensity / 50)
    for _ in range(max(1, num_pops)):
        pos = rng.randint(0, max(1, len(out) - 10))
        out[pos] += rng.choice([-1, 1]) * rng.uniform(0.1, 0.35)
    np.clip(out, -1.0, 1.0, out=out)
    return out


def bit_crush(samples, sr, bits=8):
    levels = 2 ** int(bits)
    out = np.round(samples * (levels / 2)) / (levels / 2)
    return out.astype(np.float32)


def downsample(samples, sr, target_rate=8000):
    factor = max(1, sr // int(target_rate))
    out = samples.copy()
    for i in range(0, len(out), factor):
        out[i:i + factor] = out[i]
    return out


def robot_voice(samples, sr, freq=150):
    t = np.arange(len(samples), dtype=np.float32) / sr
    carrier = np.sin(2 * np.pi * freq * t).astype(np.float32)
    return (samples * carrier).astype(np.float32)


def chorus_fx(samples, sr, rate=1.5, depth=50):
    t = np.arange(len(samples), dtype=np.float32) / sr
    mod = (np.sin(2 * np.pi * rate * t) * (depth / 100.0) * 0.004 * sr).astype(np.float32)
    indices = np.arange(len(samples), dtype=np.float32) + mod
    np.clip(indices, 0, len(samples) - 1, out=indices)
    int_idx = indices.astype(int)
    frac = indices - int_idx
    safe = np.minimum(int_idx + 1, len(samples) - 1)
    delayed = samples[int_idx] * (1 - frac) + samples[safe] * frac
    return (samples * 0.7 + delayed * 0.3).astype(np.float32)


def tremolo(samples, sr, rate=6.0, depth=100):
    t = np.arange(len(samples), dtype=np.float32) / sr
    d = depth / 100.0
    mod = (1.0 - d * 0.5 + d * 0.5 * np.sin(2 * np.pi * rate * t)).astype(np.float32)
    return (samples * mod).astype(np.float32)


def distortion(samples, sr, drive=4.0):
    return np.tanh(samples * drive).astype(np.float32)


def lofi(samples, sr, bits=8, target_rate=8000):
    return downsample(bit_crush(samples, sr, bits), sr, target_rate)


# ── Registry ─────────────────────────────────────────────────────
# (label, function, [(param_label, kwarg_name, min, max, default, step)])

FILTER_DEFS = [
    ("Fade In", fade_in, [
        ("Duration", "duration", 0.05, 5.0, 0.5, 0.05),
    ]),
    ("Fade Out", fade_out, [
        ("Duration", "duration", 0.05, 5.0, 0.5, 0.05),
    ]),
    ("Reverse", reverse, []),
    ("Silence", silence_selection, []),
    ("Amplify", amplify, [
        ("Gain", "gain", 1.0, 8.0, 2.0, 0.1),
    ]),
    ("Reduce", reduce_vol, [
        ("Amount %", "amount", 5, 95, 50, 5),
    ]),
    ("Bass Boost", bass_boost, [
        ("Freq Hz", "freq", 80, 500, 300, 10),
        ("Gain dB", "gain_db", 1, 18, 8, 1),
    ]),
    ("Treble Boost", treble_boost, [
        ("Freq Hz", "freq", 2000, 10000, 4000, 100),
        ("Gain dB", "gain_db", 1, 18, 6, 1),
    ]),
    ("Telephone", telephone, [
        ("Low Hz", "lo_hz", 100, 1000, 300, 50),
        ("High Hz", "hi_hz", 2000, 5000, 3400, 50),
    ]),
    ("Radio Static", radio_static, [
        ("Static", "static_level", 10, 200, 60, 5),
        ("Dropouts", "dropout_rate", 0, 100, 50, 5),
    ]),
    ("White Noise", white_noise_mix, [
        ("Level %", "level", 1, 50, 12, 1),
    ]),
    ("Pink Noise", pink_noise_mix, [
        ("Level %", "level", 1, 50, 15, 1),
    ]),
    ("Vinyl Crackle", vinyl_crackle, [
        ("Intensity", "intensity", 10, 100, 50, 5),
    ]),
    ("Bit Crush", bit_crush, [
        ("Bits", "bits", 2, 16, 8, 1),
    ]),
    ("Downsample", downsample, [
        ("Rate Hz", "target_rate", 1000, 22050, 8000, 500),
    ]),
    ("Robot Voice", robot_voice, [
        ("Freq Hz", "freq", 30, 500, 150, 5),
    ]),
    ("Chorus", chorus_fx, [
        ("Rate Hz", "rate", 0.1, 8.0, 1.5, 0.1),
        ("Depth %", "depth", 10, 100, 50, 5),
    ]),
    ("Tremolo", tremolo, [
        ("Rate Hz", "rate", 0.5, 20.0, 6.0, 0.5),
        ("Depth %", "depth", 10, 100, 100, 5),
    ]),
    ("Distortion", distortion, [
        ("Drive", "drive", 1.0, 20.0, 4.0, 0.5),
    ]),
    ("Lo-Fi", lofi, [
        ("Bits", "bits", 2, 16, 8, 1),
        ("Rate Hz", "target_rate", 1000, 22050, 8000, 500),
    ]),
]

# Flat registry for menu (backwards compat)
FILTER_REGISTRY = [(label, fn) for label, fn, _ in FILTER_DEFS]
