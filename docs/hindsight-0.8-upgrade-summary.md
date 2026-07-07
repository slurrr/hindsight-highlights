# Hindsight 0.8.x upgrade summary for local service + pi-collab

Date: 2026-06-11
Repo: `/home/poop/code/dev/hindsight-highlights`
Target package line: `hindsight-api` / `hindsight-client` `0.7.0 -> 0.8.1`

## Baseline observed before upgrade

- Installed local packages:
  - `hindsight-api==0.7.0`
  - `hindsight-api-slim==0.7.0`
  - `hindsight-client==0.7.0`
- `uv lock --upgrade-package hindsight-api --upgrade-package hindsight-client --dry-run` resolves only these Hindsight updates plus `pg0-embedded 0.14.1 -> 0.14.2`.
- `hindsight-api.service` was observed installed but inactive earlier; a later healthcheck found API healthy at `127.0.0.1:8888`, Postgres listening at `127.0.0.1:5432`, and vLLM not listening at `127.0.0.1:8002`.
- Current repo uses external Fedora PostgreSQL through:
  - `HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:hindsight@127.0.0.1:5432/hindsight`
  - `HINDSIGHT_API_MIGRATION_DATABASE_URL=postgresql://hindsight:hindsight@127.0.0.1:5432/hindsight`

## Release notes relevant to this deployment

### 0.8.1 highlights

Most 0.8.1 changes are integrations/docs. Relevant local-service items:

- **Migration fix for `public` schema**: maintenance routines now install correctly when `target_schema=public` / default schema. This matters directly because this repo currently does not set `HINDSIGHT_API_DATABASE_SCHEMA`, so it uses `public`.
- **Local ML dependency cap**: `tokenizers<=0.23.0` for local ML extras. This matters because this service initializes local embedding/reranker models in-process.
- **Document text storage flag**: new `HINDSIGHT_API_STORE_DOCUMENT_TEXT`; default remains `true`. If set `false`, Hindsight does not persist raw source document text (`documents.original_text` / raw chunk text). This is privacy/storage-reduction relevant, but has behavior tradeoffs for append/reprocess/detail flows.
- **vchord fix**: stops forcing `vchordrq.probes` on listless vchord indexes. Not relevant unless we switch from default `pgvector`/native text search to vchord.

### 0.8.0 highlights

Relevant backend/API/runtime changes:

- **Retain same-document concurrency hardening**: pre-extraction freshness recheck and serialized concurrent same-document writers. This is important for pi-collab because it uses stable `document_id` plus `update_mode: replace` at session shutdown; it reduces race risk if manual retain and shutdown retain overlap.
- **Bank config PATCH persists for never-retained banks**: useful for this repo’s bank-as-config workflow (`config/banks/*.json`, `scripts/push_banks.py`) before any memory exists in a bank.
- **Consolidation/observation quality improvements**:
  - duplicate observations eliminated
  - semantic dedup of near-duplicate observations
  - observation dedup enabled by default at threshold `0.97`
  - consolidation output token budget set
  These are important because pi-collab recall now leans heavily on `types: ["observation"]` for the user-profile bank.
- **Maintenance/reconcile loop**: periodic consolidation reconcile + cross-tenant retention via maintenance loop. Default interval discovered in 0.8.1 package config: `HINDSIGHT_API_CONSOLIDATION_RECONCILE_INTERVAL_SECONDS=300`.
- **Durable operation progress snapshots**: consolidation and batch retain expose more durable progress. Useful for future diagnostics around async pi-collab retain.
- **LLM request tracing defaults**:
  - per-bank LLM request tracing via OTel GenAI recorder
  - LLM request tracing enabled by default with 1-day retention
  Useful for debugging memory extraction/consolidation, but increases metadata retention in DB. Decide whether to explicitly disable or document this for local privacy.
- **LLM prompt-prefix caching**: default-on provider prompt caching for retain, consolidation, and reflect. Discovered config: `HINDSIGHT_API_LLM_PROMPT_CACHE_ENABLED=true`. Should help repeated memory operations if the backend supports it.
- **LLM compatibility fixes for local OpenAI-compatible servers**:
  - `HINDSIGHT_API_LLM_EXTRA_BODY` now applies across API providers
  - strict JSON schema support widened across json-schema-capable providers
  - `tool_choice="required"` downgraded for servers that silently drop it, including vLLM / LM Studio / Ollama
  This is directly relevant because this repo uses provider `openai` against local vLLM at `127.0.0.1:8002/v1`.
- **Recall improvements/tuning**:
  - per-strategy retrieval boost via `HINDSIGHT_API_RECALL_STRATEGY_BOOSTS`
  - configurable semantic floor `HINDSIGHT_API_SEMANTIC_MIN_SIMILARITY` (default discovered: `0.3`)
  - temporal entry-point scan bounded to top-50-per-fact_type
  - trace preserves RRF source ranks
  Useful for pi-collab’s dynamic memory relevance plan, especially trace-based filtering.
- **Bank stats performance**:
  - cheaper bank stats with result cache
  - discovered defaults: `HINDSIGHT_API_BANK_STATS_CACHE_TTL_SECONDS=60`, `HINDSIGHT_API_BANK_STATS_CACHE_MAX_ENTRIES=1024`
- **History storage migration**: mental-model and observation history moved into dedicated tables. This implies DB migrations on first 0.8.x startup are substantive; back up or snapshot before upgrading if memory contents matter.
- **External Postgres/vchord search path fix**: adds vchord catalogs to `search_path` for external Postgres. Only relevant if switching extensions.
- **Document/bank transfer**: export/import documents and whole banks without re-running LLM. Useful future path for backups or moving between Hindsight instances.
- **Retain outcome metadata exposed**: useful for client diagnostics if pi-collab later wants richer retain receipts.

## PostgreSQL-service implementation impact

Current local architecture is still aligned with upstream recommendations:

- External PostgreSQL 15+ with pgvector is the production path.
- Embedded `pg0` is only used when `HINDSIGHT_API_DATABASE_URL` is absent; this repo correctly sets database URLs, so the `pg0-embedded` update is not operationally relevant unless env loading breaks.
- Because 0.8.x includes migration and history-table changes, keep `HINDSIGHT_API_MIGRATION_DATABASE_URL` set to the direct Postgres URL and allow startup migrations, or run migrations manually with `hindsight-admin run-db-migration` before service start.
- For this single-user local system, keep defaults unless a problem appears:
  - `HINDSIGHT_API_DATABASE_BACKEND=postgresql` can be left implicit, but setting it explicitly would document intent.
  - `HINDSIGHT_API_STORE_DOCUMENT_TEXT=true` should stay default for pi-collab for now because pi-collab uses replace/upsert transcripts and may benefit from document detail/reprocess/debugging. Consider `false` only if raw transcript retention becomes a privacy/storage concern.
  - `HINDSIGHT_API_LLM_PROMPT_CACHE_ENABLED=true` should stay default.
  - `HINDSIGHT_API_SEMANTIC_MIN_SIMILARITY=0.3` should stay default until recall quality is measured.
  - `HINDSIGHT_API_RECALL_STRATEGY_BOOSTS` should remain unset until a trace-driven tuning pass.
- If vLLM is down, Hindsight can still start but LLM-dependent retain/consolidation/reflect can fail. This behavior remains important for interpreting `hindsight status` vs full memory-stack readiness.

## pi-collab client impact

Observed pi-collab repo: `/home/poop/code/dev/pi-collab`.

Current client implementation uses raw HTTP endpoints:

- Recall: `POST /v1/{namespace}/banks/{bank_id}/memories/recall`
- Retain: `POST /v1/{namespace}/banks/{bank_id}/memories`
- Namespace: `default`
- Banks by role are configured in `collab.config.json`.

### Good news / compatible areas

- pi-collab already uses `max_tokens`, not the older `max_results` name.
- pi-collab already uses stable `document_id` and `update_mode: "replace"`, which is strengthened by 0.8.0 same-document writer serialization.
- pi-collab’s user-profile recall uses `types: ["observation"]`, which should benefit from 0.8.x observation dedup and consolidation fixes.
- pi-collab avoids retaining injected `Hindsight.recall` messages into transcripts, preventing memory feedback loops.
- Existing endpoint paths and payload shapes appear still aligned with the documented API.

### Client changes worth considering after backend upgrade

1. **Improve retain diagnostics**
   - 0.8.x exposes richer retain outcome metadata. pi-collab currently treats a 2xx as `{ ok: true }` and drops response details.
   - Consider capturing and showing operation IDs / receipt metadata in `/collab memory retain-now` and ASS `pi_collab.memory_retain_completed`.

2. **Use trace for dynamic recall gating**
   - 0.8.x trace improvements preserve RRF source ranks, and pi-collab already has `docs/dynamic-memory-relevance-plan.md` proposing `trace: true`.
   - Next client pass can request `trace: true`, score/filter results, and avoid memory walls on casual turns.

3. **Review raw transcript retention policy**
   - New `HINDSIGHT_API_STORE_DOCUMENT_TEXT=false` makes it possible to avoid storing full raw transcript text server-side.
   - Do not enable yet without testing: pi-collab’s current model intentionally retains full line-oriented transcripts, and disabling document text affects append/document detail/reprocessing semantics.

4. **Tune user-profile recall after upgrade**
   - Because observation dedup changes result quality, validate composer recall against real prompts.
   - If irrelevant memories still appear, prefer client-side trace gating first; use server `HINDSIGHT_API_RECALL_STRATEGY_BOOSTS` only after collecting traces.

5. **Surface full-stack status**
   - pi-collab can report Hindsight API health separately from LLM backend readiness. Current Hindsight `/health` can be OK while vLLM is unavailable.

## Recommended upgrade execution plan

1. Back up/snapshot the current DB if contents matter:

```bash
pg_dump 'postgresql://hindsight:hindsight@127.0.0.1:5432/hindsight' > /home/poop/backups/hindsight-$(date -u +%Y%m%dT%H%M%SZ).sql
```

2. Stop Hindsight API before changing packages:

```bash
cd /home/poop/code/dev/hindsight-highlights
./scripts/hindsight down
```

3. Apply package update:

```bash
uv lock --upgrade-package hindsight-api --upgrade-package hindsight-client
uv sync
```

4. Start API and let migrations run:

```bash
./scripts/hindsight up
```

5. Validate service and memory behavior:

```bash
uv run python scripts/healthcheck.py || true
uv run python scripts/memory_canary.py --all
uv run python scripts/pi_hindsight_integration_canary.py --all
uv run python scripts/consolidation_canary.py
```

6. Validate pi-collab manually:

```bash
cd /home/poop/code/dev/pi-collab
# In a pi-collab session:
# /collab memory status
# /collab memory recall hindsight upgrade
# /collab memory retain-now
```
