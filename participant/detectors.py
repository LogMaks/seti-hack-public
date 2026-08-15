"""
Six baseline detectors — independent evidence sources for one team.

Each detector returns a BPA:
    {"signal": ..., "noise": ..., "unknown": ...}  with sum == 1

`unknown` is m(Θ), not a third class.
"""

from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from dst import validate_bpa


def _clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def _bpa_from_scores(signal_score: float, confidence: float) -> dict:
    """
    Map a [0,1] signal_score and confidence into a BPA.

    High confidence + high score  → mass on signal
    High confidence + low score   → mass on noise
    Low confidence                → mass on Θ (unknown)
    """
    s = _clip01(signal_score)
    c = _clip01(confidence)
    m_signal = c * s
    m_noise = c * (1.0 - s)
    m_unknown = 1.0 - c
    return validate_bpa({"signal": m_signal, "noise": m_noise, "unknown": m_unknown})


def _psd(x: np.ndarray, fs: float):
    nperseg = min(256, max(32, len(x) // 4))
    f, pxx = sp_signal.welch(x, fs=fs, nperseg=nperseg)
    return f, pxx


def snr_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """Peak PSD vs median PSD as a crude SNR proxy."""
    _, pxx = _psd(x, fs)
    med = float(np.median(pxx) + 1e-20)
    peak = float(np.max(pxx))
    snr_db = 10.0 * np.log10(peak / med)
    score = _clip01((snr_db - 3.0) / 12.0)
    conf = _clip01(abs(snr_db - 6.0) / 10.0)
    return _bpa_from_scores(score, conf)


def fft_peak_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """Narrow spectral peak: max / median of magnitude spectrum."""
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    med = float(np.median(spec) + 1e-20)
    peak = float(np.max(spec))
    ratio = peak / med
    score = _clip01((ratio - 5.0) / 40.0)
    conf = _clip01((ratio - 3.0) / 30.0)
    return _bpa_from_scores(score, conf)


def band_energy_detector(x: np.ndarray, fs: float = 8000.0, top_k: int = 3) -> dict:
    """Fraction of PSD energy in the top-k bins (spectral concentration)."""
    _, pxx = _psd(x, fs)
    total = float(np.sum(pxx) + 1e-20)
    top = float(np.sort(pxx)[-top_k:].sum())
    frac = top / total
    n = len(pxx)
    baseline = top_k / max(n, 1)
    score = _clip01((frac - baseline) / max(1e-6, 0.35 - baseline))
    conf = _clip01((frac - baseline) / 0.25)
    return _bpa_from_scores(score, conf)


def autocorr_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """Strongest lagged autocorrelation peak (excluding lag 0)."""
    del fs
    x = x - np.mean(x)
    if np.allclose(x, 0):
        return _bpa_from_scores(0.0, 0.2)
    ac = np.correlate(x, x, mode="full")
    ac = ac[len(ac) // 2 :]
    ac = ac / (ac[0] + 1e-20)
    min_lag = max(2, len(x) // 200)
    if min_lag >= len(ac):
        return _bpa_from_scores(0.0, 0.2)
    peak = float(np.max(ac[min_lag:]))
    score = _clip01((peak - 0.15) / 0.5)
    conf = _clip01((peak - 0.05) / 0.4)
    return _bpa_from_scores(score, conf)


def entropy_detector(x: np.ndarray, fs: float = 8000.0, bins: int = 32) -> dict:
    """
    Shannon entropy of the amplitude histogram.

    Lower entropy than a comparable Gaussian noise draw → more structure.
    """
    del fs
    x = x - np.mean(x)
    std = float(np.std(x) + 1e-20)
    xn = x / std
    hist, _ = np.histogram(xn, bins=bins, range=(-4, 4), density=False)
    p = hist.astype(float)
    p = p / (p.sum() + 1e-20)
    p = p[p > 0]
    h = float(-np.sum(p * np.log2(p)))
    h_max = np.log2(bins)
    h_norm = h / h_max
    score = _clip01((0.85 - h_norm) / 0.35)
    conf = _clip01(abs(0.75 - h_norm) / 0.35)
    return _bpa_from_scores(score, conf)


def periodicity_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """
    Periodicity score via FFT of the squared signal.

    Looks for a dominant modulation / repetition rate above a noise floor.
    """
    x = x - np.mean(x)
    y = x * x
    y = y - np.mean(y)
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    if len(spec) < 4:
        return _bpa_from_scores(0.0, 0.2)
    body = spec[1:]
    med = float(np.median(body) + 1e-20)
    peak = float(np.max(body))
    ratio = peak / med
    score = _clip01((ratio - 4.0) / 25.0)
    conf = _clip01((ratio - 2.0) / 20.0)
    return _bpa_from_scores(score, conf)


DETECTORS = (
    ("snr", snr_detector),
    ("fft_peak", fft_peak_detector),
    ("band_energy", band_energy_detector),
    ("autocorr", autocorr_detector),
    ("entropy", entropy_detector),
    ("periodicity", periodicity_detector),
)

DETECTOR_NAMES = tuple(name for name, _ in DETECTORS)


def run_detectors(x: np.ndarray, fs: float = 8000.0) -> list[dict]:
    """Return one BPA per detector (six sources)."""
    return [fn(x, fs) for _, fn in DETECTORS]
