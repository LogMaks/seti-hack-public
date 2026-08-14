"""
Toy observation generator for local experiments.

Generates ONLY simple public examples:
  - noise
  - sine + noise

This is not the organizer scenario pack and does not encode any hidden message.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from io_utils import save_observation


def noise_only(n: int, fs: float, seed: int, sigma: float = 1.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, sigma, size=n)


def sine_plus_noise(
    n: int,
    fs: float,
    seed: int,
    freq: float = 500.0,
    amp: float = 1.0,
    snr_db: float = 5.0,
) -> np.ndarray:
    """Tone in AWGN. snr_db ≈ 10 log10(amp^2 / (2 sigma^2)) for a sine."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / fs
    s = amp * np.sin(2 * np.pi * freq * t)
    # sigma from desired SNR for sine power amp^2/2
    sig_pow = (amp**2) / 2.0
    sigma = np.sqrt(sig_pow / (10 ** (snr_db / 10.0)))
    return s + rng.normal(0.0, sigma, size=n)


def write_examples(out_dir: str | Path = "data") -> None:
    out = Path(out_dir)
    fs = 8000.0
    n = 8000  # 1 second

    x0 = noise_only(n, fs, seed=0)
    save_observation(
        out / "example_noise.npy",
        x0,
        {"id": "example_noise", "fs": fs, "kind": "toy_noise", "seed": 0},
    )

    x1 = sine_plus_noise(n, fs, seed=1, freq=500.0, snr_db=8.0)
    save_observation(
        out / "example_sine.npy",
        x1,
        {"id": "example_sine", "fs": fs, "kind": "toy_sine", "seed": 1, "freq": 500.0},
    )

    print(f"wrote examples to {out.resolve()}")


if __name__ == "__main__":
    write_examples()
