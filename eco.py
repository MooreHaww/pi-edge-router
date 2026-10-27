"""Eco mode command line.

  python eco.py discover                      list local OpenAI-compatible servers on localhost
  python eco.py solve <task_file> <task_id>   run one benchmark task up the ladder

The cloud tier is off unless ALLOW_CLOUD=1 is set in this window.
"""
import os
import sys

import bench_coding
import eco_core
import router

USAGE = "Usage: python eco.py discover | python eco.py solve <task_file> <task_id>"


def cmd_discover():
    found = eco_core.discover_local()
    if not found:
        print("No local servers answered on ports", ", ".join(str(p) for p in eco_core.LOCAL_PORTS))
        return
    for s in found:
        print(f"{s['kind']:<10} port {s['port']:<6} models: {', '.join(s['models']) or '(none reported)'}")


def cmd_solve(task_file, task_id):
    tasks = {t["id"]: t for t in bench_coding.load_tasks(task_file)}
    if task_id not in tasks:
        raise SystemExit(f"No task {task_id!r} in {task_file}. Ids: {', '.join(tasks)}")
    task = tasks[task_id]
    tiers = eco_core.default_tiers()
    print(f"Ladder: pi ({router.LOCAL_URL}) -> pc ({bench_coding.PC_URL}) -> cloud "
          f"({'on' if os.environ.get('ALLOW_CLOUD') == '1' else 'off, set ALLOW_CLOUD=1 to enable'})")
    result = eco_core.solve(task["prompt"], task["tests"], task["entry"], tiers, task_id=task_id)
    for a in result["attempts"]:
        status = "PASS" if a["passed"] else "FAIL"
        print(f"  {a['tier']:<6} {status}  {a['seconds']:.1f}s  {a['out_tokens']} out tokens  "
              f"${a['cost_usd']:.6f}" + (f"  {a['error']}" if a["error"] else ""))
    for name in result["skipped"]:
        print(f"  {name:<6} skipped (cloud is off)")
    print(f"Solved by: {result['solved_by'] or 'nobody'}")
    print(f"Cost: ${result['cost_usd']:.6f}  Time: {result['seconds']:.1f}s")
    print(f"Estimated cloud cost avoided (ESTIMATE): ${result['estimated_cloud_cost_avoided_usd']:.6f}")
    print("Logged to", eco_core.LOG_PATH)


def main():
    args = sys.argv[1:]
    if args == ["discover"]:
        cmd_discover()
    elif len(args) == 3 and args[0] == "solve":
        cmd_solve(args[1], args[2])
    else:
        raise SystemExit(USAGE)


if __name__ == "__main__":
    main()
