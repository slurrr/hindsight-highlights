# Hindsight playground

Organized scratch space for customizing Hindsight without mixing experimental bank settings into the service env.

## Layout

- `banks/`: versioned memory-bank configuration JSON files. Edit these first while tuning missions, dispositions, labels, and consolidation behavior.
- `examples/`: small retain/recall/reflect scenarios for smoke tests and regression checks.
- `../env/hindsight.env`: authoritative service-level config for the local API process.
- `../scripts/playground.py`: helper CLI that applies bank config and runs scenarios against `HINDSIGHT_API_HOST`/`HINDSIGHT_API_PORT`.

## Quick start

```bash
uv sync
uv run python scripts/playground.py health
uv run python scripts/playground.py apply-bank playground/banks/coding-assistant.json
uv run python scripts/playground.py run-scenario playground/examples/coding-smoke.json
```

Keep long-lived/service defaults in `env/hindsight.env`; keep bank-level experiments here.
