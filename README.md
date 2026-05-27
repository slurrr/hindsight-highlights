# hindsight-highlights

Local ops repo and control surface for running Hindsight as a first-class service (not embedded).

- Planning doc: `docs/PLAN.md`
- Service env: `env/hindsight.env`
- Optional local overrides/secrets: `env/hindsight.local.env` (gitignored)
- systemd units + install notes: `systemd/`
- Utility scripts: `scripts/`
- Backend config surface (banks/templates/examples): `config/`

## Quick control surface

```bash
make help
make setup
make doctor
make run              # foreground Hindsight API from this repo
# or:
make install-service
make start
make status
make logs
```

The API is configured by files in this repo and targets the plan endpoints:

- Postgres: `127.0.0.1:5432`
- Hindsight API: `127.0.0.1:8888`
- vLLM: `127.0.0.1:8002`

Bank desired-state lives under `config/banks/`; service-level defaults stay in `env/hindsight.env`.
