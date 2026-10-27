"""Energy per solved task for the PC and the Pi, from saved power logs and benchmark CSVs.

Reads only files in results/. Makes no network or API calls.
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path

RESULTS = Path("results")
PC_IDLE_FILE = RESULTS / "power_pc_idle.csv"
PC_LOAD_FILE = RESULTS / "power_pc_load.csv"
PI_LOAD_FILE = RESULTS / "power_pi_load.txt"
PC_BENCH_FILE = RESULTS / "coding_pc_energy_heldout.csv"
PI_BENCH_FILE = RESULTS / "coding_pi_energy_heldout.csv"
CLOUD_MINIMAL_FILE = RESULTS / "coding_cloud_minimal_coding_tasks_heldout.csv"

# Nominal sample intervals of the loggers (assumption: real spacing can drift slightly).
PC_SAMPLE_S = 0.5
PI_SAMPLE_S = 1.0
# Pi idle power: mean of six manual vcgencmd readings with the Pi idle.
PI_IDLE_W = 1.88


def read_pc_log(path):
    """nvidia-smi CSV without header: time, watts, util. Returns (times, watts)."""
    times, watts = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue
            times.append(datetime.strptime(row[0].strip(), "%Y/%m/%d %H:%M:%S.%f"))
            watts.append(float(row[1]))
    return times, watts


def read_pi_log(path):
    with open(path, encoding="utf-8") as f:
        return [float(line) for line in f if line.strip()]


def read_bench(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def passed(row):
    return row["passed"].strip() == "True"


def energy_above_idle(watts, idle, interval):
    return sum(max(0.0, w - idle) * interval for w in watts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--price", type=float, default=0.15, help="electricity price in USD per kWh")
    args = parser.parse_args()

    idle_times, idle_watts = read_pc_log(PC_IDLE_FILE)
    load_times, load_watts = read_pc_log(PC_LOAD_FILE)
    pi_watts = read_pi_log(PI_LOAD_FILE)
    pc_bench = read_bench(PC_BENCH_FILE)
    pi_bench = read_bench(PI_BENCH_FILE)
    cloud_rows = read_bench(CLOUD_MINIMAL_FILE)

    pc_idle = sum(idle_watts) / len(idle_watts)
    measured_dt = (load_times[-1] - load_times[0]).total_seconds() / (len(load_times) - 1)

    devices = [
        ("PC", pc_bench, energy_above_idle(load_watts, pc_idle, PC_SAMPLE_S), pc_idle,
         len(load_watts) * PC_SAMPLE_S),
        ("Pi", pi_bench, energy_above_idle(pi_watts, PI_IDLE_W, PI_SAMPLE_S), PI_IDLE_W,
         len(pi_watts) * PI_SAMPLE_S),
    ]
    cloud_cost = sum(float(r["cost_usd"]) for r in cloud_rows)

    print("Energy report, held-out coding tasks")
    print("  PC = GPU only (nvidia-smi), above idle")
    print("  Pi = board power rails (vcgencmd), above idle")
    print("  12 tasks, one run")
    print()
    print(f"PC idle: {pc_idle:.2f} W (mean of {len(idle_watts)} samples in {PC_IDLE_FILE.name})")
    print(f"Pi idle: {PI_IDLE_W:.2f} W (constant, mean of six manual readings)")
    print(f"Assumption: sample intervals are nominal, PC {PC_SAMPLE_S} s and Pi {PI_SAMPLE_S} s. "
          f"PC timestamps average {measured_dt:.3f} s apart.")
    print()

    print(f"{'Device':<8}{'Solved':>8}{'Bench s':>9}{'Log s':>8}{'Joules':>10}{'Wh':>10}"
          f"{'Wh/solved':>11}{'Elec USD':>12}")
    summary = {}
    for name, bench, joules, _, log_s in devices:
        solved = sum(passed(r) for r in bench)
        bench_s = sum(float(r["seconds"]) for r in bench)
        wh = joules / 3600
        per_solved = f"{wh / solved:.5f}" if solved else "n/a"
        elec = wh / 1000 * args.price
        summary[name] = {"joules": joules, "bench_s": bench_s}
        print(f"{name:<8}{f'{solved}/{len(bench)}':>8}{bench_s:>9.1f}{log_s:>8.1f}{joules:>10.1f}"
              f"{wh:>10.5f}{per_solved:>11}{elec:>12.8f}")
    print(f"Cloud (minimal effort), same 12 tasks: ${cloud_cost:.6f} "
          f"(from {CLOUD_MINIMAL_FILE.name}, cost_usd)")
    print(f"Electricity price used: ${args.price:.2f} per kWh")
    print("Note: each power log covers the whole logging window, which is longer than the "
          "benchmark seconds; energy above idle outside the tasks is included.")
    print()

    # ESTIMATE: Pi first, PC only for the tasks the Pi failed. The PC log has no per-task
    # boundaries, so PC energy is split across tasks in proportion to each task's seconds.
    pc_by_id = {r["id"]: r for r in pc_bench}
    pi_failed = [r["id"] for r in pi_bench if not passed(r)]
    pc_joules, pc_total_s = summary["PC"]["joules"], summary["PC"]["bench_s"]
    pc_failed_s = sum(float(pc_by_id[i]["seconds"]) for i in pi_failed)
    chain_joules = summary["Pi"]["joules"] + pc_joules * pc_failed_s / pc_total_s
    chain_s = summary["Pi"]["bench_s"] + pc_failed_s
    chain_solved = sum(passed(r) for r in pi_bench) + sum(passed(pc_by_id[i]) for i in pi_failed)
    chain_wh = chain_joules / 3600

    print("ESTIMATE: Pi -> PC chain (PC runs only the tasks the Pi failed)")
    print(f"  Tasks sent to the PC: {', '.join(pi_failed)}")
    print(f"  PC energy for those tasks: split by seconds, {pc_failed_s:.1f} of {pc_total_s:.1f} PC seconds")
    print(f"  Solved: {chain_solved}/{len(pi_bench)}")
    print(f"  Energy: {chain_joules:.1f} J = {chain_wh:.5f} Wh"
          + (f" ({chain_wh / chain_solved:.5f} Wh per solved task)" if chain_solved else ""))
    print(f"  Time: {chain_s:.1f} s (Pi total {summary['Pi']['bench_s']:.1f} s + PC {pc_failed_s:.1f} s)")
    print(f"  Electricity: ${chain_wh / 1000 * args.price:.8f}")
    print()
    print("Cloud energy is not published, so no energy comparison with the cloud is made.")


if __name__ == "__main__":
    main()
