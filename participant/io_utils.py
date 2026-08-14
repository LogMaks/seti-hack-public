"""Load observation waveforms and lightweight metadata."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_observation(path: str | Path) -> tuple[np.ndarray, dict]:
    """
    Load an observation from a .npy file.

    Optional sidecar: same stem with .json (e.g. obs_s0.npy + obs_s0.json).
    Public metadata may include: id, fs, n_samples, round — never labels.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    x = np.load(path).astype(float).ravel()

    meta = {
        "id": path.stem,
        "fs": 8000.0,
        "n_samples": int(x.size),
        "path": str(path),
    }

    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        import json

        with sidecar.open() as f:
            meta.update(json.load(f))
        meta["n_samples"] = int(x.size)

    return x, meta


def save_observation(path: str | Path, x: np.ndarray, meta: dict | None = None) -> None:
    """Save waveform (+ optional public JSON sidecar). For local experiments only."""
    import json

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.asarray(x, dtype=float))
    if meta is not None:
        payload = {k: v for k, v in meta.items() if k != "path"}
        with path.with_suffix(".json").open("w") as f:
            json.dump(payload, f, indent=2)
