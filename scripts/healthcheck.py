#!/usr/bin/env python3
"""Hindsight local service dependency healthcheck."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "env" / "hindsight.env"


def tcp_check(host: str, port: int, timeout: float = 2.0) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "listening"
    except OSError as exc:
        return False, str(exc)


def http_check(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        response = httpx.get(url, timeout=timeout)
        return response.is_success, f"HTTP {response.status_code}"
    except httpx.HTTPError as exc:
        return False, str(exc)


def main() -> None:
    load_dotenv(ENV_FILE)

    api_host = os.getenv("HINDSIGHT_API_HOST", "127.0.0.1")
    api_port = int(os.getenv("HINDSIGHT_API_PORT", "8888"))
    llm_base = os.getenv("HINDSIGHT_API_LLM_BASE_URL", "http://127.0.0.1:8002/v1")
    db_url = os.getenv("HINDSIGHT_API_DATABASE_URL", "postgresql://127.0.0.1:5432/hindsight")

    parsed_db = urlparse(db_url)
    db_host = parsed_db.hostname or "127.0.0.1"
    db_port = parsed_db.port or 5432

    parsed_llm = urlparse(llm_base)
    llm_health = f"{parsed_llm.scheme}://{parsed_llm.netloc}/health"

    checks = {
        "postgres_tcp": {
            "target": f"{db_host}:{db_port}",
            "result": tcp_check(db_host, db_port),
        },
        "hindsight_api_health": {
            "target": f"http://{api_host}:{api_port}/health",
            "result": http_check(f"http://{api_host}:{api_port}/health"),
        },
        "vllm_health": {
            "target": llm_health,
            "result": http_check(llm_health),
        },
    }

    failed = False
    printable = {}
    for name, check in checks.items():
        ok, detail = check["result"]
        failed = failed or not ok
        printable[name] = {"ok": ok, "target": check["target"], "detail": detail}

    print(json.dumps(printable, indent=2, sort_keys=True))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
