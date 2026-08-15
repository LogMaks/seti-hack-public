#!/usr/bin/env python3
"""
One observation: load → 6 detectors → majority / mean / DST → team policy.

Canon: DST on all six detector BPAs.

    python generator_example.py
    python main.py data/example_noise.npy
    python main.py data/example_sine.npy --plot
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


def plot_report(obs_id: str, names: tuple[str, ...], masses: list[dict], report: dict) -> None:
    """Two-panel figure: detector BPAs + DST Bel / K / m(Θ)."""
    import matplotlib.pyplot as plt
    import numpy as np

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    fig.suptitle(f"{obs_id} — detectors & DST", fontsize=11)

    x = np.arange(len(names))
    w = 0.25
    sig = [m["signal"] for m in masses]
    noi = [m["noise"] for m in masses]
    unk = [m["unknown"] for m in masses]
    ax0.bar(x - w, sig, w, label="signal", color="#3dffa8")
    ax0.bar(x, noi, w, label="noise", color="#7f9a92")
    ax0.bar(x + w, unk, w, label="unknown", color="#e8b84a")
    ax0.set_xticks(x)
    ax0.set_xticklabels(names, rotation=30, ha="right")
    ax0.set_ylim(0, 1.05)
    ax0.set_ylabel("mass")
    ax0.set_title("6 detector BPA")
    ax0.legend(fontsize=8, loc="upper right")

    dst = report["dst"]
    policy = report["policy"]
    if dst.get("refused") or dst["mass"] is None:
        ax1.bar([0], [dst["max_conflict"]], color="#e8b84a")
        ax1.set_xticks([0])
        ax1.set_xticklabels(["maxK"])
        ax1.set_ylim(0, 1.05)
        ax1.set_title("DST refused (total conflict)")
        ax1.text(0.5, 0.92, f"policy: {policy['action']}", transform=ax1.transAxes,
                 ha="center", fontsize=9, color="#e8b84a")
    else:
        bel = dst["belief"] or summarize(dst["mass"])["belief"]
        vals = [
            bel["signal"],
            bel["noise"],
            dst["max_conflict"],
            dst["mass"]["unknown"],
        ]
        labels = ["Bel(s)", "Bel(n)", "maxK", "m(Θ)"]
        colors = ["#3dffa8", "#7f9a92", "#e8b84a", "#5ec4ff"]
        ax1.bar(labels, vals, color=colors)
        ax1.set_ylim(0, 1.05)
        ax1.set_title(f"DST → {dst['decision']}")
        ax1.text(
            0.5,
            0.92,
            f"policy: {policy['action']}",
            transform=ax1.transAxes,
            ha="center",
            fontsize=9,
        )

    plt.show()


def analyze(path: Path, ask_human: bool = False, do_plot: bool = False) -> dict:
    x, meta = load_observation(path)
    fs = float(meta.get("fs", 8000.0))
    masses = run_detectors(x, fs)
    obs_id = str(meta.get("id", path.name))

    print(f"\nObservation: {obs_id}  n={len(x)}  fs={fs}")
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
        human = human_review_prompt(obs_id, report)
    elif report["policy"]["action"] == "HUMAN_REVIEW":
        print("\n(write a team verdict — re-run with --human)")

    if do_plot:
        plot_report(obs_id, DETECTOR_NAMES, masses, report)

    return {"meta": meta, "masses": masses, "report": report, "human": human}


def main() -> None:
    p = argparse.ArgumentParser(description="SETI/DST hack — analyze one observation")
    p.add_argument("observation", type=Path, help="path to .npy observation")
    p.add_argument("--human", action="store_true", help="enter team verdict")
    p.add_argument("--plot", action="store_true", help="show BPA / Bel charts after the report")
    args = p.parse_args()
    analyze(args.observation, ask_human=args.human, do_plot=args.plot)


if __name__ == "__main__":
    main()
