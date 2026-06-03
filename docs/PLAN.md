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
- `env/`: authoritative service env config (server runtime behavior)
- `config/`: human-readable, versioned *backend configuration surface*
  - `config/banks/`: bank definitions (JSON)
  - `config/templates/`: known-good bank templates (JSON)
  - `config/examples/`: example payloads / smoke inputs
- `scripts/`: thin operational commands (launch wrapper, apply config, healthcheck, reset)
- `systemd/`: user unit files and install notes
- `docs/`: durable docs/decisions

Runtime roots (durable + observable):
- DB data: Fedora `postgresql.service` package default (`/var/lib/pgsql/data`)
- Logs: journald for `postgresql.service` and `hindsight-api.service` (user unit)
- Caches: under `~/cache/` (via env)

### Ownership contract (explicit, avoids split-brain)
- **This repo owns** (authoritative, reviewable):
  - DB URL + schema + extensions (pgvector)
  - Hindsight server runtime config (timeouts/concurrency/retrieval models)
  - *Bank definitions as code* (`config/banks/*.json`) so you can see/reason about them in one place
- **Clients (pi-ghosty) own at runtime**:
  - which banks they use / when they call retain/recall/consolidate
  - any dynamic per-request overrides (e.g. disable thinking for memory calls)

Contract detail:
- DB is the runtime source of truth. This repo is an editable snapshot/export. Client scripts SHOULD run a highlights pull after any config update to keep the snapshot current.

### Agentmux contract
- agentmux remains the cockpit for launching vLLM.
- agentmux should treat Hindsight as an **external dependency** (base URL), not a managed subservice.

---

## Service implementation plan (fresh)

### Phase A — Postgres as a real system service (fresh DB)
1) Use Fedora packages (not pg0).
2) Initialize a brand new Fedora PostgreSQL cluster.
3) Configure listen on `127.0.0.1:5432`.
4) Create:
   - role/user `hindsight` (password set)
   - database `hindsight`
5) Enable required extensions (at minimum `pgvector` if used).

Result: stable DB aligned with Fedora upgrades (ICU/glibc), no bundled-binary rot.

### Phase B — Hindsight API as its own server (manual user service)
1) Dedicated uv venv for Hindsight **in this repo**.
2) Authoritative service env lives in-repo: `env/hindsight.env`.
3) Launch profile defaults live in `env/hindsight.launch.env`.
4) Add a `systemd --user` unit `hindsight-api.service` for manual start/stop/restart only.
5) Expose a `hindsight` command wrapper for `up/down/status/logs/doctor`.
6) Logs go to journald under the user service.
7) Bank desired-state is stored in `config/banks/` and applied with a repo script (idempotent).

Result: `hindsight up` brings it up independently of agentmux, without boot enablement.

### Phase C — Stop managing Hindsight from agentmux
1) Remove (or stop using) `engine="hindsight"` stacks for normal operation.
2) Keep agentmux stacks for vLLM only.
3) Validate externally with standard tools:
   - `systemctl status postgresql`
   - `systemctl status hindsight-api`
   - `curl http://127.0.0.1:8888/health`
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
3) Keep agentmux (or the launch wrapper) handling only vLLM.
4) Run a small end-to-end sanity pass:
   - recall works
   - retain writes a couple units
   - consolidation runs
   - audit shows no reasoning leakage

---

## Open decisions (intentionally minimal)
- Postgres: **system service** (chosen)
- Hindsight API: **manual user service** (chosen)
- Env config: **in repo** (chosen)

