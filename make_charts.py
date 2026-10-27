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
TEXT = "#222222"
GREY = "#bbbbbb"
SETS = ["dev", "dev2", "heldout"]

# One identity colour per tier, used in every chart. Shades were adjusted from the
# requested ones so each has at least 3:1 contrast on white and Pi/PC stay apart
# for deuteranopia. Colour never carries pass/fail on its own.
COLORS = {
    "pi": "#A3173F",       # raspberry red
    "pc": "#22A876",       # green
    "minimal": "#3A9AD9",  # light blue, cloud at minimal effort
    "high": "#0B3C8C",     # deep blue, cloud at high effort
    "router": "#C98500",   # amber, router rows
}

COST_STRATEGIES = [
    ("Always cloud\n(high)", ["high"], "high"),
    ("Always cloud\n(minimal)", ["minimal"], "minimal"),
    ("PC -> cloud\n(minimal)", ["pc", "minimal"], "router"),
    ("Pi -> PC ->\ncloud (minimal)", ["pi", "pc", "minimal"], "router"),
    ("Pi only", ["pi"], "pi"),
    ("PC only", ["pc"], "pc"),
]
CALLOUT = ("Always cloud\n(minimal)", "PC -> cloud\n(minimal)")
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
    n = len(ids)
    rows = []
    for label, chain, family in COST_STRATEGIES:
        solved, cost, seconds, _ = simulate(ids, chain, data)
        rows.append((label, solved, cost, seconds, family))

    print("cost_heldout.png (held-out set)")
    for label, solved, cost, seconds, _ in rows:
        print(f"  {label.replace(chr(10), ' '):<30} solved {solved}/{n}  cost ${cost:.6f}  seconds {seconds:.1f}")

    labels = [r[0] for r in rows]
    a, b = labels.index(CALLOUT[0]), labels.index(CALLOUT[1])
    base, router = rows[a], rows[b]
    pct = (base[2] - router[2]) / base[2] * 100
    if router[1] == base[1]:
        callout = f"{pct:.1f}% cheaper,\nsame {router[1]}/{n}"
        title = (f"Same {router[1]}/{n} as always-cloud minimal, {pct:.1f}% lower cloud cost: "
                 f"{n} held-out tasks")
    else:
        callout = f"{pct:.1f}% cheaper,\n{router[1]}/{n} vs {base[1]}/{n}"
        title = f"Cloud cost per strategy: {n} held-out tasks"
    print(f"  callout: {callout.replace(chr(10), ' ')}  "
          f"(({base[2]:.6f} - {router[2]:.6f}) / {base[2]:.6f})")
    print(f"  title: {title}")

    nonzero = [r[2] for r in rows if r[2] > 0]
    floor = min(nonzero) / 10
    top = max(nonzero) * 30

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = list(range(len(rows)))
    ax.bar(x, [r[2] for r in rows], color=[COLORS[r[4]] for r in rows],
           edgecolor=TEXT, linewidth=0.6)
    ax.set_yscale("log")
    ax.set_ylim(floor, top)
    for i, (_, solved, cost, _, family) in enumerate(rows):
        if cost > 0:
            ax.text(i, cost * 1.15, f"${cost:.6f}\n{solved}/{n} solved", ha="center", va="bottom", fontsize=9)
        else:
            # Outline in the tier colour, no bar: $0 cannot be drawn on a log scale.
            ax.text(i, floor * 1.3, f"$0 (local only)\n{solved}/{n} solved", ha="center", va="bottom",
                    fontsize=9, bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                          edgecolor=COLORS[family], linewidth=1.5))

    # Bracket over the two compared bars, above their labels.
    y = max(base[2], router[2]) * 6
    ax.plot([a, a, b, b], [y / 1.4, y, y, y / 1.4], color=TEXT, linewidth=1)
    ax.text((a + b) / 2, y * 1.15, callout, ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Cloud cost in USD (log scale)")
    ax.set_title(title)
    footnote(fig, f"{n} tasks, one run. Local tiers cost $0 in API fees and cannot be drawn on a log scale.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path = OUT / "cost_heldout.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def passfail_chart():
    by_set = {s: {t: load(t, s) for t in TIER_FILES} for s in SETS}
    columns = [(s, i) for s in SETS for i in sorted(by_set[s]["pi"])]

    print("passfail_24.png (all sets)")
    fig, ax = plt.subplots(figsize=(12, 4))
    failures = {}
    for r, (name, tier) in enumerate(GRID_ROWS):
        color = COLORS[tier]
        counts = {"passed": 0, "failed": 0, "missing": 0}
        failures[tier] = []
        y = len(GRID_ROWS) - 1 - r
        for c, (s, i) in enumerate(columns):
            rows = by_set[s][tier]
            if rows is None or i not in rows:
                counts["missing"] += 1
                ax.add_patch(Rectangle((c, y), 1, 1, facecolor="white", edgecolor=GREY))
            elif passed(rows[i]):
                counts["passed"] += 1
                ax.add_patch(Rectangle((c, y), 1, 1, facecolor=color, edgecolor="white"))
            else:
                counts["failed"] += 1
                failures[tier].append(i)
                ax.add_patch(Rectangle((c + 0.04, y + 0.04), 0.92, 0.92, facecolor="white",
                                       edgecolor=color, hatch="xx", linewidth=1.2))
        print(f"  {name:<14} passed {counts['passed']:>2}  failed {counts['failed']:>2}  no result {counts['missing']:>2}")
        if failures[tier]:
            print(f"  {'':<14} failed: {', '.join(failures[tier])}")

    beat_pc = failures["pc"]
    short = ", ".join(i.split("_")[0] for i in beat_pc)
    if len(beat_pc) == 1:
        headline = f"Only one task ({short}) beat the PC"
    else:
        headline = f"Only {len(beat_pc)} of {len(columns)} tasks ({short}) beat the PC"
    tally = ", ".join(f"{name} {len(failures[tier])}" for name, tier in GRID_ROWS)
    title = f"{headline}\nFailures out of {len(columns)} tasks: {tally}"
    print(f"  title: {title.replace(chr(10), ' | ')}")

    ax.set_xlim(0, len(columns))
    ax.set_ylim(0, len(GRID_ROWS))
    ax.set_xticks([c + 0.5 for c in range(len(columns))])
    ax.set_xticklabels([i for _, i in columns], rotation=60, ha="right", fontsize=8)
    ax.set_yticks([len(GRID_ROWS) - 1 - r + 0.5 for r in range(len(GRID_ROWS))])
    ax.set_yticklabels([name for name, _ in GRID_ROWS], fontsize=11, fontweight="bold")
    for tick, (_, tier) in zip(ax.get_yticklabels(), GRID_ROWS):
        tick.set_color(COLORS[tier])
    ax.tick_params(length=0)
    for s_index in range(1, len(SETS)):
        boundary = sum(len(by_set[s]["pi"]) for s in SETS[:s_index])
        ax.axvline(boundary, color=TEXT, linewidth=2)
    ax.set_title(title, pad=18)
    ax.text(0, len(GRID_ROWS) + 0.08, "dev", fontsize=9, va="bottom")
    for s_index in range(1, len(SETS)):
        boundary = sum(len(by_set[s]["pi"]) for s in SETS[:s_index])
        ax.text(boundary + 0.1, len(GRID_ROWS) + 0.08, ["dev2", "held-out"][s_index - 1], fontsize=9, va="bottom")
    fig.legend(handles=[Patch(facecolor="#555555", label="Passed (filled in the tier colour)"),
                        Patch(facecolor="white", edgecolor="#555555", hatch="xx", label="Failed (X hatch)"),
                        Patch(facecolor="white", edgecolor=GREY, label="No result (blank)")],
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
        ("Pi", "pi", er.read_bench(er.PI_BENCH_FILE),
         er.energy_above_idle(er.read_pi_log(er.PI_LOAD_FILE), er.PI_IDLE_W, er.PI_SAMPLE_S)),
        ("PC", "pc", er.read_bench(er.PC_BENCH_FILE),
         er.energy_above_idle(load_watts, pc_idle, er.PC_SAMPLE_S)),
    ]
    names, colors, wh_per_solved, seconds = [], [], [], []
    print("energy_vs_time.png (held-out energy runs)")
    for name, tier, bench, joules in devices:
        solved = sum(er.passed(r) for r in bench)
        bench_s = sum(float(r["seconds"]) for r in bench)
        names.append(name)
        colors.append(COLORS[tier])
        wh_per_solved.append(joules / 3600 / solved)
        seconds.append(bench_s)
        print(f"  {name}  solved {solved}/{len(bench)}  energy {joules:.1f} J  "
              f"Wh per solved {joules / 3600 / solved:.5f}  benchmark seconds {bench_s:.1f}")
    n_tasks = len(devices[0][2])

    pi_wh, pc_wh = wh_per_solved
    pi_s, pc_s = seconds
    if pi_wh < pc_wh:
        energy_part = f"Pi: {pc_wh / pi_wh:.1f}x less energy per solved task."
    else:
        energy_part = f"PC: {pi_wh / pc_wh:.1f}x less energy per solved task."
    if pc_s < pi_s:
        time_part = f"PC: {pi_s / pc_s:.1f}x faster."
    else:
        time_part = f"Pi: {pc_s / pi_s:.1f}x faster."
    headline = f"{energy_part} {time_part}"
    print(f"  headline: {headline}  (energy ratio {max(pi_wh, pc_wh):.5f} / {min(pi_wh, pc_wh):.5f}, "
          f"time ratio {max(pi_s, pc_s):.1f} / {min(pi_s, pc_s):.1f})")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4.6))
    ax1.bar(names, wh_per_solved, color=colors, edgecolor=TEXT, linewidth=0.6)
    for i, v in enumerate(wh_per_solved):
        ax1.text(i, v, f"{v:.5f}", ha="center", va="bottom", fontsize=9)
    ax1.set_ylabel("Wh above idle per solved task")
    ax1.set_title("Energy per solved task")
    ax2.bar(names, seconds, color=colors, edgecolor=TEXT, linewidth=0.6)
    for i, v in enumerate(seconds):
        ax2.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    ax2.set_ylabel("Benchmark seconds (sum)")
    ax2.set_title("Time")
    for ax in (ax1, ax2):
        ax.margins(y=0.15)
    fig.suptitle(headline, fontsize=12, fontweight="bold", y=0.975)
    fig.text(0.5, 0.915, f"Energy and time, {n_tasks} held-out tasks\nPC = GPU only, Pi = board rails, above idle",
             ha="center", va="top", fontsize=10)
    footnote(fig, f"{n_tasks} tasks, one run.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
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
