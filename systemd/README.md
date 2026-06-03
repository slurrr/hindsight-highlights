# Hindsight user-service install notes

This repo owns Hindsight service config. Postgres is owned by Fedora system packages.

## Postgres

Use Fedora PostgreSQL packages and the standard `postgresql.service`; do not use pg0 or an embedded wrapper.

Expected endpoint: `127.0.0.1:5432`.

Fresh setup outline:

```bash
sudo dnf install postgresql-server postgresql-contrib pgvector
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
sudo -u postgres createuser hindsight
sudo -u postgres psql -c "ALTER USER hindsight WITH PASSWORD 'hindsight';"
sudo -u postgres createdb -O hindsight hindsight
sudo -u postgres psql -d hindsight -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

Set the `hindsight` role password to match `env/hindsight.env` before starting Hindsight.

## Hindsight API

The user service calls `scripts/run-api.sh`, which layers:

- `env/hindsight.env` for service/runtime defaults
- `env/hindsight.launch.env` for launch-profile defaults
- `env/hindsight.local.env` for optional local overrides

Create/update the dedicated venv:

```bash
cd /home/poop/code/dev/hindsight-highlights
uv venv --python python3.13 .venv
uv pip install --python .venv hindsight-api
```

Install the user unit:

```bash
hindsight install-service
```

Install the user command:

```bash
hindsight install-command
```

Start manually when you want it:

```bash
hindsight up
hindsight up --llm
hindsight status
hindsight logs -f
```

`hindsight up` follows logs until it sees `Application startup complete`.

The unit is intentionally not enabled at boot.
