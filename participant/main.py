#!/usr/bin/env python3
"""
Single-observation experiment pipeline.

    load → Team A detectors → Team B detectors
         → majority / mean / DST
         → HITL policy → optional human input

Usage:
    python generator_example.py
    python main.py data/example_noise.npy
    python main.py data/example_sine.npy
    python main.py data/example_sine.npy --human
"""

from __future__ import annotations

import argparse
from pathlib import Path

from decision import compare_baselines, human_review_prompt
from detectors_a import DETECTOR_NAMES_A, run_team_a
from detectors_b import DETECTOR_NAMES_B, run_team_b
from dst import mean_bpa, summarize
from io_utils import load_observation


def _fmt_bpa(m: dict) -> str:
    return (
        f"signal={m['signal']:.3f}  noise={m['noise']:.3f}  "
        f"unknown={m['unknown']:.3f}"
    )


def analyze(path: Path, ask_human: bool = False) -> dict:
    x, meta = load_observation(path)
    fs = float(meta.get("fs", 8000.0))

    bpa_a = run_team_a(x, fs)
    bpa_b = run_team_b(x, fs)

    print(f"\nObservation: {meta.get('id', path.name)}  n={len(x)}  fs={fs}")
    print("\n--- Team A (spectral) ---")
    for name, m in zip(DETECTOR_NAMES_A, bpa_a):
        print(f"  {name:12s}  {_fmt_bpa(m)}")

    print("\n--- Team B (structure) ---")
    for name, m in zip(DETECTOR_NAMES_B, bpa_b):
        print(f"  {name:12s}  {_fmt_bpa(m)}")

    # Team-level summaries (mean BPA), then fuse the two teams with DST
    team_a = mean_bpa(bpa_a)
    team_b = mean_bpa(bpa_b)
    print("\n--- Team means ---")
    print(f"  A mean       {_fmt_bpa(team_a)}")
    print(f"  B mean       {_fmt_bpa(team_b)}")

    # Compare baselines on: all detectors + on the two team means
    all_masses = bpa_a + bpa_b
    report_all = compare_baselines(all_masses)
    report_teams = compare_baselines([team_a, team_b])

    print("\n--- Baselines on all 6 detectors ---")
    print(f"  majority → {report_all['majority']['decision']}  {report_all['majority']['votes']}")
    print(f"  mean     → {report_all['mean']['decision']}  {_fmt_bpa(report_all['mean']['mass'])}")
    print(
        f"  DST      → {report_all['dst']['decision']}  "
        f"{_fmt_bpa(report_all['dst']['mass'])}  "
        f"maxK={report_all['dst']['max_conflict']:.3f}"
    )
    print(f"  policy   → {report_all['policy']}")

    print("\n--- Baselines on team means (A vs B) ---")
    print(f"  majority → {report_teams['majority']['decision']}")
    print(f"  mean     → {report_teams['mean']['decision']}  {_fmt_bpa(report_teams['mean']['mass'])}")
    print(
        f"  DST      → {report_teams['dst']['decision']}  "
        f"{_fmt_bpa(report_teams['dst']['mass'])}  "
        f"K={report_teams['dst']['max_conflict']:.3f}"
    )
    print(f"  policy   → {report_teams['policy']}")

    summary = summarize(report_teams["dst"]["mass"])
    print("\n--- Bel / Pl (team-level DST) ---")
    print(f"  Bel {summary['belief']}")
    print(f"  Pl  {summary['plausibility']}")

    human = None
    if ask_human:
        human = human_review_prompt(str(meta.get("id", path.name)), report_teams)
    elif report_teams["policy"]["action"] == "HUMAN_REVIEW":
        print("\n(HITL recommended — re-run with --human to enter a decision)")

    return {
        "meta": meta,
        "team_a": team_a,
        "team_b": team_b,
        "report_all": report_all,
        "report_teams": report_teams,
        "human": human,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="SETI/DST hack — analyze one observation")
    p.add_argument("observation", type=Path, help="path to .npy observation")
    p.add_argument("--human", action="store_true", help="force human review prompt")
    args = p.parse_args()
    analyze(args.observation, ask_human=args.human)


if __name__ == "__main__":
    main()
