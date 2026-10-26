import csv
import os
import sys
import time

import requests

LOCAL_URL = "http://192.168.1.14:8080/v1/chat/completions"
THRESHOLD = -0.2
MAX_QUESTION_CHARS = 500
# The threshold was calibrated with this suffix, so the router keeps it for now.
SUFFIX = " Answer with just the answer, no explanation."
REFUSALS = [
    "unable to verify",
    "cannot verify",
    "can't verify",
    "couldn't find",
    "could not find",
    "i don't know",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i cannot",
    "i can't",
    "i am unable",
    "i'm unable",
    "no information",
]
LOG_PATH = "results/router_log.csv"
LOG_FIELDS = ["timestamp", "route", "reason", "avg_logprob", "seconds", "question"]


def ask_local(question):
    body = {
        "messages": [{"role": "user", "content": question + SUFFIX}],
        "max_tokens": 128,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": 1,
    }
    start = time.time()
    r = requests.post(LOCAL_URL, json=body, timeout=300).json()
    seconds = time.time() - start
    choice = r["choices"][0]
    lps = [t["logprob"] for t in choice["logprobs"]["content"]]
    return {
        "answer": choice["message"]["content"].strip(),
        "avg_logprob": sum(lps) / len(lps) if lps else 0.0,
        "seconds": seconds,
    }


def ask_cloud(question):
    # Placeholder: the cloud model is not connected yet.
    return None


def decide(question, local):
    if len(question) > MAX_QUESTION_CHARS:
        return "cloud", "question too long"
    answer = local["answer"].lower()
    if not answer:
        return "cloud", "empty answer"
    for phrase in REFUSALS:
        if phrase in answer:
            return "cloud", "refusal phrase"
    if local["avg_logprob"] < THRESHOLD:
        return "cloud", "low confidence"
    return "local", "confident"


def log(row):
    new_file = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def route(question):
    start = time.time()
    local = ask_local(question)
    route_taken, reason = decide(question, local)
    answer = local["answer"]
    note = ""
    if route_taken == "cloud":
        cloud = ask_cloud(question)
        if cloud is None:
            note = "cloud not connected yet, showing local answer"
        else:
            answer = cloud
    seconds = time.time() - start
    log({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "route": route_taken,
        "reason": reason,
        "avg_logprob": round(local["avg_logprob"], 4),
        "seconds": round(seconds, 2),
        "question": question,
    })
    return {
        "route": route_taken,
        "reason": reason,
        "avg_logprob": local["avg_logprob"],
        "seconds": seconds,
        "answer": answer,
        "note": note,
    }


def main():
    if len(sys.argv) < 2:
        print('Usage: python router.py "your question"')
        return
    question = " ".join(sys.argv[1:])
    res = route(question)
    print(f'ROUTE:   {res["route"]} ({res["reason"]})')
    print(f'SCORE:   {res["avg_logprob"]:.3f}')
    print(f'TIME:    {res["seconds"]:.1f}s')
    if res["note"]:
        print(f'NOTE:    {res["note"]}')
    print(f'ANSWER:  {res["answer"]}')


if __name__ == "__main__":
    main()