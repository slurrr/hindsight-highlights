# Hindsight config control surface

Editable, versioned snapshot of Hindsight bank configuration.

This directory is intended to be an **editable export** of what `pi-ghosty/scripts/memory-status.mjs` shows at runtime.
The database remains the source of truth; these files are a human-friendly view that can be pushed back into the running service.

## Layout

- `banks/`: per-bank JSON snapshots (pulled from the live API)
- `templates/`: bank templates / mental models (optional)
- `examples/`: example payloads for smoke testing (optional)

## Workflow

- Pull from the live service (DB → files):
  - `uv run python scripts/pull_banks.py --banks <bank...>`
- Push edits to the live service (files → DB):
  - `uv run python scripts/push_banks.py --banks <bank...> --pull-after`

To reduce human error, client-side scripts that update bank config should run a pull immediately after applying changes.
## Quick start

```bash
make setup
make doctor
make run

# in another shell, once the API is healthy:
make dry-run-template
make import-template
make run-scenario
```

Keep long-lived/service defaults in `env/hindsight.env`; keep bank-level experiments here.

## Local multi-agent framework bank topology

Proposed fresh-start banks for a one-user local agent framework:

- `local-agent-user-profile`: durable personalization, goals, preferences, commitments, routines, and feedback. Main user-facing agent reads this before user interaction; other agents generally should not write here except via curated summaries.
- `local-agent-product-strategy`: ideas, high-level product plans, requirements, decisions, assumptions, risks, and implementation specs. Main/planner agents write and read this during ideation and spec creation.
- `local-agent-implementation-work`: delegated research/build/review/test work, module context, API contracts, blockers, handoffs, test results, and review findings. Peer agents write/read this while executing specs in parallel.
- `local-agent-assistant-ops`: scheduled non-user-facing assistant task memory, standing triage rules, summary outputs, follow-ups, and notable external signals. Scheduled agents write here; the main user-facing agent reads curated summaries and follow-ups.
- `local-agent-framework-procedural`: reusable operating rules for the framework itself: role boundaries, delegation protocols, memory routing, tool hygiene, review/test checklists, privacy/safety, and output contracts.

Recommended recall strategy:

- Use `recall` as the default in agent prompts; reserve `reflect` for explicit memory-grounded synthesis or structured profile/procedure answers.
- Recall from one bank at a time and orchestrate multi-bank recall client-side. For user-facing turns, query `local-agent-user-profile` + `local-agent-product-strategy` + `local-agent-framework-procedural`; add `local-agent-assistant-ops` only when discussing scheduled-assistant outputs; add `local-agent-implementation-work` when a spec is being executed or reviewed.
- Use `tags_match="any_strict"` or `all_strict` when filtering by entity-label tags such as `procedure_type:rule`, `work_phase:test`, `attention_level:needs_user`, or `planning_artifact:implementation_spec` so unrelated memory shapes do not enter ranking.
- Default to `budget="mid"`; use `budget="low"` for frequent agent-loop checks and `budget="high"` for deliberate deep planning, audits, or handoff recovery.
- Retain full structured conversations or task transcripts with stable `document_id`s and rich `context`; do not pre-summarize before retain. Use timestamps on all retained items so temporal retrieval works.
- Treat the database as truth. After pushing these files with `scripts/push_banks.py`, let the script pull back server-normalized snapshots.

## Template workflow

1. Edit `playground/templates/coding-assistant.json`.
2. Dry-run it against the live API before changing a bank.
3. Import it into a playground bank.
4. Run a scenario from `playground/examples/`.
5. Export the live bank back to a file when you want to snapshot server-side changes:

```bash
uv run python scripts/playground.py export-template playground-coding-assistant \
  --output playground/templates/exported-coding-assistant.json
```

The bank-template API is the preferred path because one manifest can keep bank config, directives, and mental models together.
