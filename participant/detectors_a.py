"""
Team A baselines — spectral / energy detectors.

Question: is there a physically distinguishable signal (vs noise-like spectrum)?

Each detector returns a BPA:
    {"signal": ..., "noise": ..., "unknown": ...}  with sum == 1
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
    # map ~0..20 dB → score; confidence grows with extreme SNR
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
    # noise-like ≈ top_k / n_bins; structured → larger fraction
    n = len(pxx)
    baseline = top_k / max(n, 1)
    score = _clip01((frac - baseline) / max(1e-6, 0.35 - baseline))
    conf = _clip01((frac - baseline) / 0.25)
    return _bpa_from_scores(score, conf)


def run_team_a(x: np.ndarray, fs: float = 8000.0) -> list[dict]:
    """Return list of Team A BPAs (one per detector)."""
    return [
        snr_detector(x, fs),
        fft_peak_detector(x, fs),
        band_energy_detector(x, fs),
    ]


DETECTOR_NAMES_A = ("snr", "fft_peak", "band_energy")
