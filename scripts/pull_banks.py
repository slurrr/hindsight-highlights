#!/usr/bin/env python3
"""Export bank config from a running Hindsight API into repo files.

This is the "editable status script" for bank config.

Usage:
  uv run python scripts/pull_banks.py --banks pi-ghosty-personal pi-ghosty-procedural

Defaults:
- base URL derived from env/hindsight.env (HINDSIGHT_API_HOST/HINDSIGHT_API_PORT)
- output dir: config/banks/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def _env_default_base_url() -> str:
    host = os.environ.get("HINDSIGHT_API_HOST", "127.0.0.1")
    port = os.environ.get("HINDSIGHT_API_PORT", "8888")
    return f"http://{host}:{port}"


def _get_json(url: str, timeout: float = 30.0) -> object:
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=_env_default_base_url())
    ap.add_argument("--banks", nargs="+", required=True)
    ap.add_argument("--out-dir", default="config/banks")
    ap.add_argument("--pretty", action="store_true", default=True)
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_index: dict[str, str] = {}

    for bank_id in args.banks:
        bank_q = urllib.parse.quote(bank_id, safe="")
        url = f"{base}/v1/default/banks/{bank_q}/config"
        data = _get_json(url)

        # Preserve the shape we want to reason about locally.
        # Keep raw server response fields we care about.
        payload = {
            "bank_id": data.get("bank_id") if isinstance(data, dict) else bank_id,
            "config": data.get("config") if isinstance(data, dict) else data,
        }
        if isinstance(data, dict) and "overrides" in data:
            payload["overrides"] = data.get("overrides")

        path = out_dir / f"{bank_id}.json"
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n" if args.pretty else json.dumps(payload) + "\n"
        path.write_text(text, encoding="utf-8")
        out_index[bank_id] = str(path)
        print(f"pulled {bank_id} -> {path}")

    # Write a small index for convenience.
    (out_dir / "_index.json").write_text(
        json.dumps({"base_url": base, "banks": out_index}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
