SHELL := /usr/bin/env bash

BANK ?= playground-coding-assistant
TEMPLATE ?= playground/templates/coding-assistant.json
SCENARIO ?= playground/examples/coding-smoke.json

.PHONY: help setup run install-service start stop restart status logs health doctor dry-run-template import-template export-template run-scenario files

help:
	@echo "Hindsight control surface"
	@echo ""
	@echo "Setup/service:"
	@echo "  make setup            uv sync into .venv"
	@echo "  make run              run hindsight-api in foreground from this repo"
	@echo "  make install-service  install user systemd unit from systemd/hindsight-api.service"
	@echo "  make start|stop|restart|status|logs"
	@echo ""
	@echo "Checks:"
	@echo "  make health           API /health via playground helper"
	@echo "  make doctor           check Postgres, Hindsight API, vLLM endpoints"
	@echo ""
	@echo "Playground:"
	@echo "  make dry-run-template [BANK=...] [TEMPLATE=...]"
	@echo "  make import-template  [BANK=...] [TEMPLATE=...]"
	@echo "  make export-template  [BANK=...]"
	@echo "  make run-scenario     [SCENARIO=...]"
	@echo "  make files            show editable control files"

setup:
	uv sync

run: setup
	./scripts/run-api.sh

install-service: setup
	./scripts/install-user-service.sh

start:
	systemctl --user start hindsight-api

stop:
	systemctl --user stop hindsight-api

restart:
	systemctl --user restart hindsight-api

status:
	systemctl --user status hindsight-api --no-pager

logs:
	journalctl --user -u hindsight-api -f

health:
	uv run python scripts/playground.py health

doctor:
	uv run python scripts/healthcheck.py

dry-run-template:
	uv run python scripts/playground.py dry-run-template $(BANK) $(TEMPLATE)

import-template:
	uv run python scripts/playground.py import-template $(BANK) $(TEMPLATE)

export-template:
	uv run python scripts/playground.py export-template $(BANK) --output playground/templates/exported-$(BANK).json

run-scenario:
	uv run python scripts/playground.py run-scenario $(SCENARIO)

files:
	@printf '%s\n' \
	  README.md \
	  docs/PLAN.md \
	  env/hindsight.env \
	  env/hindsight.local.env \
	  systemd/hindsight-api.service \
	  scripts/run-api.sh \
	  scripts/healthcheck.py \
	  scripts/playground.py \
	  playground/README.md \
	  playground/templates/coding-assistant.json \
	  playground/examples/coding-smoke.json
