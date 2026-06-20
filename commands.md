# Hindsight Highlights command surface

This repo uses a **manual `systemd --user` service** plus a `hindsight` command wrapper for the Hindsight API.

- **Service/runtime logs:** journald
- **Run artifacts / experiments:** `~/runs/hindsight-highlights/`

## Service lifecycle

### Install the user unit
```bash
hindsight install-service
```

### Install the user command
```bash
hindsight install-command
```

### Start / stop / restart
```bash
hindsight up
hindsight down
hindsight restart
```

### Check status
```bash
hindsight status
```

### Logs
```bash
hindsight logs -f
hindsight logs
```

## Launcher wrapper

Start Hindsight directly with the repo launcher:

```bash
./scripts/run-api.sh
```

Start Hindsight without vLLM:

```bash
hindsight up
```

`hindsight up` follows the unit logs until it sees `Application startup complete`.

Start Hindsight and also launch a memory stack:

```bash
hindsight up --llm          # defaults to mem_gem_hsx
hindsight up --llm mem_gem_hsx
hindsight up --llm other_stack_name
```

Useful launch overrides live in:

- `env/hindsight.env`
- `env/hindsight.launch.env`
- `env/hindsight.local.env` (gitignored)

## Monitoring / dashboards

### Start or recreate Grafana LGTM monitoring
```bash
hindsight monitoring -d --force-recreate
```

Grafana: <http://localhost:3000>

### Verify dashboard metric plumbing
```bash
uv run python scripts/monitoring_doctor.py
```

Expected result: Prometheus target `http://127.0.0.1:8888/metrics` is `UP`, and `hindsight_llm_*` queries return non-zero series. If this fails, Grafana dashboards will be empty even though Hindsight traces may still appear.

### Important model-label note

For useful LLM comparison dashboards, start/restart Hindsight after the LLM backend on `127.0.0.1:8002` is healthy so `HINDSIGHT_API_LLM_MODEL=auto` resolves to the served model name instead of staying `auto`.

```bash
hindsight restart
uv run python scripts/monitoring_doctor.py
```

## Runtime evidence

### Monitor VRAM for the Hindsight API PID
```bash
uv run python scripts/monitor_hindsight_vram.py --pid <pid>
```

### Inspect the legacy unbounded run log
```bash
less /home/poop/runs/hindsight/api.log
```

## Memory write audits

Read-only workflow for checking latest retained facts and consolidation output. This is for write quality, not recall quality.

### Apply all bank configs and verify drift
```bash
uv run python scripts/push_banks.py --no-pull-after
```

`push_banks.py` now defaults to all local-agent banks and verifies all critical bank config after every push.

### Verify running bank config matches repo files without changing anything
```bash
uv run python scripts/check_bank_config_drift.py
```

### Audit all configured local-agent banks
```bash
uv run python scripts/memory_write_audit.py
```

### Audit one bank with more recent items
```bash
uv run python scripts/memory_write_audit.py --banks local-agent-user-profile --limit 10
```

### Filter memory text while auditing
```bash
uv run python scripts/memory_write_audit.py --banks local-agent-user-profile --q Seth --limit 20
```

### Save a markdown audit report
```bash
uv run python scripts/memory_write_audit.py \
  --output /home/poop/runs/hindsight-highlights/memory-write-audit-$(date -u +%Y%m%dT%H%M%SZ).md
```

The report includes compact bank stats, recent `world` facts, recent `experience` facts, recent `observation` consolidations, and mental model metadata if any models exist.

## Reflect / mental model planning

Current implementation plan:

```bash
less docs/reflect-mental-model-plan.md
```

Reflect and mental models are separate from automatic observation consolidation: `reflect_mission` configures explicit reflect calls, while mental models are saved/curated reflect responses that must be created through the mental-model API/client flow.

## Where to look for evidence

- **Service/runtime logs:** journald (`journalctl --user -u hindsight-api`)
- **Canary run evidence:** `~/runs/hindsight-highlights/`
- **Actual retained memories/facts:** Hindsight database / API, not journald
