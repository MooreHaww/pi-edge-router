# pi-edge-router

An edge-first AI assistant on a Raspberry Pi 5. A small quantized Llama model answers locally, and only the requests it is unsure about are escalated to a cloud model.

Built for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026). Work in progress.

## Why this exists

Cloud models are fast and capable but cost money and need a connection for every request. Small models running on cheap hardware cost nothing per request, but they are slower and get harder questions wrong. This project tests a middle path: answer locally when the small model is confident, and pay for the cloud only when it is not.

## What it does (planned)

- Runs Llama 3.2 3B (4-bit) on the Pi through llama.cpp's server
- A router sends each question to the local model first
- A confidence check decides whether to keep the local answer or escalate to the cloud model
- Every request is logged with the model used, latency and confidence, so the trade-off can be measured

## Measured so far

Llama 3.2 3B Instruct, Q4_K_M, Raspberry Pi 5 (8 GB), 4 threads, CPU only, context 4096.

| Test | Prompt (tokens/s) | Generation (tokens/s) |
|---|---|---|
| llama-bench | 26.46 | 5.04 |
| Real chat (llama-cli) | 25.6 | 5.5 |

## How it works

See [docs/design.md](docs/design.md) for the router design (v1).

## Setup (Pi, so far)

```
sudo apt update && sudo apt install -y git build-essential cmake libcurl4-openssl-dev
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release -j4
```

Download the model and run it with a small context. Without `-c 4096` the program was killed for running out of memory on the 8 GB Pi.

```
./build/bin/llama-cli -m ~/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 4096
```

## What I wanted to learn

- What quantization actually buys on cheap hardware
- How to decide, with a measured signal, when a small model should hand a question to a bigger one

## Status

- [x] Pi 5 set up, llama.cpp built, 3B model running
- [x] First speed measurements
- [x] Design v1
- [ ] Local model server and router
- [ ] Confidence check and threshold
- [ ] Cloud model connection
- [ ] Test questions and results table
- [ ] Demo

## License

MIT