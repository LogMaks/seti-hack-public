#!/usr/bin/env python3
"""
Bonus decode sketch: matched filter → bits → ASCII.

You choose carrier frequency (--f0) and samples per bit (--spb)
from your own analysis of the observation. Nothing is pre-filled.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from io_utils import load_observation


def matched_bits(x: np.ndarray, fs: float, f0: float, spb: int) -> list[int]:
    """One bit per block: sign of correlation with a reference sine."""
    n = (len(x) // spb) * spb
    x = x[:n]
    t = np.arange(spb) / fs
    ref = np.sin(2 * np.pi * f0 * t)
    bits: list[int] = []
    for i in range(0, n, spb):
        block = x[i : i + spb]
        score = float(np.dot(block, ref))
        bits.append(1 if score >= 0 else 0)
    return bits


def bits_to_bytes(bits: list[int], msb_first: bool = True) -> bytes:
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        chunk = bits[i : i + 8]
        val = 0
        for b in chunk if msb_first else reversed(chunk):
            val = (val << 1) | b
        out.append(val)
    return bytes(out)


def strip_preamble(bits: list[int], pattern: str = "10") -> tuple[list[int], int]:
    """Drop a leading alternating preamble if present; return (payload, cut)."""
    pat = [int(c) for c in pattern]
    cut = 0
    while cut + len(pat) <= len(bits) and bits[cut : cut + len(pat)] == pat:
        cut += len(pat)
    if cut == 0:
        pat2 = [int(c) for c in pattern[::-1]]
        while cut + len(pat2) <= len(bits) and bits[cut : cut + len(pat2)] == pat2:
            cut += len(pat2)
    return bits[cut:], cut


def main() -> None:
    p = argparse.ArgumentParser(
        description="Bonus matched-filter decode — pass carrier and symbol length yourself"
    )
    p.add_argument("observation", type=Path, help="path to .npy observation")
    p.add_argument(
        "--f0",
        type=float,
        required=True,
        help="carrier frequency in Hz (estimate from spectrum yourself)",
    )
    p.add_argument(
        "--spb",
        type=int,
        required=True,
        help="samples per bit (estimate from structure yourself)",
    )
    p.add_argument("--show-bits", type=int, default=64, help="print first N bits")
    args = p.parse_args()

    x, meta = load_observation(args.observation)
    fs = float(meta.get("fs", 8000.0))

    bits = matched_bits(x, fs, args.f0, args.spb)
    print(f"n={len(x)}  fs={fs}  f0={args.f0}  spb={args.spb}  bits={len(bits)}")
    print("first bits:", "".join(str(b) for b in bits[: args.show_bits]))

    payload, cut = strip_preamble(bits)
    print(f"preamble cut ≈ {cut} bits")

    raw = bits_to_bytes(payload, msb_first=True)
    text = raw.decode("ascii", errors="replace")
    print("ASCII (MSB first):", repr(text))
    print("printable:        ", "".join(ch if 32 <= ord(ch) < 127 else "." for ch in text))


if __name__ == "__main__":
    main()
