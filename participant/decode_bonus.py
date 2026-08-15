#!/usr/bin/env python3
"""
Bonus decode sketch: matched filter → bits → ASCII.

You still choose --f0 (carrier from spectrum).
If samples-per-bit is unclear, use --scan-spb to try lengths that fit
an integer number of carrier periods (common for this kind of signal).
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


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    ok = sum(1 for ch in text if 32 <= ord(ch) < 127)
    return ok / len(text)


def alternating_prefix(bits: list[int], max_n: int = 32) -> int:
    """How many leading bits follow 1010… or 0101…"""
    if len(bits) < 2:
        return 0
    best = 0
    for start in (0, 1):
        n = 0
        for i, b in enumerate(bits[:max_n]):
            if b == ((start + i) % 2):
                n += 1
            else:
                break
        best = max(best, n)
    return best


def candidate_spb(fs: float, f0: float, periods_min: int = 2, periods_max: int = 12) -> list[int]:
    """
    Symbol lengths that cover an integer number of carrier periods.
    periods_per_bit = spb * f0 / fs  ∈ ℤ  →  spb = k * fs / f0
    """
    out: list[int] = []
    for k in range(periods_min, periods_max + 1):
        spb = int(round(k * fs / f0))
        if spb < 8:
            continue
        # keep only near-integer period fits
        periods = spb * f0 / fs
        if abs(periods - round(periods)) > 0.02:
            continue
        if spb not in out:
            out.append(spb)
    return out


def score_spb(x: np.ndarray, fs: float, f0: float, spb: int) -> dict:
    bits = matched_bits(x, fs, f0, spb)
    alt = alternating_prefix(bits)
    payload, cut = strip_preamble(bits)
    raw = bits_to_bytes(payload, msb_first=True)
    text = raw.decode("ascii", errors="replace")
    pr = printable_ratio(text)
    # prefer long alternating head + readable ASCII after preamble cut
    score = alt * 0.5 + cut * 0.3 + pr * 40.0
    return {
        "spb": spb,
        "periods": spb * f0 / fs,
        "alt": alt,
        "preamble_cut": cut,
        "printable": pr,
        "score": score,
        "preview": "".join(ch if 32 <= ord(ch) < 127 else "." for ch in text[:24]),
        "first_bits": "".join(str(b) for b in bits[:32]),
    }


def scan_spb(x: np.ndarray, fs: float, f0: float) -> list[dict]:
    cands = candidate_spb(fs, f0)
    scored = [score_spb(x, fs, f0, spb) for spb in cands]
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored


def decode_one(x: np.ndarray, fs: float, f0: float, spb: int, show_bits: int) -> None:
    bits = matched_bits(x, fs, f0, spb)
    print(f"n={len(x)}  fs={fs}  f0={f0}  spb={spb}  bits={len(bits)}")
    print(f"periods/bit ≈ {spb * f0 / fs:.3f}")
    print("first bits:", "".join(str(b) for b in bits[:show_bits]))

    payload, cut = strip_preamble(bits)
    print(f"preamble cut ≈ {cut} bits")

    raw = bits_to_bytes(payload, msb_first=True)
    text = raw.decode("ascii", errors="replace")
    print("ASCII (MSB first):", repr(text))
    print("printable:        ", "".join(ch if 32 <= ord(ch) < 127 else "." for ch in text))


def main() -> None:
    p = argparse.ArgumentParser(
        description="Bonus matched-filter decode — set --f0; use --spb or --scan-spb"
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
        default=None,
        help="samples per bit (if known)",
    )
    p.add_argument(
        "--scan-spb",
        action="store_true",
        help="try symbol lengths with an integer number of carrier periods",
    )
    p.add_argument("--show-bits", type=int, default=64, help="print first N bits")
    args = p.parse_args()

    if args.spb is None and not args.scan_spb:
        p.error("pass --spb N  or  --scan-spb  (kids often get stuck on symbol length)")

    x, meta = load_observation(args.observation)
    fs = float(meta.get("fs", 8000.0))

    if args.scan_spb:
        print(f"scan spb for f0={args.f0} Hz, fs={fs}")
        print("hint: look for long 1010… head and readable ASCII preview\n")
        ranked = scan_spb(x, fs, args.f0)
        if not ranked:
            print("no candidates — check --f0")
            return
        print(f"{'spb':>5}  {'per':>6}  {'alt':>3}  {'cut':>3}  {'print':>5}  preview")
        for row in ranked[:8]:
            print(
                f"{row['spb']:5d}  {row['periods']:6.2f}  {row['alt']:3d}  "
                f"{row['preamble_cut']:3d}  {row['printable']:5.2f}  {row['preview']!r}"
            )
        best = ranked[0]
        print(f"\nbest guess spb={best['spb']}  first bits={best['first_bits']}")
        print(f"decode with:  python decode_bonus.py {args.observation} --f0 {args.f0} --spb {best['spb']}")
        if args.spb is None:
            print("\n--- decode with best guess ---")
            decode_one(x, fs, args.f0, best["spb"], args.show_bits)
            return

    decode_one(x, fs, args.f0, args.spb, args.show_bits)


if __name__ == "__main__":
    main()
