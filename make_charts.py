"""Draw the README charts from the saved result files.

Reads only files in results/ (through simulate_router.py and energy_report.py) and writes
PNGs to docs/img/. Makes no network or API calls. Every number comes from the CSVs.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

import energy_report as er
from simulate_router import TIER_FILES, load, passed, simulate

OUT = Path("docs/img")
BAR = "#3b5b8c"
TEXT = "#222222"
SETS = ["dev", "dev2", "heldout"]

COST_STRATEGIES = [
    ("Always cloud\n(high)", ["high"]),
    ("Always cloud\n(minimal)", ["minimal"]),
    ("PC -> cloud\n(minimal)", ["pc", "minimal"]),
    ("Pi -> PC ->\ncloud (minimal)", ["pi", "pc", "minimal"]),
    ("Pi only", ["pi"]),
    ("PC only", ["pc"]),
]
GRID_ROWS = [("Pi", "pi"), ("PC", "pc"), ("Cloud minimal", "minimal"), ("Cloud high", "high")]

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "text.color": TEXT, "axes.labelcolor": TEXT, "axes.edgecolor": TEXT,
    "xtick.color": TEXT, "ytick.color": TEXT, "font.size": 10,
})


def footnote(fig, text):
    fig.text(0.01, 0.01, text, fontsize=8, ha="left", va="bottom")


def cost_chart():
    data = {t: load(t, "heldout") for t in TIER_FILES}
    ids = sorted(data["pi"])
    rows = []
    for label, chain in COST_STRATEGIES:
        solved, cost, seconds, _ = simulate(ids, chain, data)
        rows.append((label, solved, cost, seconds))

    print("cost_heldout.png (held-out set)")
    for label, solved, cost, seconds in rows:
        print(f"  {label.replace(chr(10), ' '):<30} solved {solved}/{len(ids)}  cost ${cost:.6f}  seconds {seconds:.1f}")

    nonzero = [c for _, _, c, _ in rows if c > 0]
    floor = min(nonzero) / 10
    top = max(nonzero) * 10

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(rows))
    ax.bar(x, [c if c > 0 else 0 for _, _, c, _ in rows], color=BAR, bottom=0)
    ax.set_yscale("log")
    ax.set_ylim(floor, top)
    for i, (_, solved, cost, _) in enumerate(rows):
        label = f"${cost:.6f}\n{solved}/{len(ids)} solved" if cost > 0 else f"$0 (local only)\n{solved}/{len(ids)} solved"
        y = cost * 1.15 if cost > 0 else floor * 1.15
        ax.text(i, y, label, ha="center", va="bottom", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([r[0] for r in rows])
    ax.set_ylabel("Cloud cost in USD (log scale)")
    ax.set_title(f"Cost per strategy, {len(ids)} held-out tasks")
    footnote(fig, f"{len(ids)} tasks, one run. Local tiers cost $0 in API fees and cannot be drawn on a log scale.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path = OUT / "cost_heldout.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def passfail_chart():
    by_set = {s: {t: load(t, s) for t in TIER_FILES} for s in SETS}
    columns = [(s, i) for s in SETS for i in sorted(by_set[s]["pi"])]

    print("passfail_24.png (all sets)")
    fig, ax = plt.subplots(figsize=(12, 3.8))
    for r, (name, tier) in enumerate(GRID_ROWS):
        counts = {"passed": 0, "failed": 0, "missing": 0}
        for c, (s, i) in enumerate(columns):
            rows = by_set[s][tier]
            y = len(GRID_ROWS) - 1 - r
            if rows is None or i not in rows:
                counts["missing"] += 1
                ax.add_patch(Rectangle((c, y), 1, 1, facecolor="white", edgecolor="#bbbbbb"))
            elif passed(rows[i]):
                counts["passed"] += 1
                ax.add_patch(Rectangle((c, y), 1, 1, facecolor=BAR, edgecolor="white"))
            else:
                counts["failed"] += 1
                ax.add_patch(Rectangle((c, y), 1, 1, facecolor="white", edgecolor=TEXT, hatch="xx"))
        print(f"  {name:<14} passed {counts['passed']:>2}  failed {counts['failed']:>2}  no result {counts['missing']:>2}")
        failed = [i for s, i in columns if by_set[s][tier] is not None and i in by_set[s][tier]
                  and not passed(by_set[s][tier][i])]
        if failed:
            print(f"  {'':<14} failed: {', '.join(failed)}")

    ax.set_xlim(0, len(columns))
    ax.set_ylim(0, len(GRID_ROWS))
    ax.set_xticks([c + 0.5 for c in range(len(columns))])
    ax.set_xticklabels([i for _, i in columns], rotation=60, ha="right", fontsize=8)
    ax.set_yticks([len(GRID_ROWS) - 1 - r + 0.5 for r in range(len(GRID_ROWS))])
    ax.set_yticklabels([name for name, _ in GRID_ROWS])
    ax.tick_params(length=0)
    for s_index in range(1, len(SETS)):
        boundary = sum(len(by_set[s]["pi"]) for s in SETS[:s_index])
        ax.axvline(boundary, color=TEXT, linewidth=1.5)
    ax.set_title(f"Tests passed per tier, {len(columns)} tasks (dev | dev2 | held-out)")
    fig.legend(handles=[Patch(facecolor=BAR, label="Passed"),
                        Patch(facecolor="white", edgecolor=TEXT, hatch="xx", label="Failed"),
                        Patch(facecolor="white", edgecolor="#bbbbbb", label="No result")],
               loc="lower center", bbox_to_anchor=(0.5, 0.05), ncol=3, frameon=False)
    footnote(fig, f"{len(columns)} tasks, one run. Blank cells have no saved result; they are not failures.")
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    path = OUT / "passfail_24.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def energy_chart():
    _, idle_watts = er.read_pc_log(er.PC_IDLE_FILE)
    _, load_watts = er.read_pc_log(er.PC_LOAD_FILE)
    pc_idle = sum(idle_watts) / len(idle_watts)
    devices = [
        ("Pi", er.read_bench(er.PI_BENCH_FILE),
         er.energy_above_idle(er.read_pi_log(er.PI_LOAD_FILE), er.PI_IDLE_W, er.PI_SAMPLE_S)),
        ("PC", er.read_bench(er.PC_BENCH_FILE),
         er.energy_above_idle(load_watts, pc_idle, er.PC_SAMPLE_S)),
    ]
    names, wh_per_solved, seconds = [], [], []
    print("energy_vs_time.png (held-out energy runs)")
    for name, bench, joules in devices:
        solved = sum(er.passed(r) for r in bench)
        bench_s = sum(float(r["seconds"]) for r in bench)
        names.append(name)
        wh_per_solved.append(joules / 3600 / solved)
        seconds.append(bench_s)
        print(f"  {name}  solved {solved}/{len(bench)}  energy {joules:.1f} J  "
              f"Wh per solved {joules / 3600 / solved:.5f}  benchmark seconds {bench_s:.1f}")
    n_tasks = len(devices[0][1])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
    ax1.bar(names, wh_per_solved, color=BAR)
    for i, v in enumerate(wh_per_solved):
        ax1.text(i, v, f"{v:.5f}", ha="center", va="bottom", fontsize=9)
    ax1.set_ylabel("Wh above idle per solved task")
    ax1.set_title("Energy per solved task")
    ax2.bar(names, seconds, color=BAR)
    for i, v in enumerate(seconds):
        ax2.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    ax2.set_ylabel("Benchmark seconds (sum)")
    ax2.set_title("Time")
    for ax in (ax1, ax2):
        ax.margins(y=0.15)
    fig.suptitle(f"Energy and time, {n_tasks} held-out tasks\nPC = GPU only, Pi = board rails, above idle")
    footnote(fig, f"{n_tasks} tasks, one run.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path = OUT / "energy_vs_time.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [passfail_chart(), cost_chart(), energy_chart()]
    print("Wrote:")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
