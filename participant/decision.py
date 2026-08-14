"""
Decision baselines and a tiny Human-in-the-Loop policy.

Baselines (for comparison on the same observation):
  - majority voting on hard labels from BPAs
  - mean / averaged score
  - DST fusion (Dempster)

Policy after fusion:
  high conflict or high ignorance → HUMAN_REVIEW
  weak belief → OBSERVE_MORE / ABSTAIN
  otherwise → DECIDE(signal|noise)
"""

from __future__ import annotations

from dst import belief, combine_many, mean_bpa, plausibility, validate_bpa


# Tunable thresholds — change them; defend your choice.
TAU_CONFLICT = 0.25
TAU_UNKNOWN = 0.40
TAU_BELIEF = 0.55


def hard_label(m: dict) -> str:
    """Map one BPA to a hard class using belief; ties → abstain."""
    m = validate_bpa(m)
    bel = belief(m)
    if bel["signal"] > bel["noise"]:
        return "signal"
    if bel["noise"] > bel["signal"]:
        return "noise"
    return "abstain"


def majority_vote(masses: list[dict]) -> dict:
    """Count hard labels; returns a simple report dict."""
    labels = [hard_label(m) for m in masses]
    counts = {"signal": 0, "noise": 0, "abstain": 0}
    for lab in labels:
        counts[lab] += 1
    decisive = {k: counts[k] for k in ("signal", "noise")}
    if decisive["signal"] == decisive["noise"]:
        winner = "abstain"
    else:
        winner = max(decisive, key=decisive.get)
    return {"method": "majority", "votes": counts, "decision": winner}


def mean_score(masses: list[dict]) -> dict:
    """Average BPAs, then pick argmax belief."""
    m = mean_bpa(masses)
    bel = belief(m)
    if bel["signal"] > bel["noise"]:
        decision = "signal"
    elif bel["noise"] > bel["signal"]:
        decision = "noise"
    else:
        decision = "abstain"
    return {
        "method": "mean_score",
        "mass": m,
        "belief": bel,
        "plausibility": plausibility(m),
        "decision": decision,
    }


def dst_fusion(masses: list[dict]) -> dict:
    """Dempster combination of all BPAs."""
    fused, ks = combine_many(masses)
    bel = belief(fused)
    if bel["signal"] > bel["noise"]:
        decision = "signal"
    elif bel["noise"] > bel["signal"]:
        decision = "noise"
    else:
        decision = "abstain"
    return {
        "method": "dst",
        "mass": fused,
        "belief": bel,
        "plausibility": plausibility(fused),
        "pairwise_conflict": ks,
        "max_conflict": max(ks) if ks else 0.0,
        "decision": decision,
    }


def hitl_policy(fused: dict, max_conflict: float = 0.0) -> dict:
    """
    Simple post-fusion policy.

    Returns action in {DECIDE, HUMAN_REVIEW, OBSERVE_MORE} and optional label.
    """
    m = validate_bpa(fused["mass"] if "mass" in fused else fused)
    bel = belief(m)

    if max_conflict >= TAU_CONFLICT:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"conflict K={max_conflict:.3f} ≥ {TAU_CONFLICT}",
            "label": None,
        }
    if m["unknown"] >= TAU_UNKNOWN:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"m(Θ)={m['unknown']:.3f} ≥ {TAU_UNKNOWN}",
            "label": None,
        }

    winner = "signal" if bel["signal"] >= bel["noise"] else "noise"
    if bel[winner] >= TAU_BELIEF:
        return {
            "action": "DECIDE",
            "reason": f"Bel({winner})={bel[winner]:.3f} ≥ {TAU_BELIEF}",
            "label": winner,
        }

    return {
        "action": "OBSERVE_MORE",
        "reason": f"Bel({winner})={bel[winner]:.3f} < {TAU_BELIEF}",
        "label": None,
    }


def compare_baselines(masses: list[dict]) -> dict:
    """Run majority, mean, and DST on the same list of BPAs."""
    maj = majority_vote(masses)
    mean = mean_score(masses)
    dst = dst_fusion(masses)
    policy = hitl_policy(dst, max_conflict=dst["max_conflict"])
    return {"majority": maj, "mean": mean, "dst": dst, "policy": policy}


def human_review_prompt(obs_id: str, report: dict) -> str | None:
    """
    Minimal HITL interface: print context, ask for a decision.
    Returns 'signal', 'noise', 'abstain', or None if skipped / non-interactive.
    """
    print("\n=== HUMAN REVIEW ===")
    print(f"observation: {obs_id}")
    print(f"policy:      {report['policy']}")
    print(f"DST mass:    {report['dst']['mass']}")
    print(f"majority:    {report['majority']['decision']}")
    print(f"mean:        {report['mean']['decision']}")
    try:
        ans = input("Your decision [signal/noise/abstain/skip]: ").strip().lower()
    except EOFError:
        return None
    if ans in {"signal", "noise", "abstain"}:
        return ans
    return None
