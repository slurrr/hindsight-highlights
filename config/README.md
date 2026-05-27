# Hindsight playground

Editable control surface for the live Hindsight API served from this repo. Service launch/config stays in the repo root (`Makefile`, `env/`, `systemd/`, `scripts/`); bank templates and smoke scenarios stay here.

## Layout

- `templates/`: preferred Hindsight bank-template manifests (`version: "1"`) with bank config, mental models, and directives.
- `banks/`: legacy/simple memory-bank configuration JSON files. Keep only ad hoc per-bank experiments here.
- `examples/`: small retain/recall/reflect scenarios for smoke tests and regression checks.
- `../env/hindsight.env`: authoritative service-level config for the local API process.
- `../scripts/playground.py`: helper CLI that validates/imports templates and runs scenarios against `HINDSIGHT_API_HOST`/`HINDSIGHT_API_PORT`.
- `../scripts/run-api.sh`: foreground launcher for the live API.
- `../Makefile`: top-level control surface for setup, launch, status, logs, health, and template operations.

## Quick start

```bash
make setup
make doctor
make run

# in another shell, once the API is healthy:
make dry-run-template
make import-template
make run-scenario
```

Keep long-lived/service defaults in `env/hindsight.env`; keep bank-level experiments here.

## Template workflow

1. Edit `playground/templates/coding-assistant.json`.
2. Dry-run it against the live API before changing a bank.
3. Import it into a playground bank.
4. Run a scenario from `playground/examples/`.
5. Export the live bank back to a file when you want to snapshot server-side changes:

```bash
uv run python scripts/playground.py export-template playground-coding-assistant \
  --output playground/templates/exported-coding-assistant.json
```

The bank-template API is the preferred path because one manifest can keep bank config, directives, and mental models together.
