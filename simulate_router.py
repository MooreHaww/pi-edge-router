"""Simulate Pi-first routing on coding tasks using saved benchmark CSVs.

Reads only the CSV files written by bench_coding.py. Makes no network or API calls.
"""
import csv
from pathlib import Path

RESULTS = Path("results")
DEV_PI = ["coding_pi_coding_tasks_dev.csv", "coding_pi_coding_tasks_dev2.csv"]
DEV_CLOUD = ["coding_cloud_high_coding_tasks_dev.csv", "coding_cloud_high_coding_tasks_dev2.csv"]
HELDOUT_PI = ["coding_pi_coding_tasks_heldout.csv"]
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
    return row["passed"].strip() == "True"


def report(title, pi, cloud, note):
    print(f"=== {title} ===")
    ids = sorted(pi)
    missing = [i for i in ids if i not in cloud]
    if missing:
        print("Warning: no cloud result for", ", ".join(missing), "- counted as not solved by cloud.")

    def cloud_solved(i):
        return i in cloud and passed(cloud[i])

    def cloud_cost(i):
        return float(cloud[i]["cost_usd"]) if i in cloud else 0.0

    def cloud_seconds(i):
        return float(cloud[i]["seconds"]) if i in cloud else 0.0

    total = len(ids)
    pi_seconds = sum(float(pi[i]["seconds"]) for i in ids)
    escalated = [i for i in ids if not passed(pi[i])]

    strategies = [
        ("Always cloud",
         sum(cloud_solved(i) for i in ids),
         sum(cloud_cost(i) for i in ids),
         sum(cloud_seconds(i) for i in ids)),
        ("Pi only",
         sum(passed(pi[i]) for i in ids),
         0.0,
         pi_seconds),
        ("Router",
         sum(passed(pi[i]) for i in ids) + sum(cloud_solved(i) for i in escalated),
         sum(cloud_cost(i) for i in escalated),
         pi_seconds + sum(cloud_seconds(i) for i in escalated)),
    ]

    print(f"{'Strategy':<14}{'Solved':>10}{'Cost USD':>12}{'Seconds':>10}")
    for name, solved, cost, seconds in strategies:
        print(f"{name:<14}{f'{solved}/{total}':>10}{cost:>12.6f}{seconds:>10.1f}")

    cloud_total = strategies[0][2]
    router_total = strategies[2][2]
    if cloud_total > 0:
        saving = (cloud_total - router_total) / cloud_total * 100
        print(f"Router cost saving vs always-cloud: {saving:.1f}%")

    print(f"Escalated to cloud ({len(escalated)} of {total}):")
    for i in escalated:
        reason = pi[i]["first_failure"] or pi[i]["error"] or "(no reason recorded)"
        outcome = "cloud passed" if cloud_solved(i) else "cloud failed"
        if i in cloud and int(cloud[i]["out_tokens"] or 0) >= TOKEN_CAP:
            outcome += ", hit the token cap"
        print(f"  {i}: {reason}  -> {outcome}")

    print(f"Note: {note}\n")


def main():
    dev_pi, dev_cloud = load(DEV_PI), load(DEV_CLOUD)
    held_pi, held_cloud = load(HELDOUT_PI), load(HELDOUT_CLOUD)

    report("Dev sets", dev_pi, dev_cloud,
           "dev simulation; these tasks were seen while building the router.")
    report("Held-out set", held_pi, held_cloud,
           "held-out tasks; this is the honest estimate.")
    report("All combined", {**dev_pi, **held_pi}, {**dev_cloud, **held_cloud},
           "dev and held-out together; mixes seen and unseen tasks.")


if __name__ == "__main__":
    main()
