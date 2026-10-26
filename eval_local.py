import csv
import json
import re
import time

import requests

URL = "http://192.168.1.14:8080/v1/chat/completions"
SUFFIX = " Answer with just the answer, no explanation."


def is_correct(answer, expected):
    a = answer.lower().replace(",", "")
    e = expected.lower()
    return re.search(r"(?<![\w.])" + re.escape(e) + r"(?!\w)", a) is not None


def ask(question):
    body = {
        "messages": [{"role": "user", "content": question + SUFFIX}],
        "max_tokens": 64,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": 1,
    }
    start = time.time()
    r = requests.post(URL, json=body, timeout=300).json()
    seconds = time.time() - start
    choice = r["choices"][0]
    lps = [t["logprob"] for t in choice["logprobs"]["content"]]
    return {
        "answer": choice["message"]["content"].strip(),
        "avg_logprob": sum(lps) / len(lps),
        "min_logprob": min(lps),
        "seconds": seconds,
        "tokens_per_s": r["timings"]["predicted_per_second"],
    }


def main():
    with open("data/questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    rows = []
    for q in questions:
        res = ask(q["question"])
        res["id"] = q["id"]
        res["kind"] = q["kind"]
        res["expected"] = q["answer"]
        res["correct"] = is_correct(res["answer"], q["answer"])
        rows.append(res)
        mark = "OK " if res["correct"] else "BAD"
        print(
            f'{q["id"]:>2} {mark} avg={res["avg_logprob"]:.3f} '
            f'min={res["min_logprob"]:.3f} {res["seconds"]:.1f}s '
            f'| {res["answer"][:60]}'
        )

    fields = ["id", "kind", "expected", "answer", "correct",
              "avg_logprob", "min_logprob", "seconds", "tokens_per_s"]
    with open("results/local_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    good = sum(r["correct"] for r in rows)
    print(f"\n{good}/{len(rows)} correct. Saved results/local_results.csv")


if __name__ == "__main__":
    main()