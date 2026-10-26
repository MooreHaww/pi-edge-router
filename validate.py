import csv
import json

from eval_local import is_correct
from router import ask_local, decide


def main():
    with open("data/validation.json", encoding="utf-8") as f:
        questions = json.load(f)

    rows = []
    for q in questions:
        local = ask_local(q["question"])
        route, reason = decide(q["question"], local)
        correct = is_correct(local["answer"], q["answer"])
        rows.append({
            "id": q["id"],
            "kind": q["kind"],
            "expected": q["answer"],
            "answer": local["answer"],
            "correct": correct,
            "route": route,
            "reason": reason,
            "avg_logprob": round(local["avg_logprob"], 4),
            "seconds": round(local["seconds"], 2),
        })
        mark = "OK " if correct else "BAD"
        print(
            f'{q["id"]:>2} {mark} {route:<5} avg={local["avg_logprob"]:.3f} '
            f'| {local["answer"][:60]}'
        )

    fields = list(rows[0].keys())
    with open("results/validation_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    kept = [r for r in rows if r["route"] == "local"]
    sent = [r for r in rows if r["route"] == "cloud"]
    print()
    print(f"Local model correct overall: {sum(r['correct'] for r in rows)}/{len(rows)}")
    print(f"Kept local: {len(kept)} ({sum(r['correct'] for r in kept)} correct)")
    print(f"Escalated: {len(sent)} ({sum(not r['correct'] for r in sent)} were wrong)")
    missed = [r["id"] for r in kept if not r["correct"]]
    print(f"WRONG answers kept local (missed): {len(missed)} {missed}")
    print("Saved results/validation_results.csv")


if __name__ == "__main__":
    main()
