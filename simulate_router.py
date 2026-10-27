"""Simulate tiered routing on coding tasks using saved benchmark CSVs.

Reads only the CSV files written by bench_coding.py. Makes no network or API calls.
"""
import csv
from pathlib import Path

RESULTS = Path("results")
DEV_PI = ["coding_pi_coding_tasks_dev.csv", "coding_pi_coding_tasks_dev2.csv"]
DEV_PC = ["coding_pc_coding_tasks_dev.csv", "coding_pc_coding_tasks_dev2.csv"]
DEV_CLOUD = ["coding_cloud_high_coding_tasks_dev.csv", "coding_cloud_high_coding_tasks_dev2.csv"]
HELDOUT_PI = ["coding_pi_coding_tasks_heldout.csv"]
HELDOUT_PC = ["coding_pc_coding_tasks_heldout.csv"]
HELDOUT_CLOUD = ["coding_cloud_high_coding_tasks_heldout.csv"]
TOKEN_CAP = 3000


def load(files):
    rows = {}
    for name in files:
        with open(RESULTS / name, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[row["id"]] = row
    return rows


def passed(row):
    return row is not None and row["passed"].strip() == "True"


def simulate(ids, local_tiers, cloud, use_cloud):
    """Run each task through the local tiers in order, then the cloud if all of them failed.

    A task is solved if any tier that handled it passed. Cost is cloud cost_usd only.
    Seconds add up for every tier that actually ran on that task.
    """
    solved, cost, seconds = 0, 0.0, 0.0
    escalated = []
    for i in ids:
        done = False
        reason = ""
        for tier in local_tiers:
            row = tier.get(i)
            if row is None:
                reason = "(no local result)"
                continue
            seconds += float(row["seconds"])
            if passed(row):
                done = True
                break
            reason = row["first_failure"] or row["error"] or "(no reason recorded)"
        if not done and use_cloud:
            row = cloud.get(i)
            if row is not None:
                seconds += float(row["seconds"])
                cost += float(row["cost_usd"])
            done = passed(row)
            escalated.append((i, reason, row))
        solved += done
    return solved, cost, seconds, escalated


def report(title, pi, pc, cloud, note):
    print(f"=== {title} ===")
    ids = sorted(pi)
    for name, tier in (("PC", pc), ("cloud", cloud)):
        missing = [i for i in ids if i not in tier]
        if missing:
            print(f"Warning: no {name} result for", ", ".join(missing), "- counted as not solved there.")

    rows = [
        ("Always cloud", [], True),
        ("Pi only", [pi], False),
        ("PC only", [pc], False),
        ("Pi -> cloud", [pi], True),
        ("PC -> cloud", [pc], True),
        ("Pi -> PC -> cloud", [pi, pc], True),
    ]
    results = [(name, *simulate(ids, tiers, cloud, use_cloud)) for name, tiers, use_cloud in rows]
    total = len(ids)
    cloud_total = results[0][2]

    print(f"{'Strategy':<20}{'Solved':>8}{'Cost USD':>12}{'Seconds':>10}{'Saving':>9}")
    for (name, solved, cost, seconds, _), (_, tiers, _) in zip(results, rows):
        is_router = bool(tiers) and name.endswith("cloud")
        saving = f"{(cloud_total - cost) / cloud_total * 100:.1f}%" if is_router and cloud_total > 0 else ""
        print(f"{name:<20}{f'{solved}/{total}':>8}{cost:>12.6f}{seconds:>10.1f}{saving:>9}")

    for name, _, _, _, escalated in results[3:]:
        print(f"{name}: {len(escalated)} of {total} reached the cloud")
        for i, reason, row in escalated:
            if row is None:
                outcome = "no cloud result"
            else:
                outcome = "cloud passed" if passed(row) else "cloud failed"
                if int(row["out_tokens"] or 0) >= TOKEN_CAP:
                    outcome += ", hit the token cap"
            print(f"  {i}: {reason}  -> {outcome}")

    print(f"Note: {note}\n")


def main():
    dev = load(DEV_PI), load(DEV_PC), load(DEV_CLOUD)
    held = load(HELDOUT_PI), load(HELDOUT_PC), load(HELDOUT_CLOUD)

    report("Dev sets", *dev,
           "dev simulation; these tasks were seen while building the router.")
    report("Held-out set", *held,
           "held-out tasks; this is the honest estimate.")
    report("All combined", *({**d, **h} for d, h in zip(dev, held)),
           "dev and held-out together; mixes seen and unseen tasks.")


if __name__ == "__main__":
    main()
