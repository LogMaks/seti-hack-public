#!/usr/bin/env python3
"""
One observation: load → 6 detectors → majority / mean / DST → team policy.

Canon: DST on all six detector BPAs.

    python generator_example.py
    python main.py data/example_noise.npy
    python main.py data/example_sine.npy --human
"""

from __future__ import annotations

import argparse
from pathlib import Path

from decision import compare_baselines, human_review_prompt
from detectors import DETECTOR_NAMES, run_detectors
from dst import summarize
from io_utils import load_observation


def _fmt_bpa(m: dict) -> str:
    return f"signal={m['signal']:.3f}  noise={m['noise']:.3f}  unknown={m['unknown']:.3f}"


def _fmt_dst(dst: dict) -> str:
    k = dst["max_conflict"]
    if dst.get("refused") or dst["mass"] is None:
        return f"refused  K={k:.3f}"
    return f"{dst['decision']}  {_fmt_bpa(dst['mass'])}  K={k:.3f}"


def analyze(path: Path, ask_human: bool = False) -> dict:
    x, meta = load_observation(path)
    fs = float(meta.get("fs", 8000.0))
    masses = run_detectors(x, fs)

    print(f"\nObservation: {meta.get('id', path.name)}  n={len(x)}  fs={fs}")
    print("\n--- Detectors (6 sources) ---")
    for name, m in zip(DETECTOR_NAMES, masses):
        print(f"  {name:12s}  {_fmt_bpa(m)}")

    report = compare_baselines(masses)
    print("\n--- Baselines ---")
    print(f"  majority → {report['majority']['decision']}  {report['majority']['votes']}")
    print(f"  mean     → {report['mean']['decision']}  {_fmt_bpa(report['mean']['mass'])}")
    print(f"  DST      → {_fmt_dst(report['dst'])}")
    print(f"  policy   → {report['policy']}")

    fused = report["dst"]["mass"]
    if fused is not None:
        s = summarize(fused)
        print("\n--- Bel / Pl (DST) ---")
        print(f"  Bel {s['belief']}")
        print(f"  Pl  {s['plausibility']}")
    else:
        print("\n--- Bel / Pl --- combination refused (total conflict)")

    human = None
    if ask_human:
        human = human_review_prompt(str(meta.get("id", path.name)), report)
    elif report["policy"]["action"] == "HUMAN_REVIEW":
        print("\n(write a team verdict — re-run with --human)")

    return {"meta": meta, "masses": masses, "report": report, "human": human}


def main() -> None:
    p = argparse.ArgumentParser(description="SETI/DST hack — analyze one observation")
    p.add_argument("observation", type=Path, help="path to .npy observation")
    p.add_argument("--human", action="store_true", help="enter team verdict")
    args = p.parse_args()
    analyze(args.observation, ask_human=args.human)


if __name__ == "__main__":
    main()
