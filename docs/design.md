# pi-edge-router: design v1

An edge-first assistant on a Raspberry Pi 5. A quantized open-weights model answers locally, and only requests it is unsure about are escalated to a cloud model.

## Parts
- **Local model server (Pi):** llama.cpp server running Llama 3.2 3B Instruct, Q4_K_M, exposed over HTTP.
- **Router (Python):** receives a question, asks the local model first, decides whether to trust the answer, otherwise forwards the question to the cloud model.
- **Log:** every request records which model answered, latency and the confidence score. The results table comes from here.

## Confidence check (v1, deliberately simple)
1. Average token confidence of the local answer. Below a threshold means escalate.
2. Hard rules that escalate regardless of score: the model says it doesn't know, the answer is empty or very short, the question is very long.
3. The threshold is picked from data: about 30 test questions run through both models, choosing the cut-off that keeps easy questions local and sends hard ones up.

## Results table (to fill in)
- Local speed
- Share of requests kept on the Pi
- Local vs cloud response time
- Answer quality

## Measured so far
- Llama 3.2 3B Q4_K_M, 4 threads, CPU only, context 4096
- Benchmark: 26.46 tokens/s prompt, 5.04 tokens/s generation
- Real chat: 25.6 tokens/s prompt, 5.5 tokens/s generation

## Stretch goal
Camera and segmentation feature, only if time allows.