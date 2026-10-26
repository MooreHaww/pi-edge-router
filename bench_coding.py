import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import requests

import router  # reuse LOCAL_URL and the cloud settings

BLOCKED = ["import os", "from os", "import sys", "from sys", "subprocess", "shutil",
           "socket", "open(", "eval(", "exec(", "__import__", "pathlib",
           "requests", "urllib"]

HARNESS = """
import json, sys
src = open("answer.py", encoding="utf-8").read()
spec = json.load(open("spec.json", encoding="utf-8"))
ns = {}
try:
    exec(compile(src, "answer", "exec"), ns)
    fn = ns[spec["entry"]]
except Exception as e:
    print(json.dumps({"error": "load: " + repr(e)}))
    sys.exit(0)
passed = 0
fails = []
for args, expected in spec["tests"]:
    try:
        got = fn(*args)
        if got == expected:
            passed += 1
        else:
            fails.append([args, expected, got])
    except Exception as e:
        fails.append([args, expected, "EXC " + repr(e)])
print(json.dumps({"passed": passed, "total": len(spec["tests"]), "fails": fails}, default=repr))
"""

FIELDS = ["id", "passed", "tests_passed", "tests_total", "seconds", "in_tokens",
          "out_tokens", "cost_usd", "error", "first_failure", "code"]


def load_tasks(path):
    spec = importlib.util.spec_from_file_location("tasks_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TASKS


def ask_pi(prompt):
    body = {"messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500, "temperature": 0}
    start = time.time()
    r = requests.post(router.LOCAL_URL, json=body, timeout=600).json()
    return {"text": r["choices"][0]["message"]["content"],
            "seconds": time.time() - start,
            "in_tokens": r["usage"]["prompt_tokens"],
            "out_tokens": r["usage"]["completion_tokens"],
            "cost": 0.0}


def ask_cloud(prompt):
    key = os.environ.get("MODEL_API_KEY")
    if not key or os.environ.get("ALLOW_CLOUD") != "1":
        raise SystemExit("Cloud is off. Set MODEL_API_KEY and ALLOW_CLOUD=1 in this window first.")
    body = {"model": router.CLOUD_MODEL, "input": prompt, "max_output_tokens": 3000,
            "reasoning": {"effort": router.CLOUD_EFFORT}}
    start = time.time()
    r = requests.post(router.CLOUD_URL, json=body,
                      headers={"Authorization": "Bearer " + key}, timeout=600)
    seconds = time.time() - start
    r.raise_for_status()
    data = r.json()
    text = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    text += part.get("text", "")
    usage = data.get("usage", {})
    tin, tout = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    return {"text": text, "seconds": seconds, "in_tokens": tin, "out_tokens": tout,
            "cost": tin * 1.25 / 1e6 + tout * 4.25 / 1e6}


def extract_code(text):
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def run_tests(code, task):
    for bad in BLOCKED:
        if bad in code:
            return {"error": "blocked: " + bad}
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "answer.py"), "w", encoding="utf-8") as f:
            f.write(code)
        with open(os.path.join(tmp, "spec.json"), "w", encoding="utf-8") as f:
            json.dump({"entry": task["entry"], "tests": task["tests"]}, f)
        with open(os.path.join(tmp, "harness.py"), "w", encoding="utf-8") as f:
            f.write(HARNESS)
        try:
            p = subprocess.run([sys.executable, "-I", "harness.py"], cwd=tmp,
                               capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        lines = p.stdout.strip().splitlines()
        if not lines:
            return {"error": "no output: " + p.stderr.strip()[-200:]}
        try:
            return json.loads(lines[-1])
        except ValueError:
            return {"error": "bad output"}


def main():
    backend = sys.argv[1] if len(sys.argv) > 1 else "pi"
    path = sys.argv[2] if len(sys.argv) > 2 else "data/coding_tasks_dev.py"
    if backend not in ("pi", "cloud"):
        raise SystemExit('Usage: python bench_coding.py [pi|cloud] [tasks_file]')
    ask = ask_pi if backend == "pi" else ask_cloud
    tasks = load_tasks(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    out_path = f"results/coding_{backend}_{stem}.csv"
    rows = []
    for task in tasks:
        print(f"{task['id']} ...", end=" ", flush=True)
        res = ask(task["prompt"])
        code = extract_code(res["text"])
        t = run_tests(code, task)
        error = t.get("error", "")
        tp, tt = t.get("passed", 0), t.get("total", len(task["tests"]))
        ok = (not error) and tp == tt
        first = ""
        if t.get("fails"):
            args, exp, got = t["fails"][0]
            first = f"input={args} expected={exp} got={got}"
        rows.append({"id": task["id"], "passed": ok, "tests_passed": tp, "tests_total": tt,
                     "seconds": round(res["seconds"], 1), "in_tokens": res["in_tokens"],
                     "out_tokens": res["out_tokens"], "cost_usd": round(res["cost"], 6),
                     "error": error, "first_failure": first, "code": code})
        print(("PASS" if ok else "FAIL") + f" ({tp}/{tt} tests, {res['seconds']:.0f}s, "
              f"{res['out_tokens']} out tokens)" + (f" {error}" if error else ""), flush=True)
        if first:
            print("    first failure:", first)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    solved = sum(r["passed"] for r in rows)
    total_cost = sum(r["cost_usd"] for r in rows)
    print(f"\n{backend}: {solved}/{len(rows)} tasks passed all tests, cost ${total_cost:.4f}")
    print("saved", out_path)


if __name__ == "__main__":
    main()