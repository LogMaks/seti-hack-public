"""
Team B baselines — structure / randomness detectors.

Question: is there non-random structure in the observation?

Each detector returns a BPA:
    {"signal": ..., "noise": ..., "unknown": ...}  with sum == 1
"""

from __future__ import annotations

import numpy as np

from dst import validate_bpa


def _clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def _bpa_from_scores(signal_score: float, confidence: float) -> dict:
    s = _clip01(signal_score)
    c = _clip01(confidence)
    m_signal = c * s
    m_noise = c * (1.0 - s)
    m_unknown = 1.0 - c
    return validate_bpa({"signal": m_signal, "noise": m_noise, "unknown": m_unknown})


def autocorr_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """Strongest lagged autocorrelation peak (excluding lag 0)."""
    del fs  # reserved for future lag-in-seconds thresholds
    x = x - np.mean(x)
    if np.allclose(x, 0):
        return _bpa_from_scores(0.0, 0.2)
    ac = np.correlate(x, x, mode="full")
    ac = ac[len(ac) // 2 :]
    ac = ac / (ac[0] + 1e-20)
    # ignore very small lags (adjacent samples)
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
    # normalized entropy in ~[0,1]; lower → more structured
    h_norm = h / h_max
    score = _clip01((0.85 - h_norm) / 0.35)
    conf = _clip01(abs(0.75 - h_norm) / 0.35)
    return _bpa_from_scores(score, conf)


def periodicity_detector(x: np.ndarray, fs: float = 8000.0) -> dict:
    """
    Simple periodicity score via FFT of the squared signal (crude).

    Looks for a dominant modulation / repetition rate above a noise floor.
    """
    x = x - np.mean(x)
    y = x * x
    y = y - np.mean(y)
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    # skip DC
    if len(spec) < 4:
        return _bpa_from_scores(0.0, 0.2)
    body = spec[1:]
    med = float(np.median(body) + 1e-20)
    peak = float(np.max(body))
    ratio = peak / med
    score = _clip01((ratio - 4.0) / 25.0)
    conf = _clip01((ratio - 2.0) / 20.0)
    return _bpa_from_scores(score, conf)


def run_team_b(x: np.ndarray, fs: float = 8000.0) -> list[dict]:
    """Return list of Team B BPAs (one per detector)."""
    return [
        autocorr_detector(x, fs),
        entropy_detector(x, fs),
        periodicity_detector(x, fs),
    ]


DETECTOR_NAMES_B = ("autocorr", "entropy", "periodicity")
