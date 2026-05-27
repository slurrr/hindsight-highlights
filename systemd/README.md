# Hindsight systemd install notes

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

The system service sources `/home/poop/code/dev/hindsight-highlights/env/hindsight.env` and runs `hindsight-api` from `/home/poop/code/dev/hindsight-highlights/.venv`.

Create/update the dedicated venv:

```bash
cd /home/poop/code/dev/hindsight-highlights
uv venv --python python3.13 .venv
uv pip install --python .venv hindsight-api
```

Install/start the system service:

```bash
sudo cp systemd/hindsight-api.service /etc/systemd/system/hindsight-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now hindsight-api
```

Validate:

```bash
systemctl status postgresql
systemctl status hindsight-api
curl http://127.0.0.1:8888/health
```
