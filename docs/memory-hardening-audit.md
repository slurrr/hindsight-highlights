# Memory Hardening Audit

Date: 2026-05-31

## Current observed state

Sampled Hindsight via `GET /v1/default/banks/{bank}/memories/list`.

Approximate counts at audit time:

- `local-agent-user-profile`: 365 memories
- `local-agent-product-strategy`: 558 memories
- `local-agent-framework-procedural`: 495 memories
- `local-agent-implementation-work`: 39 memories
- `local-agent-assistant-ops`: 0 memories

## What is working

- Structural extraction is healthy: facts and observations are being produced.
- Tags are present and consistent (`source:pi`, `pi-collab`, `role:*`, `event:session_shutdown`).
- Implementation-work looks appropriately scoped for worker sessions and peer reports.
- Product-strategy and framework-procedural are broadly useful, though somewhat overlapping during framework bring-up.
- Full transcript retain is viable; no evidence yet that preprocessing is required for structural correctness.

## Main quality issue

`local-agent-user-profile` is too permissive. It is storing agent actions, tool calls, delegation tasks, and system/project facts as if they were user-profile memories.

Examples observed:

- grep/read/bash operations retained in the user-profile bank
- delegated test-file tasks retained as profile observations
- pi-collab role/system facts retained as profile observations

These are not user preferences, routines, durable personal facts, or feedback that helps Composer serve the user.

## Likely cause

The current user-profile mission is directionally correct but too broad for a full Pi transcript. Because the retained content includes user messages, assistant reasoning, tool calls, delegation events, and worker reports, the extractor sees many true facts. The mission says to ignore implementation details, but does not hard-require that facts be about the user or explicit user preferences/feedback.

This is a selectivity problem, not a tagging or Hindsight structure problem.

## Recommended next step

Do one stricter mission iteration before replacing the full retain prompt.

Applied first hardening pass:

- user-profile mission now repeatedly names Seth as the only profile subject
- mission includes a hard negative: if a chunk has no durable fact about Seth or Seth's preferences, extract nothing
- mission explicitly rejects assistant actions, tool calls, commands, files, delegated task details, framework facts, session events, debug logs, worker reports, and procedural rules
- observations mission now only synthesizes observations directly about Seth
- `entities_allow_free_form` is disabled for the profile bank to reduce graph/entity noise from filenames, tools, framework concepts, and transient implementation nouns

Use Hindsight's recommended progression:

1. tighten `retain_mission`
2. tighten `observations_mission`
3. improve per-retain `context` for this bank
4. only then switch the bank to `retain_extraction_mode: custom` with `retain_custom_instructions`

## Proposed user-profile policy

The user-profile bank should extract only:

- explicit user preferences
- explicit feedback about assistant behavior
- durable user goals and priorities
- recurring workflow/style preferences
- durable personal constraints
- standing commitments/routines
- important relationships/interests when user-relevant

It should not extract:

- assistant/tool actions
- delegated task details
- files created for tests
- implementation facts
- pi-collab architecture facts
- session lifecycle events
- one-off commands
- worker output unless it reveals durable user preference/feedback

## If mission tightening fails

A custom retain prompt is justified for `local-agent-user-profile` only.

Reason: profile memory has stricter inclusion semantics than normal fact extraction. For this bank, false positives are worse than false negatives because noisy profile recall directly affects Composer behavior.

Custom mode should still preserve Hindsight structure and only replace selection guidelines. It should be narrow: extract user-profile facts only when the fact is explicitly about the user or their preferences/workflow/feedback.

## Product/framework tightening

Product-strategy and framework-procedural are usable, but can be tightened later:

- Product-strategy should reject pure debug/test execution facts unless they changed product direction, acceptance criteria, or requirements.
- Framework-procedural should keep reusable rules/contracts/lessons and reject one-off command logs.

Do not over-tune these until more diverse non-pi-collab sessions exist.

## Transcript memory pruning

Current debug memory rendering not serializing into the retained transcript is good.

Later improvement: prune recalled memories from prior turns (`n - 1` recall blocks) before retain so the session transcript does not recursively re-retain older memory. This is lower priority than user-profile selectivity because current bad examples are primary transcript facts, not recalled-memory echoes.
