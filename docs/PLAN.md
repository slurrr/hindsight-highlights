# Hindsight Highlights: start-fresh service plan

## Goal
Stand up Hindsight as a **real local service** (not embedded), with **clear boundaries**, **same URLs**, and a **fresh/optimized v2 setup** (not a lift-and-shift of the current pg0 state).

Target endpoints:
- Postgres: `127.0.0.1:5432`
- Hindsight API: `127.0.0.1:8888`
- vLLM: `127.0.0.1:8002` (agentmux still owns model serving)

## Non-goals (for the start-fresh pass)
- No attempt to preserve existing Hindsight DB contents unless explicitly requested later.
- No pg0.
- No “agentmux starts postgres.” Hindsight service owns its DB dependency.
- Avoid scattering config across repos without an explicit contract.

---

## New structure (clean boundaries)

### Repo: `hindsight-highlights`
Purpose: an ops repo for running Hindsight locally.

Contains:
- `env/`: authoritative service env config
- `systemd/`: unit files
- `scripts/`: init/reset/healthcheck utilities
- `docs/`: durable docs/decisions

Runtime roots (durable + observable):
- DB data: `~/data/hindsight-pg/` (fresh)
- Logs/pids: `~/runs/hindsight/`
- Caches: under `~/cache/` (via env)

### Ownership contract
- **This repo owns**:
  - DB URL + schema
  - Hindsight server worker/concurrency/timeouts defaults
  - retrieval model choices (embeddings/reranker) unless deliberately delegated to clients
  - “safe defaults” for memory extraction (structured outputs, etc.)
- **Clients (pi-ghosty) own**:
  - bank semantics (what banks exist, what they mean)
  - when to call retain/recall/consolidate
  - per-call toggles (e.g. disable thinking for memory calls if desired)
  - tagging conventions

### Agentmux contract
- agentmux remains the cockpit for launching vLLM.
- agentmux should treat Hindsight as an **external dependency** (base URL), not a managed subservice.

---

## Service implementation plan (fresh)

### Phase A — Postgres as a real system service (fresh DB)
1) Use Fedora packages (not pg0).
2) Initialize a brand new cluster in `~/data/hindsight-pg/`.
3) Configure listen on `127.0.0.1:5432`.
4) Create:
   - role/user `hindsight` (password set)
   - database `hindsight`
5) Enable required extensions (at minimum `pgvector` if used).

Result: stable DB aligned with Fedora upgrades (ICU/glibc), no bundled-binary rot.

### Phase B — Hindsight API as its own server (systemd user service)
1) Dedicated uv venv for Hindsight **in this repo**.
2) Authoritative env file lives in-repo: `env/hindsight.env`.
3) Add systemd user unit `hindsight-api.service` to run the API on `127.0.0.1:8888`.
4) Logs go to `~/runs/hindsight/` (either journald-only or explicit file logs).

Result: `systemctl --user start hindsight-api` brings it up independently of agentmux.

### Phase C — Stop managing Hindsight from agentmux
1) Remove (or stop using) `engine="hindsight"` stacks for normal operation.
2) Keep agentmux stacks for vLLM only.
3) Provide a small healthcheck script in this repo to validate:
   - DB reachable
   - Hindsight `/health`
   - vLLM `/health` (optional)

---

## Better defaults baked into the fresh setup
Based on what we learned:

1) **Structured extraction stability first**
- Keep xgrammar structured outputs enabled for memory extraction workloads.
- Keep thinking for memory as a **client-controlled toggle**; default memory calls remain thinking-discouraged until proven safe under load.

2) **Avoid retry storms**
- Keep generous per-call timeouts for memory ops.
- Keep retain concurrency caps (e.g. 8) to prevent tail blowups.

3) **Tool payload blow-up protection (client-side)**
- Don’t rely on server-side truncation.
- Keep a client hygiene rule: don’t feed giant tool_result blobs into procedural retain.

4) **DB-truth auditing stays**
- Keep a script-based workflow to inspect actual stored units (not receipts), to verify no reasoning leakage is persisted.

---

## Cutover plan (low drama)
1) Stand up fresh Postgres + fresh Hindsight API at the same ports.
2) Point clients to the new Hindsight service URL (still `127.0.0.1:8888`).
3) Keep agentmux launching only vLLM.
4) Run a small end-to-end sanity pass:
   - recall works
   - retain writes a couple units
   - consolidation runs
   - audit shows no reasoning leakage

---

## Open decisions (intentionally minimal)
- Postgres: **system service** (chosen)
- Env config: **in repo** (chosen)

