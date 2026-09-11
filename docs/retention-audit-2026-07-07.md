# Hindsight Retention & Recall Deep-Dive Audit

**Date:** 2026-07-07
**Scope:** Retain, recall, consolidation, and canary testing across hindsight-highlights + vendor/hindsight

---

## 1. Recent Changes Timeline

### hindsight-highlights ops repo (config + tooling)
| Commit | What changed |
|--------|-------------|
| `048f69d` | Healthcheck scripts + docs cleanup |
| `4474da5` | Wire Hindsight journal logs into Loki monitoring |
| `dde9166` | Fix Grafana scraping |
| `7f031cf` | Auto-apply bank configs on startup |
| `9baa728` | Bank config drift check |
| `2a5b5fa` | Switch to manual systemd service + command wrapper |
| `0f4f241` | Plan reflect + mental model integration |
| `a3ca006` | Document memory write audit |
| `ff5b67f` | Add memory write audit workflow |
| `cdbc18e` | Tighten user profile memory extraction |
| `869184e` | Clarify Pi session lifecycle + retention rules |
| `56c429a` | Document Pi session lifecycle + retention strategies |
| `48578d9` | Extensive fresh bank configs + restore swarm draft |
| `338990a` | Spec for fresh pi-ghosty bank bootstrap |
| `2adc1da` | Bank config pull/push scripts (DB snapshot workflow) |
| `d6cf873` | Make repo a config control surface |
| `e7ae5e2` | Add Makefile + enhance README |

### vendor/hindsight upstream (key recall/retain/pruning changes)
| PR | Change |
|----|--------|
| #2147 | Haystack integration (auto-retain/recall wrapper) |
| #2149 | Per-scope observation limits |
| #2140 | Consolidation: per-scope observation limits |
| #2131 | Recall/reflect disconnect cancellation |
| #2127 | Cancel abandoned recall & reflect via cooperative token |
| #2126 | Retain: chunk JSONL at line boundaries |
| #2039 | Configurable HINDSIGHT_API_SEMANTIC_MIN_SIMILARITY |
| #2046 | recall-temporal suite (forces temporal arm) |
| #2041 | Retain: expose outcome metadata |
| #2052 | Fold recall into first system section |
| #2011 | Fresh mental model can short-circuit forced retrieval |
| #1976 | Reversible curation: edit/invalidate/revert memory units |
| #1969 | Periodic reconcile + cross-tenant retention via maintenance loop |
| #2122 | Cancel abandoned recall via cooperative token |

---

## 2. Current Recall Architecture

### Flow
1. **Query analysis** → fact types, question date, tags
2. **4-way parallel search** (semantically independent):
   - Semantic (vector similarity)
   - BM25 (full-text / keyword)
   - Graph (entity-link expansion)
   - Temporal (time-aware search with spreading)
3. **Reciprocal Rank Fusion (RRF)** merges all arms → ranked pool
4. **Cross-encoder reranking** → relevance scoring
5. **Combined scoring** → CE score × recency_boost × temporal_boost × proof_count_boost
6. **Token budget filtering** → stop before exceeding max_tokens

### Key Config Knobs
| Knob | Default | Meaning |
|------|---------|---------|
| `recall_budget_function` | `fixed` | Maps budget enum to integer |
| `recall_budget_fixed_low/mid/high` | 100/300/1000 | DB query budget (thinking_budget) |
| `recall_budget_adaptive_*` | 0.025/0.075/0.25 | Ratio of max_tokens |
| `recall_budget_min/max` | 20/2000 | Clamp floor/ceiling |
| `DEFAULT_RECALL_MAX_TOKENS` | 2048 | Token budget for returned facts |
| `HINDSIGHT_API_RERANKER_MAX_CANDIDATES` | 300 | Global candidate budget on reranker |
| `recall_connection_budget` | 4 | Max concurrent DB connections per recall |
| `recap_per_source_cap` | 0 (disabled) | Per-arm result cap before fusion |
| `recall_boost` | none | Strategy-level arm prioritization |

### Current Budget Resolution
With `recall_budget_function=fixed` (current default):
- `budget=low` → `thinking_budget=100` (DB search scope)
- `budget=mid` → `thinking_budget=300`
- `budget=high` → `thinking_budget=1000`

With `recall_budget_function=adaptive` (not yet used):
- `budget=low` → `round(max_tokens × 0.025)`, clamped to [20, 2000]
- `budget=mid` → `round(max_tokens × 0.075)`
- `budget=high` → `round(max_tokens × 0.25)`

**Critical insight:** `thinking_budget` controls how aggressively the DB searches (vector + BM25 + graph hops). `max_tokens` controls how many results actually come back. These are two separate knobs.

---

## 3. Current Retain Architecture

### Flow
1. **Chunking** → split by JSONL line boundaries (recent PR #2126)
2. **Structured extraction** → xgrammar for JSON schema compliance
3. **Fact creation** → world/experience/opinion facts with tags + entities
4. **Auto-consolidation** → merges similar facts into observations (if enabled)

### Bank Configuration
Each bank has:
- `retain_mission` → selection guidelines for the LLM
- `observations_mission` → consolidation guidelines
- `reflect_mission` → explicit reflect query guidance
- `entity_labels` → controlled vocabulary for tags
- `disposition_*` → LLM tone controls
- `enable_auto_consolidation` → toggle

### Current Banks
| Bank | Purpose | Status |
|------|---------|--------|
| `local-agent-user-profile` | Durable personal facts about Seth | Tightened (May 31 audit) |
| `local-agent-product-strategy` | Product planning, decisions, scope | Usable but overlapping |
| `local-agent-framework-procedural` | Reusable rules, contracts, procedures | Usable |
| `local-agent-implementation-work` | Implementation handoffs, test results | Limited use |
| `local-agent-assistant-ops` | Scheduled assistant output, ops memory | Not yet populated |

---

## 4. What We've Tried (Testing & Canary Suite)

### memory_canary.py — Structured extraction + recall
**What it does:** Retains a synthetic scenario into a canary bank, then recalls with both broad and strict tag queries.
**5 scenarios** — one per bank.
**Checks:** memory count, tag presence, entity extraction, required/forbidden tags, recall term matching, strict tag recall.
**Limitation:** Tests *extraction quality* under controlled conditions, not *recall quality* on real content.

### session_evolution_canary.py — Replace vs append
**What it does:** Same evolving transcript through two modes — replace (re-retain full transcript after each step) vs append (retain only new turns).
**Checks:** fact density, duplicate-ish facts, controlled tags, strict recall, debug-log spam detection.
**Limitation:** Narrowly tests update_mode behavior on a single transcript, doesn't test recall on diverse content.

### pi_hindsight_integration_canary.py — Pi lifecycle integration
**What it does:** Tests Pi-shaped session JSONL retention — session_shutdown triggers, full active-branch transcripts, resume/update/fork/clone lineage, compaction-entry handling.
**Limitation:** Tests *retain* pipeline end-to-end, not recall.

### memory_concurrency_canary.py — Burst retain testing
**What it does:** Simulates multiple Pi sessions ending simultaneously, retaining to different banks. Uses Barrier for synchronized starts.
**Checks:** retain succeeds, recall finds expected content.
**Limitation:** Tests concurrent writes, not recall quality.

### consolidation_canary.py — Observation generation
**What it does:** Retains several overlapping session-end documents, waits for auto-consolidation, verifies observations are generated correctly.
**Checks:** observation creation, controlled tags, recall structure.
**Limitation:** Tests consolidation pipeline, not recall directly.

### memory_write_audit.py — Read-only inspection
**What it does:** Inspects recent writes — facts, observations, stats, mental models.
**Checks:** compact stats, recent world/experience facts, recent observation consolidations, mental model metadata.
**Limitation:** Not a recall test. Diagnostic only.

### healthcheck.py — Service dependency check
**What it does:** TCP/HTTP checks for Postgres, Hindsight API, LLM, Grafana stack.
**Limitation:** Infrastructure health, not memory quality.

---

## 5. Current State Assessment

### What's working well
1. **Retain pipeline is stable** — structured extraction produces facts with proper tags and entities
2. **4-way parallel search** covers semantic, lexical, graph, and temporal dimensions
3. **RRF fusion** prevents any single arm from dominating
4. **Cross-encoder reranking** adds meaningful relevance signal beyond RRF
5. **Combined scoring** correctly weights recency and temporal proximity
6. **Token budget filtering** prevents overlong responses
7. **Bank config as code** — versionable, reviewable, reproducible
8. **Concurrent retain** handles burst session-end writes

### Known quality issues (from memory-hardening-audit.md)
1. **User-profile was too permissive** — stored agent actions, tool calls, framework facts
   - Fixed: tighter mission, hard negative rules, disabled free-form entities
2. **Product-strategy and framework-procedural overlap** — both capturing similar content
3. **Canned queries don't reflect real recall patterns** — testing with synthetic queries that may not match actual usage

### Recall quality problems
The core issue is that **recall quality depends on the intersection of**:
1. How well retain captures the right facts (input quality)
2. Whether the search finds them (retrieval quality)
3. Whether the reranker ranks them appropriately (ranking quality)
4. Whether the token budget cuts off relevant results prematurely (budget quality)

**Current pain points:**
- `max_tokens=2048` is generous but may cut off relevant results for broad queries
- `thinking_budget=300` (mid) may not search deep enough for complex queries
- Cross-encoder reranker uses local MiniLM-L-6-v2 by default — good but not production-grade
- No per-bank recall tuning yet — all banks use the same budget/ranking settings
- `recall_boost` strategy is available but unused

---

## 6. Improvement Opportunities

### High impact (low effort)
1. **Tune recall_budget per bank** — product-strategy may need higher budget than user-profile
2. **Enable adaptive budget function** — scales with max_tokens, more intuitive
3. **Add recall boost strategies** — e.g., `graph:high` for entity-heavy queries, `semantic:low` for keyword-heavy
4. **Test recall on real transcripts** — not just canned queries, but actual Pi session content
5. **Log and compare recall results** — track what comes back for common queries, identify gaps

### Medium impact
6. **Switch reranker to external** (Cohere rerank-v3.5, Jina, or qwen3-rerank) for better ranking
7. **Per-bank max_tokens** — some banks may need tighter/looser budgets
8. **Implement `n-1` recall pruning** — strip previous recall blocks from session before retain to avoid recursive retention
9. **Add recall quality metrics** — track precision/recall over time
10. **Mental model integration** — use reflect for structured summaries (per the mental model plan)

### Lower impact / higher effort
11. **Custom retention prompts** per bank (replace full retain prompt with bank-specific)
12. **Entity deduplication** during retain to reduce graph noise
13. **Temporal recall tuning** — improve time-aware search
14. **Consolidation quality** — prevent duplicate observations
15. **Cross-bank recall** — search across multiple banks simultaneously

---

## 7. Next Steps Recommendation

1. **Run recall on real Pi transcript excerpts** — not canned scenarios. Take actual Pi session content, retain it, then recall with queries a real user would ask.
2. **Add recall logging** — log query, budget used, number of results, token count, and top-3 results for each recall call
3. **Profile current recall quality** — identify which queries return too few / too many / irrelevant results
4. **Tune per-bank settings** — based on profiling, set appropriate budget and max_tokens per bank
5. **Consider reranker upgrade** — if local MiniLM is insufficient, test external rerankers
6. **Implement the reflect/mental model plan** — start with `seth-working-profile` model if user-profile is clean enough
7. **Build a recall dashboard** — visualize recall quality over time (results count, token usage, relevance)

---

## 8. File Map

| File | Purpose |
|------|---------|
| `scripts/memory_canary.py` | Structured extraction + recall testing (5 scenarios) |
| `scripts/session_evolution_canary.py` | Replace vs append comparison |
| `scripts/pi_hindsight_integration_canary.py` | Pi lifecycle integration tests |
| `scripts/memory_concurrency_canary.py` | Burst retain concurrency |
| `scripts/consolidation_canary.py` | Observation generation testing |
| `scripts/memory_write_audit.py` | Read-only write inspection |
| `scripts/healthcheck.py` | Service dependency health |
| `config/banks/*.json` | Bank definitions (6 banks) |
| `env/hindsight.env` | Service env (LLM, DB, embeddings, reranker, observability) |
| `docs/memory-hardening-audit.md` | May 31 quality audit |
| `docs/reflect-mental-model-plan.md` | Reflect + mental models roadmap |
| `docs/PLAN.md` | Start-fresh service plan |
