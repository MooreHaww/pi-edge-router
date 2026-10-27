"""Simulate tiered routing on coding tasks using saved benchmark CSVs.

Reads only the CSV files written by bench_coding.py. Makes no network or API calls.
"""
import csv
from pathlib import Path

RESULTS = Path("results")
TIER_FILES = {
    "pi": "coding_pi_coding_tasks_{}.csv",
    "pc": "coding_pc_coding_tasks_{}.csv",
    "high": "coding_cloud_high_coding_tasks_{}.csv",
    "minimal": "coding_cloud_minimal_coding_tasks_{}.csv",
}
CLOUD_TIERS = {"high": "cloud (high)", "minimal": "cloud (minimal)"}
TOKEN_CAP = 3000

STRATEGIES = [
    ("Always cloud (high)", ["high"]),
    ("Always cloud (minimal)", ["minimal"]),
    ("Pi only", ["pi"]),
    ("PC only", ["pc"]),
    ("Pi -> cloud (high)", ["pi", "high"]),
    ("PC -> cloud (high)", ["pc", "high"]),
    ("Pi -> PC -> cloud (high)", ["pi", "pc", "high"]),
    ("PC -> cloud (minimal)", ["pc", "minimal"]),
    ("Pi -> PC -> cloud (minimal)", ["pi", "pc", "minimal"]),
    ("PC -> cloud (minimal) -> cloud (high)", ["pc", "minimal", "high"]),
]

HELDOUT_NOTE = ("held-out has now been used for these comparisons, and with this few tasks per set "
                "(6 per dev set, 12 held-out) the differences are evidence, not proof.")


def load(tier, set_name):
    """Return {id: row} for one tier and one task set, or None if the file does not exist."""
    path = RESULTS / TIER_FILES[tier].format(set_name)
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def merge(*parts):
    """Combine several {id: row} dicts; None if any part is missing."""
    if any(p is None for p in parts):
        return None
    combined = {}
    for p in parts:
        combined.update(p)
    return combined


def passed(row):
    return row["passed"].strip() == "True"


def is_router(chain):
    return any(t not in CLOUD_TIERS for t in chain) and any(t in CLOUD_TIERS for t in chain)


def simulate(ids, chain, data):
    """Run each task through the tiers in order, stopping at the first pass.

    A task is solved if any tier that handled it passed. Cost is cloud cost_usd only.
    Seconds add up for every tier that actually ran on that task.
    """
    solved, cost, seconds = 0, 0.0, 0.0
    escalated = []
    for i in ids:
        reason = ""
        cloud_steps = []
        for tier in chain:
            row = data[tier][i]
            seconds += float(row["seconds"])
            ok = passed(row)
            if tier in CLOUD_TIERS:
                cost += float(row["cost_usd"])
                step = CLOUD_TIERS[tier] + (" passed" if ok else " failed")
                if int(row["out_tokens"] or 0) >= TOKEN_CAP:
                    step += ", hit the token cap"
                cloud_steps.append(step)
            elif not ok:
                reason = row["first_failure"] or row["error"] or "(no reason recorded)"
            if ok:
                solved += 1
                break
        if cloud_steps:
            escalated.append((i, reason, cloud_steps))
    return solved, cost, seconds, escalated


def saving(cost, baseline):
    if baseline is None:
        return "n/a"
    if baseline == 0:
        return ""
    return f"{(baseline - cost) / baseline * 100:.1f}%"


def report(title, data, notes):
    print(f"=== {title} ===")
    missing = [t for t, rows in data.items() if rows is None]
    if missing:
        print("Missing results for:", ", ".join(missing), "- rows that need them show n/a.")
    ids = sorted(data["pi"])
    total = len(ids)

    results = {}
    for name, chain in STRATEGIES:
        if any(data[t] is None or any(i not in data[t] for i in ids) for t in chain):
            results[name] = None
        else:
            results[name] = simulate(ids, chain, data)

    base_high = results["Always cloud (high)"]
    base_min = results["Always cloud (minimal)"]
    base_high = base_high[1] if base_high else None
    base_min = base_min[1] if base_min else None

    print(f"{'Strategy':<38}{'Solved':>8}{'Cost USD':>11}{'Seconds':>9}"
          f"{'Saving vs high':>16}{'Saving vs minimal':>19}")
    for name, chain in STRATEGIES:
        r = results[name]
        if r is None:
            print(f"{name:<38}{'n/a':>8}{'n/a':>11}{'n/a':>9}")
            continue
        solved, cost, seconds, _ = r
        vs_high = saving(cost, base_high) if is_router(chain) else ""
        vs_min = saving(cost, base_min) if is_router(chain) else ""
        print(f"{name:<38}{f'{solved}/{total}':>8}{cost:>11.6f}{seconds:>9.1f}{vs_high:>16}{vs_min:>19}")

    for name, chain in STRATEGIES:
        r = results[name]
        if r is None or not is_router(chain):
            continue
        escalated = r[3]
        print(f"{name}: {len(escalated)} of {total} reached the cloud")
        for i, reason, steps in escalated:
            print(f"  {i}: {reason}  -> {'; '.join(steps)}")

    for note in notes:
        print(f"Note: {note}")
    print()


def main():
    sets = {s: {t: load(t, s) for t in TIER_FILES} for s in ("dev", "dev2", "heldout")}
    combined = {t: merge(*(sets[s][t] for s in sets)) for t in TIER_FILES}

    report("Dev set", sets["dev"],
           ["dev simulation; these tasks were seen while building the router."])
    report("Dev2 set", sets["dev2"],
           ["dev simulation; these tasks were seen while building the router."])
    report("Held-out set", sets["heldout"],
           ["held-out tasks; this is the honest estimate.", HELDOUT_NOTE])
    report("All combined", combined,
           ["dev and held-out together; mixes seen and unseen tasks."])


if __name__ == "__main__":
    main()
