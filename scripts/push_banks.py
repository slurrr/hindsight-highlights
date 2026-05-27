#!/usr/bin/env python3
"""Apply repo bank config files to a running Hindsight API.

This is intentionally simple:
- read config/banks/<bank>.json
- PATCH /v1/default/banks/<bank>/config with {updates: <file.config>}
- optionally pull immediately after to normalize/snapshot server-side defaults

Usage:
  # default: push then pull (self-normalize)
  uv run python scripts/push_banks.py --banks pi-ghosty-personal pi-ghosty-procedural

  # disable self-normalization:
  uv run python scripts/push_banks.py --banks pi-ghosty-personal pi-ghosty-procedural --no-pull-after
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


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _patch_json(url: str, payload: object, timeout: float = 60.0) -> object:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="PATCH",
        headers={"content-type": "application/json", "accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=_env_default_base_url())
    ap.add_argument("--banks", nargs="+", required=True)
    ap.add_argument("--in-dir", default="config/banks")
    ap.add_argument(
        "--no-pull-after",
        action="store_true",
        help="Disable post-push pull (default behavior is to pull to snapshot server-normalized config)",
    )
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    in_dir = Path(args.in_dir)

    for bank_id in args.banks:
        path = in_dir / f"{bank_id}.json"
        if not path.exists():
            raise SystemExit(f"missing bank file: {path}")
        data = _read_json(path)
        if not isinstance(data, dict):
            raise SystemExit(f"invalid JSON shape in {path}")

        updates = data.get("config")
        if not isinstance(updates, dict):
            raise SystemExit(f"{path} missing object field: config")

        bank_q = urllib.parse.quote(bank_id, safe="")
        url = f"{base}/v1/default/banks/{bank_q}/config"
        _patch_json(url, {"updates": updates})
        print(f"pushed {bank_id} <- {path}")

    if not args.no_pull_after:
        
        # Import lazily to avoid circular dependency; just invoke pull script.
        import subprocess

        subprocess.check_call(
            [sys.executable, str(Path(__file__).parent / "pull_banks.py"), "--base-url", base, "--banks", *args.banks]
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
