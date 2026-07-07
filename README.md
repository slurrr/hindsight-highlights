# hindsight-highlights

Local ops repo and control surface for running Hindsight as a standalone local service.

- Planning doc: `docs/PLAN.md`
- Service env: `env/hindsight.env`
- Launch profile: `env/hindsight.launch.env`
- Command wrapper: `hindsight`
- Optional local overrides/secrets: `env/hindsight.local.env` (gitignored)
- systemd user unit + install notes: `systemd/`
- Utility scripts: `scripts/`
- Backend config surface (banks/templates/examples): `config/`
- Upstream Hindsight source checkout: `~/code/vendor/hindsight`

This repo is local ops/config glue. The Python packages are installed editable from the upstream source checkout via `tool.uv.sources` in `pyproject.toml`. Use `hindsight sync-env` instead of raw `uv sync`; it syncs upstream source packages, then restores this workstation's CUDA torch runtime without patching upstream.

## Quick control surface

```bash
hindsight up
hindsight up --llm
hindsight down
hindsight status
hindsight logs -f      # follow Hindsight user-service journal
hindsight llm-logs -f  # follow active agentmux LLM log
hindsight metrics      # cumulative LLM/operation metrics since service start
hindsight ops          # recent async retain/consolidation operations and durations
hindsight ui           # run upstream Control Plane UI on localhost:9999
hindsight monitoring   # start upstream Grafana LGTM stack/dashboards
hindsight dashboard    # print UI URL; use --open to launch browser
hindsight source-info  # confirm editable upstream source paths
hindsight sync-env     # uv sync + restore this machine's CUDA torch runtime
hindsight doctor
# foreground launch:
./scripts/run-api.sh
```

`hindsight up` follows logs until it sees `Application startup complete`.

## Monitoring / browser UI

OTEL tracing is already enabled in `env/hindsight.env`; you do not need to remember separate env vars. `hindsight monitoring` starts the upstream Grafana LGTM stack that receives traces and scrapes `/metrics`.

Browser UIs:

```bash
hindsight ui              # Hindsight Control Plane at http://localhost:9999
hindsight dashboard --open

hindsight monitoring      # Grafana LGTM at http://localhost:3000
hindsight dashboard --grafana --open
```

Use Hindsight Control Plane for the product UI. Use Grafana dashboards for metrics and Explore → Tempo for traces. If monitoring is not running, Prometheus metrics are still available at `http://127.0.0.1:8888/metrics`, but OTEL traces have nowhere useful to go.

The API is configured by files in this repo and targets the plan endpoints:

- Postgres: `127.0.0.1:5432`
- Hindsight API: `127.0.0.1:8888`
- LLM slot (OpenAI-compatible vLLM/llama.cpp/etc.): `127.0.0.1:8002`

Bank desired-state lives under `config/banks/`; service defaults stay in `env/hindsight.env` and launch defaults in `env/hindsight.launch.env` (`mem_gem_hsx` when `--llm` is used).
