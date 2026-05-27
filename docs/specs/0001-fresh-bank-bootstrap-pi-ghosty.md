# Spec: Fresh bank bootstrap for pi-ghosty (start-fresh-ish)

Goal: create a new set of banks on the new Postgres-backed Hindsight service, using only what we learned (better missions/config), without copying embedded-era drift.

## Assumptions
- Hindsight API running at `http://127.0.0.1:8888`
- vLLM running at `http://127.0.0.1:8002/v1`
- DB is truth; `hindsight-highlights` is the editable snapshot.

## Bank set (pi-ghosty)
Start with the two canonical banks:
- `pi-ghosty-personal`
- `pi-ghosty-procedural`

(Keep names stable so existing pi-ghosty runtime wiring continues to work.)

## Desired workflow
1) **Reset / fresh banks** (one-time for this bootstrap)
   - Ensure banks exist and are empty (or create new banks if Hindsight requires explicit creation).
2) **Apply new bank config from files**
   - Edit `hindsight-highlights/config/banks/pi-ghosty-personal.json`
   - Edit `hindsight-highlights/config/banks/pi-ghosty-procedural.json`
   - Run `push_banks.py` (self-normalizes via pull).
3) **Point pi-ghosty at these banks**
   - Confirm `pi-agent.json` / bank ids match the above.
4) **Smoke test (light)**
   - Small chat + 1 retain + 1 recall.
   - Confirm memory log shows sane timings.
   - Confirm highlights snapshot updated after any ghosty-side config update.
5) **Audit**
   - Verify stored units are reasonable (no reasoning leakage; no fact spam).

## What "good" looks like
- Retain extracts a small number of facts for casual banter.
- Consolidation avg per memory is in the sane band (no 100s tails).
- Streaming reasoning is clean in vLLM (already patched).

## Files to create/edit
- `config/banks/pi-ghosty-personal.json`
- `config/banks/pi-ghosty-procedural.json`

Suggested approach: start by cloning the style of `config/banks/coding-assistant.json` but tailor missions to each bank role.
