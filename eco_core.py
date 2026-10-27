"""Eco mode core: run a coding task up a ladder of models and stop at the first that passes its tests.

Cloud tiers are skipped unless ALLOW_CLOUD=1. Every solve appends one JSON line to the cost log.
"""
import csv
import glob
import json
import os
import statistics
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import bench_coding

LOG_PATH = "results/eco_log.jsonl"
CLOUD_MINIMAL_GLOB = "results/coding_cloud_minimal_*.csv"
CLOUD_IN_PER_M = 1.25   # USD per million input tokens, same price as bench_coding.ask_cloud
CLOUD_OUT_PER_M = 4.25  # USD per million output tokens
LOCAL_PORTS = {11434: "Ollama", 8080: "llama.cpp", 8081: "llama.cpp", 1234: "LM Studio"}


@dataclass
class Tier:
    name: str
    kind: str  # "local" or "cloud"
    # Takes a prompt. Returns the model's text, or a dict like bench_coding's ask_* helpers
    # (text, in_tokens, out_tokens, cost) when token counts are known.
    ask: Callable
    cost_per_call: float = 0.0


def default_tiers():
    """Pi at router.LOCAL_URL, PC at bench_coding.PC_URL, then cloud (off unless ALLOW_CLOUD=1)."""
    return [
        Tier("pi", "local", bench_coding.ask_pi),
        Tier("pc", "local", bench_coding.ask_pc),
        Tier("cloud", "cloud", bench_coding.ask_cloud),
    ]


def solve(prompt, tests, entry, tiers, task_id=None, log_path=LOG_PATH):
    """Try each tier in order and stop at the first answer that passes all tests."""
    task = {"entry": entry, "tests": tests}
    attempts, skipped = [], []
    solved_by = None
    for tier in tiers:
        if tier.kind == "cloud" and os.environ.get("ALLOW_CLOUD") != "1":
            skipped.append(tier.name)
            continue
        start = time.time()
        attempt = {"tier": tier.name, "passed": False, "seconds": 0.0, "in_tokens": 0,
                   "out_tokens": 0, "cost_usd": 0.0, "error": ""}
        try:
            reply = tier.ask(prompt)
        except Exception as e:  # an unreachable or broken tier counts as a failed attempt
            attempt["seconds"] = round(time.time() - start, 2)
            attempt["error"] = "ask: " + repr(e)
            attempts.append(attempt)
            continue
        if isinstance(reply, dict):
            text = reply["text"]
            attempt["in_tokens"] = reply.get("in_tokens", 0)
            attempt["out_tokens"] = reply.get("out_tokens", 0)
            attempt["cost_usd"] = reply.get("cost", tier.cost_per_call)
        else:
            text = reply
            attempt["cost_usd"] = tier.cost_per_call
        result = bench_coding.run_tests(bench_coding.extract_code(text), task)
        attempt["seconds"] = round(time.time() - start, 2)
        attempt["error"] = result.get("error", "")
        attempt["passed"] = not attempt["error"] and result.get("passed", 0) == result.get("total", len(tests))
        attempts.append(attempt)
        if attempt["passed"]:
            solved_by = tier.name
            break

    solved_tier = next((t for t in tiers if t.name == solved_by), None)
    avoided = estimate_cloud_cost(prompt) if solved_tier is not None and solved_tier.kind == "local" else 0.0
    out = {
        "task_id": task_id,
        "solved_by": solved_by,
        "attempts": attempts,
        "skipped": skipped,
        "cost_usd": round(sum(a["cost_usd"] for a in attempts), 6),
        "seconds": round(sum(a["seconds"] for a in attempts), 2),
        "estimated_cloud_cost_avoided_usd": round(avoided, 6),
    }
    write_log(out, log_path)
    return out


def write_log(result, log_path=LOG_PATH):
    line = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **result}
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def median_cloud_minimal_out_tokens(pattern=CLOUD_MINIMAL_GLOB):
    values = []
    for path in sorted(glob.glob(pattern)):
        with open(path, newline="", encoding="utf-8") as f:
            values += [int(r["out_tokens"]) for r in csv.DictReader(f) if r.get("out_tokens")]
    return statistics.median(values) if values else None


def estimate_cloud_cost(prompt, pattern=CLOUD_MINIMAL_GLOB):
    """ESTIMATE of what always-cloud (minimal) would have cost for this prompt.

    Input tokens are approximated as characters / 4; output tokens are the median
    out_tokens of the saved minimal-effort cloud results. Not a measured cost.
    """
    median_out = median_cloud_minimal_out_tokens(pattern)
    if median_out is None:
        return 0.0
    return len(prompt) / 4 * CLOUD_IN_PER_M / 1e6 + median_out * CLOUD_OUT_PER_M / 1e6


def discover_local(ports=LOCAL_PORTS, host="localhost", timeout=1.0):
    """Ask each usual local port for its OpenAI-compatible /v1/models list. No benchmarking."""
    found = []
    for port, kind in ports.items():
        url = f"http://{host}:{port}/v1/models"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception:
            continue
        models = [m.get("id", "?") for m in data.get("data", [])] if isinstance(data, dict) else []
        found.append({"port": port, "kind": kind, "url": f"http://{host}:{port}/v1/chat/completions",
                      "models": models})
    return found
