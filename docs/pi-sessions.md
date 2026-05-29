# Pi Sessions → Hindsight Client Notes

This document captures the client-side design constraints for implementing Hindsight memory writes in `pi-ghosty` / Pi orchestration.

## Hindsight retain guidance that matters

From Hindsight docs and current local testing:

- Retain a full conversation/session artifact as a single document when possible.
- Use a stable `document_id` so repeated writes are idempotent.
- Default `update_mode: "replace"` deletes the old document's memories and reprocesses the new content.
- `append` exists for incrementally growing documents, but Hindsight docs describe sending only new content for append. Previous local trials found delta-only append less reliable for this workflow.
- Hindsight best practices allow retaining after each turn **or** at session end.
- Do not retain and then require recall from that write in the same active turn.

Design implication: for Pi, it is acceptable and simpler to treat Hindsight as long-term memory and not retain every active turn. The active session remains in Pi context/session storage until a lifecycle boundary.

## Pi lifecycle events relevant to memory

Pi provides these extension events relevant to session lifecycle:

- `session_start`
  - reasons: `"startup" | "reload" | "new" | "resume" | "fork"`
- `session_shutdown`
  - reasons: `"quit" | "reload" | "new" | "resume" | "fork"`
- `session_before_switch`
  - before `/new` or `/resume` / session switch
- `session_before_fork`
  - before `/fork` or `/clone`
- `session_before_compact`
- `session_compact`
- `session_before_tree`
- `session_tree`
- `agent_end`
- `turn_end`

Practical canary testing confirmed that a real `pi --mode rpc` process emits the needed events for clone/fork, new session, switch/resume, and quit.

## Recommended production write policy

### Normal active turns

Do not retain by default.

The current session is already in Pi context/session storage. Hindsight is used for prior durable memory, not for facts from the currently active turn.

### Session shutdown

On `session_shutdown` for:

```text
quit, new, resume, fork
```

retain with:

```text
update_mode: replace
```

Use stable document IDs.

For a normal/root/resumed session, use a real concrete ID. Placeholder examples use braces here to avoid implying XML/HTML content:

```text
pi-session:{session_id}:root
```

or, if branch leaf identity is needed:

```text
pi-session:{session_id}:{active_leaf_or_branch_id}
```

Include metadata such as:

```json
{
  "pi_session_id": "...",
  "pi_session_file": "...",
  "pi_leaf_id": "...",
  "event": "session_shutdown",
  "shutdown_reason": "quit|new|resume|fork"
}
```

### Resume

Do not retain immediately on `session_start(reason="resume")`.

Pi already has the session file. Continue the session normally, then retain when that resumed session shuts down.

Use the same logical document ID for the resumed root/session artifact so `replace` updates the document instead of creating duplicate session memory.

### Fork / clone

Do **not** retain the full copied ancestor path for every fork. That duplicates parent facts across branch documents.

Recommended fork document content:

```text
fork-specific turns after the fork point
```

Parent/lineage should go in metadata/tags, not repeated transcript content:

```json
{
  "pi_session_id": "...",
  "pi_leaf_id": "...",
  "parent_session_id": "...",
  "parent_leaf_id": "...",
  "fork_point_entry_id": "...",
  "event": "session_shutdown",
  "fork": "true"
}
```

Example document ID:

```text
pi-session:{session_id}:fork:{fork_id}
```

This supports the common workflow:

```text
do task A → fork back → do task B → fork back → do task C
```

without re-retaining the same parent context into every task branch.

### Compaction

Pi compaction is lossy for active context, but the full JSONL history remains in the session file.

On `session_compact`, retain a separate compaction artifact:

```text
pi-compaction:{session_id}:{compaction_entry_id}
```

Do not treat compaction as a whole-session end.

Also exclude compaction entries from normal full-session transcript serialization if compaction artifacts are retained separately; otherwise the same summary can be double-written.

### Reload

`session_shutdown(reason="reload")` exists, but should probably not retain by default unless implementation needs it. Reload is an extension/config lifecycle event, not a semantic session boundary.

## Transcript serialization notes

Production serialization should be Pi-shaped, not generic chat-only text. The retain API request itself is JSON, but the `content` field can be a string.

Current canaries send a plain line-oriented transcript string inspired by Pi's compaction serialization, not XML-tagged diffs and not stringified JSON. Earlier local integrations used stringified JSON arrays/objects inside `content`; that can work, but it is not what produced the latest good canary results. If `pi-ghosty` reimplements this, match the canary first: JSON HTTP payload whose `content` value is a line-oriented transcript string.

Reasoning:

- Pi's own compaction serializer feeds the model line-oriented text like `[User]: ...`, `[Assistant]: ...`, `[Tool result]: ...`.
- Hindsight retain prompts already wrap the content with the bank mission/config; the canary is exercising those real prompts through the real API.
- Line-oriented transcript text is easier for the model to read than a huge escaped JSON string and avoids append-concatenation problems if append is ever revisited.
- Keep original Pi JSONL/session IDs in metadata for provenance rather than forcing the whole source JSON into the model-facing content.

Include:

- user messages
- assistant text
- relevant assistant tool calls at a compact level
- tool results only when useful, truncated similarly to Pi compaction serialization
- custom messages if they participate in context
- branch summaries only if they are part of the active branch context and not separately retained

Avoid retaining raw noise:

- transient debug logs
- token budget chatter
- stack traces unless diagnostic/durable
- full tool dumps
- repeated command output

The current canary serializes tool results with a cap and checks that synthetic debug markers do not become stored facts.

## Bank routing implications

The five-bank topology remains useful, but production should not blindly retain every session to every bank.

Route based on the kind of session/artifact:

- `local-agent-user-profile`: durable user preferences, goals, communication style
- `local-agent-product-strategy`: product plans, accepted/rejected decisions, open questions, UX/scope/data strategy
- `local-agent-implementation-work`: worker handoffs, technical findings, test results, blockers, API contracts
- `local-agent-assistant-ops`: scheduled assistant outputs, standing ops rules, follow-ups
- `local-agent-framework-procedural`: durable procedures/rules for the agent framework itself

Concurrent writes to multiple banks are expected mainly when several worker/user-facing sessions end around the same time.

## Current canaries

### Per-bank structured quality

```bash
uv run python scripts/memory_canary.py --all --suffix <run-id>
```

Previously passed with all five configured banks and validates structured tags/entities/strict recall.

### Pi lifecycle + Pi transcript retain

```bash
uv run python scripts/pi_hindsight_integration_canary.py --all --suffix <run-id>
```

Current passing runs:

```text
uv run python scripts/pi_hindsight_integration_canary.py --all --suffix final2
summary: failures=0

uv run python scripts/pi_hindsight_integration_canary.py --all --suffix 20260527T224911Z
summary: failures=0
```

Captured run log:

```text
/home/poop/runs/hindsight-highlights/pi-integration-20260527T224911Z.log
```

What it proves:

- real Pi RPC process + extension can observe needed lifecycle events
- clone/fork/new/resume/quit produce usable `session_shutdown` boundaries
- Pi JSONL-shaped transcripts retain successfully through Hindsight
- `replace` with stable document IDs works for resumed sessions
- fork suffix retention avoids obvious parent/fork duplicate facts
- compaction artifact retention works separately
- strict recall finds the expected implementation decisions/contracts
- debug/tool-noise markers did not become facts in the tested run

Known caveats from this test:

- Hindsight can still produce a small number of duplicate-ish facts with timestamp/provenance variants. The canary reports these as warnings, not failures, because observations/consolidation may clean them up, but production should monitor them.
- This canary uses the real Hindsight API and real retain pipeline, including the configured bank missions/entity labels and Hindsight's own retain prompt overhead. It is not a direct/raw model call.
- Auto-consolidation was observed indirectly in the captured run: the canary bank had completed `consolidation` operations and returned `fact_type: observation` memories. However, this canary does not yet assert consolidation quality or backlog behavior.

### Consolidation / observation structure

```bash
uv run python scripts/consolidation_canary.py --suffix <run-id> --timeout 240
```

Current passing run:

```text
uv run python scripts/consolidation_canary.py --suffix 20260527T231714Z --timeout 240
summary: failures=0
```

Captured run log:

```text
/home/poop/runs/hindsight-highlights/consolidation-20260527T231714Z.log
```

What it proves:

- `enable_auto_consolidation` produced completed `consolidation` operations without manual triggering.
- Stored observations have `fact_type: observation`.
- Observations are tagged; the passing run's top observation had controlled tags such as `artifact_type:decision` and `work_phase:build`.
- Source facts had consolidation markers (`consolidated_at` or `consolidation_failed_at`); in the passing run there were zero unconsolidated source facts after completion.
- Strict recall with `types: ["observation"]` and `tags_match: "any_strict"` returned observations.
- Observation text captured the expected Pi session retain policy and did not contain synthetic debug/tool-noise markers.

Observed caveat:

- `source_fact_ids` in recall can contain repeated IDs. That looks like Hindsight provenance duplication rather than missing observation structure, but it is worth watching.

### Concurrent session-end burst

```bash
uv run python scripts/memory_concurrency_canary.py --suffix <run-id>
```

Current passing runs:

```text
uv run python scripts/memory_concurrency_canary.py --suffix smoke
summary: failures=0

uv run python scripts/memory_concurrency_canary.py --suffix 20260527T224911Z
summary: failures=0
```

Captured run log:

```text
/home/poop/runs/hindsight-highlights/concurrency-20260527T224911Z.log
```

What it proves:

- five canary banks can receive simultaneous synchronous retain calls
- local backend/model handled the burst without HTTP failures
- strict recall still worked afterward for all five banks

Observed concurrent retain timings in the smoke run were roughly 7–11 seconds per bank for small Pi-shaped transcripts.

## Open implementation questions for pi-ghosty

- Exact document ID scheme: whether root/resumed sessions should use `root`, active leaf IDs, or an explicit branch ID abstraction.
- How to persist fork-point metadata robustly across `/fork`, `/clone`, `/tree`, and orchestrator-created worker sessions.
- Whether worker sessions should retain only their final handoff artifact rather than full transcript.
- Whether session-end retain should be synchronous, queued in-process, or handed to a durable background worker.
- How to surface retain failures to the user/orchestrator without blocking Pi shutdown too long.
- Whether duplicate-ish fact warnings require a client-side suppression strategy or should be left to Hindsight consolidation.

## Current backend readiness assessment

The local Hindsight backend/model is ready enough to implement the Pi client integration behind a conservative feature flag:

```text
replace + stable document_id + session_shutdown/session_compact triggers + selective bank routing
```

Before enabling broadly, run the four canaries above after any bank config/model/runtime change.
