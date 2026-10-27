"""Simulate Pi-first routing on coding tasks using saved benchmark CSVs.

Reads only the CSV files written by bench_coding.py. Makes no network or API calls.
"""
import csv
from pathlib import Path

RESULTS = Path("results")
PI_FILES = ["coding_pi_coding_tasks_dev.csv", "coding_pi_coding_tasks_dev2.csv"]
CLOUD_FILES = ["coding_cloud_high_coding_tasks_dev.csv", "coding_cloud_high_coding_tasks_dev2.csv"]


def load(files):
    rows = {}
    for name in files:
        with open(RESULTS / name, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[row["id"]] = row
    return rows


def passed(row):
    return row["passed"].strip() == "True"


def main():
    pi = load(PI_FILES)
    cloud = load(CLOUD_FILES)
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

    print(f"\nEscalated to cloud ({len(escalated)} of {total}):")
    for i in escalated:
        reason = pi[i]["first_failure"] or pi[i]["error"] or "(no reason recorded)"
        outcome = "cloud passed" if cloud_solved(i) else "cloud failed"
        print(f"  {i}: {reason}  -> {outcome}")

    cloud_total = strategies[0][2]
    router_total = strategies[2][2]
    if cloud_total > 0:
        saving = (cloud_total - router_total) / cloud_total * 100
        print(f"\nRouter cost saving vs always-cloud: {saving:.1f}%")

    print("Note: this is a simulation on the dev sets only, using saved results, not a held-out test.")


if __name__ == "__main__":
    main()
