"""
Baselines + team policy. Canon fusion is team-mean A vs B (see main.py).

majority / mean score / Dempster, then:
  high K or high m(Θ) → HUMAN_REVIEW (teams write the verdict)
  weak / tied belief → OBSERVE_MORE
  else → DECIDE(signal|noise)
"""

from __future__ import annotations

from dst import TotalConflict, belief, combine_many, mean_bpa, plausibility, validate_bpa

TAU_CONFLICT = 0.25
TAU_UNKNOWN = 0.40
TAU_BELIEF = 0.55


def _argmax_bel(m: dict) -> str:
    bel = belief(m)
    if bel["signal"] > bel["noise"]:
        return "signal"
    if bel["noise"] > bel["signal"]:
        return "noise"
    return "abstain"


def hard_label(m: dict) -> str:
    return _argmax_bel(validate_bpa(m))


def majority_vote(masses: list[dict]) -> dict:
    counts = {"signal": 0, "noise": 0, "abstain": 0}
    for m in masses:
        counts[hard_label(m)] += 1
    if counts["signal"] == counts["noise"]:
        winner = "abstain"
    else:
        winner = "signal" if counts["signal"] > counts["noise"] else "noise"
    return {"method": "majority", "votes": counts, "decision": winner}


def mean_score(masses: list[dict]) -> dict:
    m = mean_bpa(masses)
    return {
        "method": "mean_score",
        "mass": m,
        "belief": belief(m),
        "plausibility": plausibility(m),
        "decision": _argmax_bel(m),
    }


def dst_fusion(masses: list[dict]) -> dict:
    try:
        fused, ks = combine_many(masses)
    except TotalConflict as e:
        return {
            "method": "dst",
            "mass": None,
            "belief": None,
            "plausibility": None,
            "pairwise_conflict": [],
            "max_conflict": e.k,
            "decision": "abstain",
            "refused": True,
        }
    return {
        "method": "dst",
        "mass": fused,
        "belief": belief(fused),
        "plausibility": plausibility(fused),
        "pairwise_conflict": ks,
        "max_conflict": max(ks) if ks else 0.0,
        "decision": _argmax_bel(fused),
        "refused": False,
    }


def hitl_policy(fused: dict, max_conflict: float = 0.0) -> dict:
    if fused.get("refused") or max_conflict >= TAU_CONFLICT:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"conflict K={max_conflict:.3f} ≥ {TAU_CONFLICT}",
            "label": None,
        }
    m = validate_bpa(fused["mass"] if "mass" in fused else fused)
    bel = belief(m)
    if m["unknown"] >= TAU_UNKNOWN:
        return {
            "action": "HUMAN_REVIEW",
            "reason": f"m(Θ)={m['unknown']:.3f} ≥ {TAU_UNKNOWN}",
            "label": None,
        }
    winner = _argmax_bel(m)
    if winner == "abstain":
        return {"action": "OBSERVE_MORE", "reason": "Bel(signal) = Bel(noise)", "label": None}
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
    dst = dst_fusion(masses)
    return {
        "majority": majority_vote(masses),
        "mean": mean_score(masses),
        "dst": dst,
        "policy": hitl_policy(dst, max_conflict=dst["max_conflict"]),
    }


def human_review_prompt(obs_id: str, report: dict) -> str | None:
    print("\n=== TEAM REVIEW ===")
    print(f"observation: {obs_id}")
    print(f"policy:      {report['policy']}")
    print(f"DST mass:    {report['dst']['mass']}")
    print(f"majority:    {report['majority']['decision']}")
    print(f"mean:        {report['mean']['decision']}")
    try:
        ans = input("Team verdict [signal/noise/abstain/skip]: ").strip().lower()
    except EOFError:
        return None
    return ans if ans in {"signal", "noise", "abstain"} else None
