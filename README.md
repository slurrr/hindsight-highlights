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

## Quick control surface

```bash
hindsight up
hindsight up --llm
hindsight down
hindsight status
hindsight doctor
# foreground launch:
./scripts/run-api.sh
```

`hindsight up` follows logs until it sees `Application startup complete`.

The API is configured by files in this repo and targets the plan endpoints:

- Postgres: `127.0.0.1:5432`
- Hindsight API: `127.0.0.1:8888`
- vLLM: `127.0.0.1:8002`

Bank desired-state lives under `config/banks/`; service defaults stay in `env/hindsight.env` and launch defaults in `env/hindsight.launch.env` (`mem_gem_hsx` when `--llm` is used).
