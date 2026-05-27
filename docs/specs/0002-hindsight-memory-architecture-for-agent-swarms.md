# Draft: Hindsight memory architecture for an agent swarm (pi-ghosty + scheduled assistants)

Status: draft for iteration

## Problem statement
We want a memory system that:
- improves multi-agent productivity (planning/research/spec/coding/review)
- supports scheduled personal-assistant agents (email triage, feeds/blogs/papers)
- captures user preferences and workflow style without polluting worker peers
- minimizes drift: no prompt-injected lore, no uncontrolled "helpful but wrong" memories
- is low-maintenance: operators can inspect/update config in `hindsight-highlights`, and clients can apply updates via API

Constraints:
- Hindsight quality depends heavily on **well-scoped retain missions**.
- A single universal mission cannot serve all agent roles without either underfitting (too generic) or overfitting (drift/pollution).

## Design principles (align with Hindsight guidance)
1) **Few banks, strong missions.** Prefer a small number of banks with clear roles over one universal bank with weak guidance.
2) **Banks represent semantic domains, not individual agents.** Avoid “one bank per agent” unless the agent is truly isolated.
3) **Access control via bank selection + tags.** Different agents recall from different bank sets; tags refine within a bank.
4) **DB is runtime truth; repo is editable snapshot.** `hindsight-highlights/config/banks/*.json` is an exportable view you can edit/push.
5) **Entity schema is explicit.** Keep entity labels consistent to avoid model-invented ontologies.

## Recommended bank topology (start-fresh baseline)
Instead of personal/procedural as the primary split, use **domain banks** that map to agent classes.

### A) Shared work brain (engineering/product)
- Bank ID: `pi-core`
- Used by: planners/researchers/spec-writers/reviewers/coders
- Content: repo maps, subsystem names, commands, infra conventions, durable project decisions, recurring workflow patterns

### B) User preferences + personal working style
- Bank ID: `user-seth`
- Used by: user-facing agent, personal-assistant agents
- Content: communication preferences, workflow phases, constraints, personal preferences, long-term goals
- **Hard rule:** do not store implementation details unless they are explicitly preferences/workflow.

### C) Personal-assistant operations (inbox/feeds)
- Bank ID: `pa-core`
- Used by: email triage, feeds/blogs/papers, calendar helpers
- Content: what to prioritize, summaries-of-summaries, standing rules (what to flag), recurring correspondents/topics, follow-up conventions

### Optional overlays (only if needed)
Add these only when you feel pain:
- Project overlays: `proj-<name>` (e.g. `proj-agentmux`, `proj-pi-ghosty`) when separation is beneficial.
- External-sources overlay: `reads-<domain>` (if you want long-running knowledge from papers/blogs separated from operational PA rules).

## Agent recall policy (how we get “specific peers get specific memories”)
Agents don’t need dedicated banks. They need a **recall policy** that selects banks.

Proposed default policies:
- Coding/engineering worker peer: recall from `[pi-core]` (+ `proj-*` when task scoped)
- Research/spec worker: recall from `[pi-core]` (+ `proj-*`)
- User-facing orchestrator: recall from `[user-seth, pi-core]` (+ `proj-*`)
- Scheduled personal assistant: recall from `[user-seth, pa-core]` (+ `pi-core` only when explicitly needed)

This solves the “scheduled peers” issue without per-agent banks.

## Tagging strategy (simple + composable)
Use tags to support filtering and to keep recall precise.

Baseline tag keys:
- `agent:<name>` (optional, for provenance)
- `role:<worker|pa|user>`
- `project:<slug>`
- `repo:<slug>`
- `topic:<slug>`
- `user:seth` (only for user-specific banks)
- `source:<email|feed|paper|chat|issue|pr|doc>`

Rule of thumb:
- Tags should help *exclude* irrelevant memories at recall time.

## Entity schema (explicit; avoid free-form drift)
Use a consistent entity label set across banks so linking is predictable.

Suggested labels:
- `project`
- `repo`
- `subsystem`
- `file`
- `command`
- `tool`
- `service`
- `model`
- `decision`
- `preference`
- `workflow_phase`
- `person`

Start with `entities_allow_free_form=false`.
If recall/linking feels too constrained, loosen later with a deliberate decision.

## Missions: why multiple banks are necessary
A universal memory bank fails because retain missions must be tight.

Each bank must have a distinct mission set:
- `pi-core`: technical structure + decisions + durable ops knowledge
- `user-seth`: preferences + workflow style only
- `pa-core`: prioritization rules + recurring topics + summarization norms

This is the lever that makes extraction quality high without drift.

## Fresh-start setup flow (high level)
1) Bring up Hindsight service + Postgres (system services).
2) Create banks: `pi-core`, `user-seth`, `pa-core`.
3) In `hindsight-highlights`, define bank config JSONs for each bank (missions + entity labels + defaults).
4) Apply via `push_banks.py` (auto pull after push).
5) Configure pi-ghosty to use the new recall policy per agent role.

## Backfill / building banks from past transcripts (optional but desired)
Goal: initialize banks with useful history without manual copy/paste.

Approach:
- Run a one-time backfill job that:
  - enumerates session transcripts (codex / pi sessions / productive logs)
  - filters out test-only sources (OpenWebUI/TUI experiments) via path rules
  - batches documents into the appropriate banks:
    - engineering transcripts -> `pi-core`
    - preference-heavy transcripts -> `user-seth`
    - email/feed summaries -> `pa-core`

Important: backfill should be idempotent and provenance-tagged (`source:*`, `import:*`).

## Drift control / safety knobs
- Keep missions narrow.
- Prefer skepticism/literalism settings that avoid over-inference.
- Keep recall budgets conservative; increase only when you can measure benefit.
- Audit DB-truth periodically (the whole point of highlights snapshot + inspect scripts).

## What we still need to decide
1) Bank IDs/names (final)
2) Default recall budgets per agent role
3) Backfill inclusion/exclusion rules (which transcript roots count)
4) How much free-form entities to allow (default: off)
