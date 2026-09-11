# Recall Threshold Experiment Design

**Date:** 2026-07-07
**Purpose:** Determine optimal per-bank thresholds using real pi-collab messages against real production banks, with full score extraction from traces.

---

## Bank → Query Mapping

| Bank | Queried by | Query Source |
|------|-----------|--------------|
| user-profile | User messages | Composer session messages |
| product-strategy | User messages | Composer session messages |
| framework-procedural | User messages | Composer session messages |
| implementation-work | Delegation messages | Worker/orchestrator session messages |
| assistant-ops | **Unused** — no scheduled assistants exist yet |

**Important:** Only composer banks have per-bank thresholds configured (all at 0.30). `implementation-work` uses global default (0.05). `assistant-ops` is skipped entirely.

---

## Data Sources

### Composer sessions
- Source: pi-collab TUI session transcripts (composer messages)
- Content: Full user messages from Seth — conversational, technical, exploratory
- Not: tiny canary snippets like "What is the Atlas MVP product scope?"

### Delegation sessions
- Source: worker session transcripts (builder, researcher, reviewer, spec-writer)
- Content: Full delegation messages — handoff text, test results, research findings
- Not: generic query text

---

## Experiment Steps

### Step 1: Extract real messages
1. Parse pi-collab session logs for **composer messages** (role: user, from composer context)
2. Parse pi-collab session logs for **delegation messages** (role: user, from worker context)
3. Select ~15 composer messages and ~10 delegation messages — short, medium, long turns
4. Filter out: blank messages, system messages, tool output, debug noise lines

### Step 2: Recall with trace
For each message:
1. **Composer messages** → recall against each of the 3 composer banks (user-profile, product-strategy, framework-procedural)
2. **Delegation messages** → recall against each of the 2 worker banks (implementation-work, assistant-ops)
3. Use `budget: mid`, `max_tokens: 1200`, `trace: true`
4. Use **raw message text** as the recall query (not contextual query shaping)
5. Extract all score fields per result from `trace.final_results`

### Step 3: Score extraction per result
For each recalled result, extract:
- `cross_encoder_score` (raw)
- `cross_encoder_score_normalized` (sigmoid → [0,1])
- `combined_score` (CE × recency × temporal × proof)
- `recency` (0.5 = neutral)
- `temporal` (0.5 = neutral)
- `proof_count` (evidence strength for observations)
- `semantic_similarity` (vector similarity)
- `rrf_score` (fusion score)
- `weight` (final ranking weight)
- `text` (the memory text)
- `fact_type` (world/experience/observation)
- `bank_id` (which bank it came from)

### Step 4: Classification
For each result, classify as:
- **Clearly relevant**: directly addresses the message's intent
- **Marginally relevant**: related but not directly answering
- **Noise**: stale, generic, or tangential

Classification is done by checking if the returned memory text contains key terms from the original message.

### Step 5: Analysis
1. **Score distribution per bank** — histogram of ce_normalized and combined_score per relevance bucket
2. **Separation analysis** — is there a gap between relevant and noise scores?
3. **Metric comparison** — ce_normalized vs combined_score for thresholding
4. **Per-bank threshold recommendation** — what floor value filters noise while keeping relevant results?
5. **Universal threshold viability** — can one threshold work across all banks?

---

## Expected Output

### Research doc: `docs/recall-threshold-analysis-real.md`
- Score distribution tables/charts per bank
- Relevance classification results
- Comparison: ce_normalized vs combined_score
- Threshold viability per bank and universally
- Recommended per-bank thresholds
- Recommended metric (ce_normalized vs combined_score)

### Raw data: `/tmp/recall_real_score_data.json`
- Full trace data for all recall calls
- Score fields per result
- Classification labels

---

## Design Notes

### Why real messages matter
The canary experiment used synthetic queries that perfectly matched their content. Real messages are:
- Conversational ("when i ask a question that is specific and maybe a little ambiguous...")
- Fragmented ("i just want a model that can chat with me")
- Technical ("the coordinator should be allowed to say whatever the fuck it wants")
- Context-dependent ("i gave you a good system (i think)")

These produce different score distributions than canned queries.

### Why raw messages, not contextual queries
Current config uses contextual queries like "Seth's current workspace state..." which are tailored per bank. Testing with raw messages:
- Simulates what happens when we remove contextual query shaping
- Tests whether raw user messages can be scored directly
- Reveals whether banks are too permissive with generic queries

### Why only mid budget
Previous experiments showed budget level doesn't affect scores — only DB search scope. Testing all 3 budget levels is redundant.

### Why both composer and delegation messages
Different banks receive different query shapes:
- Composer banks get conversational/product questions
- Worker banks get technical/delegation text

Testing both ensures we calibrate thresholds for all banks, not just the composer ones.
