#!/usr/bin/env python3
"""Small Hindsight playground helper.

Examples:
  uv run python scripts/playground.py health
  uv run python scripts/playground.py apply-bank playground/banks/coding-assistant.json
  uv run python scripts/playground.py run-scenario playground/examples/coding-smoke.json
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from hindsight_client import Hindsight

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / "env" / "hindsight.env"


def load_service_env(env_file: Path = DEFAULT_ENV) -> str:
    load_dotenv(env_file)
    host = os.getenv("HINDSIGHT_API_HOST", "127.0.0.1")
    port = os.getenv("HINDSIGHT_API_PORT", "8888")
    return f"http://{host}:{port}"


def client() -> Hindsight:
    return Hindsight(base_url=load_service_env(), timeout=60.0)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def cmd_health(_: argparse.Namespace) -> None:
    response = httpx.get(f"{load_service_env()}/health", timeout=10.0)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2, sort_keys=True))


def cmd_apply_bank(args: argparse.Namespace) -> None:
    data = read_json(args.path)
    bank_id = data["bank_id"]
    name = data.get("name", bank_id)
    config = data.get("config", {})

    c = client()
    try:
        c.create_bank(bank_id=bank_id, name=name)
        print(f"created bank: {bank_id}")
    except Exception as exc:  # create is idempotent enough for playground use
        print(f"create skipped/failed for {bank_id}: {exc}")

    if config:
        allowed = set(inspect.signature(c.update_bank_config).parameters) - {"self", "bank_id"}
        skipped = sorted(set(config) - allowed)
        filtered = {k: v for k, v in config.items() if k in allowed}
        c.update_bank_config(bank_id, **filtered)
        print(f"applied config: {args.path}")
        if skipped:
            print(f"skipped unsupported client config keys: {', '.join(skipped)}")


def cmd_run_scenario(args: argparse.Namespace) -> None:
    data = read_json(args.path)
    bank_id = data["bank_id"]

    c = client()
    retain = c.retain(
        bank_id=bank_id,
        content=json.dumps(data["content"], ensure_ascii=False),
        context=data.get("context"),
        document_id=data.get("document_id"),
        retain_async=False,
    )
    print("retain:")
    print(retain)

    if query := data.get("recall_query"):
        recalled = c.recall(bank_id=bank_id, query=query, budget="mid", max_tokens=2048)
        print("\nrecall:")
        for item in recalled.results:
            print(f"- {item.text}")

    if query := data.get("reflect_query"):
        reflected = c.reflect(bank_id=bank_id, query=query, budget="low")
        print("\nreflect:")
        print(reflected.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hindsight local playground helper")
    sub = parser.add_subparsers(required=True)

    health = sub.add_parser("health", help="Check the configured Hindsight API")
    health.set_defaults(func=cmd_health)

    apply_bank = sub.add_parser("apply-bank", help="Create/update a bank from JSON config")
    apply_bank.add_argument("path", type=Path)
    apply_bank.set_defaults(func=cmd_apply_bank)

    run = sub.add_parser("run-scenario", help="Retain + recall/reflect from a scenario JSON file")
    run.add_argument("path", type=Path)
    run.set_defaults(func=cmd_run_scenario)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
