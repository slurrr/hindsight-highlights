# Reflect and Mental Models Plan

## Current state

The banks already have `reflect_mission` and disposition settings. That means the backend is configured for `reflect`, but pi-collab is not yet calling reflect and no mental models have been created.

Important distinction:

- `retain_mission` drives fact extraction.
- `observations_mission` drives automatic consolidation into `fact_type: observation`.
- `reflect_mission` only affects explicit `reflect` calls.
- Mental models are saved/curated reflect responses. They are not created just because observations exist.

## Goal

Use Hindsight more fully without disrupting the proven recall/retain path:

1. Keep recall injection as the fast default.
2. Add reflect as an explicit diagnostic/planning command first.
3. Add curated mental models only after real external-project usage shows stable repeated questions.
4. Let pi-collab consume mental models through reflect later, not by inventing its own summary layer.

## What belongs where

### hindsight-highlights repo

This repo owns backend memory configuration and operations:

- bank configs
- scripts to create/list/refresh mental models
- reflect/mental-model audit scripts
- canaries for reflect quality
- run logs under `/home/poop/runs/hindsight-highlights/`

### pi-collab repo

pi-collab owns client usage:

- optional `/collab reflect ...` command
- optional `/collab memory-models` command
- optional reflect-backed Composer context in the future
- no durable mental-model source of truth

### Runtime config

Runtime config should decide whether pi-collab uses recall only or recall + reflect:

```text
PI_COLLAB_RECALL_ENABLED=true
PI_COLLAB_REFLECT_ENABLED=false initially
PI_COLLAB_REFLECT_BUDGET=low|mid|high
PI_COLLAB_MENTAL_MODELS_ENABLED=false initially
```

## Phase 1: Reflect audit tooling

Add a script here that calls:

```text
POST /v1/default/banks/{bank_id}/reflect
```

Use cases:

```bash
uv run python scripts/memory_reflect_audit.py \
  --bank local-agent-user-profile \
  --query "What durable preferences should Composer remember about Seth?" \
  --include-facts

uv run python scripts/memory_reflect_audit.py \
  --bank local-agent-framework-procedural \
  --query "What are the current pi-collab delegation and reporting rules?" \
  --include-facts
```

Output should include:

- reflect answer
- cited memories / observations / mental models via `include.facts`
- optional tool trace only when debugging

Purpose: verify reflect quality before wiring it into pi-collab.

## Phase 2: Mental model management scripts

Add scripts here for user-curated mental models:

```text
scripts/mental_models.py list --bank <bank>
scripts/mental_models.py create --bank <bank> --id <id> --name <name> --query <query> [--tag ...] [--refresh-after-consolidation]
scripts/mental_models.py refresh --bank <bank> --id <id>
scripts/mental_models.py show --bank <bank> --id <id>
```

Do not auto-create a large set immediately. Start with a few high-value models once the first external project produces real data.

## Candidate first mental models

### local-agent-user-profile

ID: `seth-working-profile`

Query:

```text
Summarize durable facts about Seth that should help Composer personalize collaboration: communication style, workflow preferences, long-running goals, constraints, interests, and assistant feedback. Exclude implementation details and one-off project tasks.
```

Suggested refresh:

- manual at first
- maybe `refresh_after_consolidation: true` later if quality is stable

### local-agent-framework-procedural

ID: `pi-collab-operating-rules`

Query:

```text
Summarize the current reusable operating rules for pi-collab: roles, delegation routing, peer_report behavior, ASS/ISCP usage, war-room behavior, memory policy, and safety constraints.
```

Suggested refresh:

- manual until architecture stabilizes
- delta refresh later if it becomes a long-lived playbook

### local-agent-product-strategy

ID: `active-project-direction`

Query:

```text
Summarize current active product/project direction, accepted decisions, open questions, risks, and next planning priorities. Exclude low-level command logs and implementation chatter.
```

Suggested refresh:

- manual per project milestone
- avoid broad global use until project tagging/scoping is clearer

### local-agent-implementation-work

ID: `implementation-state`

Query:

```text
Summarize current implementation state: accepted technical decisions, important files/modules, completed work, test results, blockers, and next handoff actions.
```

Suggested refresh:

- manual after meaningful worker sessions
- use tags later when per-project or per-thread scoping exists

## Phase 3: pi-collab commands

After reflect audit is useful, add pi-collab commands under `/collab`:

```text
/collab memory-reflect <bank> <query>
/collab memory-models
/collab memory-model-show <bank> <id>
```

These should be explicit user/debug commands first. Do not inject reflect output into every Composer turn yet.

## Phase 4: Runtime use in Composer

Only after quality is proven:

- keep recall injection for normal turn context
- optionally call reflect for session-start briefing or explicit planning moments
- optionally include mental model summaries in Composer startup context

Recommended first runtime use:

```text
on Composer session_start:
  reflect user-profile with a fixed query at low/mid budget
  inject a short "Seth working profile" note if enabled
```

Do not do this until profile memories are clean enough. Bad profile reflection would be worse than no reflection.

## Tag/scoping caution

Mental model tags affect both:

- which memories are used to build/refresh the model
- which reflect calls can see the model

Because current tags are broad (`source:pi`, `role:*`, bank entity labels), avoid aggressive tagging for initial mental models. Prefer untagged or simple bank-level models until project/thread tags exist.

## Acceptance criteria

Reflect is ready when:

- `include.facts` shows relevant observations/facts
- answers do not invent durable preferences or decisions
- user-profile reflect excludes tool/debug facts
- framework reflect gives reusable procedures, not raw session logs
- mental model content is short, stable, and worth injecting

Mental models are ready for pi-collab runtime when:

- they survive several refreshes without drifting
- they improve Composer behavior in real sessions
- they do not duplicate full transcript content
- they can be inspected and refreshed manually

## Implementation order

1. Add `scripts/memory_reflect_audit.py` in hindsight-highlights.
2. Test reflect on all four active banks with `include.facts`.
3. Add `scripts/mental_models.py` management script.
4. Create one manual `seth-working-profile` model if reflect quality is good.
5. Create one manual `pi-collab-operating-rules` model if framework reflect is clean.
6. Add pi-collab `/collab memory-reflect` and model listing commands.
7. Consider optional session-start mental model injection only after several successful external-project sessions.
