# CLAUDE.md

## Project
pi-edge-router is an edge-first assistant. A quantized Llama 3.2 3B (Q4_K_M) runs locally on a
Raspberry Pi 5 through llama.cpp's server. A router (router.py) escalates to a cloud model
(Meta Model API, Muse Spark) when the local answer is not trustworthy.
Built for the Meta Global AI Developer Hackathon.

## Environment
- Windows, PowerShell. Python virtualenv in .venv; activate with `.venv\Scripts\Activate.ps1`.
- The Pi address is set by LOCAL_URL in router.py and can change after a reboot.
- Start llama-server on the Pi with a small context. Without `-c 4096` it gets killed for running out of memory:
  `./build/bin/llama-server -m ~/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 4096 --host 0.0.0.0 --port 8080`

## Files
- router.py: routing decision. In order, these escalate to the cloud: question too long
  (MAX_QUESTION_CHARS = 500), letter/spelling question, empty answer, refusal phrase,
  then average logprob below THRESHOLD = -0.2.
- eval_local.py: runs data/questions.json through the local model.
- validate.py: runs a question file through the router's decision rule.
- data/: question sets. results/: CSV outputs.

## Honesty rules for measurements
- THRESHOLD was chosen from data/questions.json.
- data/validation.json and data/validation2.json are held-out sets that have already been used.
  Never tune THRESHOLD or the rules against them.
- Any new rule or threshold change must be tested on a new, unseen question set.
- Never edit existing data/*.json or results/*.csv files to make numbers look better.
- Never make a live call to the cloud API without asking me first; the free credits are limited.

## Git rules
- Commit only when asked. Never push.
- Never add Co-authored-by lines or any Claude attribution to commits.
- Never move, delete or recreate the git tag `pre-hackathon`, and never rewrite history.
  Everything up to that tag is pre-event work; everything after it is hackathon work.
- Do not commit results/router_log.csv, .env files, or *.gguf model files.

## Secrets
- The cloud API key lives only in the MODEL_API_KEY environment variable.
- Never put keys in code, files, commits or chat. Never read or print the contents of any .env file.
- Cloud endpoint: https://api.meta.ai/v1, model ID `muse-spark-1.3`.
- Cloud calls cost money: count them in the log and keep max output small.

## Working style
- The user is new to this stack. Before running commands, explain what you are about to do in one or two sentences.
- Make small changes, one at a time, and show the diff.
