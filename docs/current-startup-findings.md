# Current startup findings

## Current situation
- `hindsight-api` is now intended to be started manually as a `systemd --user` service (not enabled at boot).
- Service logs now go to journald (`journalctl --user -u hindsight-api`); the old `/home/poop/runs/hindsight/api.log` is a legacy unbounded file log.
- The service can start even when the LLM backend is not ready.

## What startup did
From the service journal, Hindsight startup followed this order:
1. MCP/session startup
2. metrics initialization
3. embeddings provider init
4. reranker provider init
5. LLM connectivity verification
6. DB migrations
7. request polling / worker loop

## Relevant log findings
- Embeddings loaded with the local SentenceTransformer model:
  - `BAAI/bge-small-en-v1.5`
  - log line: `Embeddings: local provider initialized (dim: 384)`
- Reranker loaded with the local CrossEncoder model:
  - `cross-encoder/ms-marco-MiniLM-L-6-v2`
  - log line: `Reranker: local provider initialized (max_concurrent=4)`
- The LLM backend verification initially failed during startup:
  - `APIConnectionError ... attempt 1/2/3`
  - then: `Connection verification failed for openai/gemma-4-e4b-memory`
  - then: `Server will start but LLM-dependent operations may fail until the provider is available.`
- Startup still completed after that failure.

## What that means
- Hindsight does not have a separate “load models” command; model loading happens as part of service startup.
- The local retrieval models are initialized inside the Hindsight process.
- The main memory LLM is a separate backend (`vLLM` on `127.0.0.1:8002`), and Hindsight can come up before that backend is ready.
- So “service started” only means systemd will try to run it; it does **not** guarantee the whole memory stack is ready.

## Practical takeaway
The startup behavior is currently:
- Hindsight API starts
- local embeddings/reranker initialize
- LLM connectivity may fail if vLLM is not already up
- service continues running anyway

This is the main startup boundary to remember when debugging boot behavior.
