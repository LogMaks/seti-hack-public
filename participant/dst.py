"""
Minimal Dempster–Shafer Theory for a binary frame of discernment.

    Θ = {signal, noise}

A basic probability assignment (BPA) is a dict:

    {"signal": m({signal}), "noise": m({noise}), "unknown": m(Θ)}

with non-negative masses that sum to 1.
"unknown" is ignorance mass on the whole frame — not a third class.
"""

from __future__ import annotations

from typing import Iterable


HYPOTHESES = ("signal", "noise")


def validate_bpa(m: dict) -> dict:
    """Return a normalized copy; raise if keys/masses are invalid."""
    required = {"signal", "noise", "unknown"}
    if set(m) != required:
        raise ValueError(f"BPA keys must be exactly {required}, got {set(m)}")
    vals = {k: float(m[k]) for k in ("signal", "noise", "unknown")}
    if any(v < -1e-12 for v in vals.values()):
        raise ValueError(f"negative mass in {vals}")
    s = sum(vals.values())
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"masses must sum to 1, got {s}")
    # tiny numerical cleanup
    vals["unknown"] = 1.0 - vals["signal"] - vals["noise"]
    return vals


def belief(m: dict) -> dict:
    """Bel(A) = m(A) for singletons; ignorance is not believed."""
    m = validate_bpa(m)
    return {"signal": m["signal"], "noise": m["noise"]}


def plausibility(m: dict) -> dict:
    """Pl(A) = m(A) + m(Θ)."""
    m = validate_bpa(m)
    return {
        "signal": m["signal"] + m["unknown"],
        "noise": m["noise"] + m["unknown"],
    }


def conflict(m1: dict, m2: dict) -> float:
    """Dempster conflict K between two BPAs (before normalization)."""
    a, b = validate_bpa(m1), validate_bpa(m2)
    return a["signal"] * b["noise"] + a["noise"] * b["signal"]


def combine(m1: dict, m2: dict) -> tuple[dict, float]:
    """
    Dempster's rule for two BPAs.

    Returns (combined_bpa, conflict_K).
    If K → 1, combination is ill-conditioned (strong contradiction).
    """
    a, b = validate_bpa(m1), validate_bpa(m2)
    k = a["signal"] * b["noise"] + a["noise"] * b["signal"]
    if k >= 1.0 - 1e-12:
        # Total conflict: keep raw product masses unnormalized marker
        raise ValueError(f"total conflict K={k:.6f}; refuse to combine")

    norm = 1.0 - k
    signal = (a["signal"] * b["signal"] + a["signal"] * b["unknown"] + a["unknown"] * b["signal"]) / norm
    noise = (a["noise"] * b["noise"] + a["noise"] * b["unknown"] + a["unknown"] * b["noise"]) / norm
    unknown = (a["unknown"] * b["unknown"]) / norm
    return validate_bpa({"signal": signal, "noise": noise, "unknown": unknown}), k


def combine_many(masses: Iterable[dict]) -> tuple[dict, list[float]]:
    """Sequentially combine BPAs; returns (fused, list of pairwise K)."""
    masses = list(masses)
    if not masses:
        raise ValueError("empty mass list")
    fused = validate_bpa(masses[0])
    ks: list[float] = []
    for m in masses[1:]:
        fused, k = combine(fused, m)
        ks.append(k)
    return fused, ks


def mean_bpa(masses: Iterable[dict]) -> dict:
    """Component-wise mean of BPAs (baseline, not a DST rule)."""
    masses = [validate_bpa(m) for m in masses]
    if not masses:
        raise ValueError("empty mass list")
    n = len(masses)
    return validate_bpa(
        {
            "signal": sum(m["signal"] for m in masses) / n,
            "noise": sum(m["noise"] for m in masses) / n,
            "unknown": sum(m["unknown"] for m in masses) / n,
        }
    )


def summarize(m: dict) -> dict:
    """Handy bundle for printing / reports."""
    m = validate_bpa(m)
    bel = belief(m)
    pl = plausibility(m)
    return {"mass": m, "belief": bel, "plausibility": pl}
