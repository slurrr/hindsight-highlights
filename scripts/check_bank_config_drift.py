#!/usr/bin/env python3
"""Check Hindsight bank config drift between repo files and the running API.

Read-only. Exits non-zero if any selected config field differs or is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BANKS = [
    "local-agent-user-profile",
    "local-agent-product-strategy",
    "local-agent-framework-procedural",
    "local-agent-implementation-work",
    "local-agent-assistant-ops",
]

CHECK_FIELDS = [
    "retain_mission",
    "retain_extraction_mode",
    "retain_custom_instructions",
    "observations_mission",
    "reflect_mission",
    "disposition_skepticism",
    "disposition_literalism",
    "disposition_empathy",
    "enable_observations",
    "enable_auto_consolidation",
    "entity_labels",
    "entities_allow_free_form",
    "recall_budget_function",
    "recall_budget_fixed_low",
    "recall_budget_fixed_mid",
    "recall_budget_fixed_high",
]


def env_default_base_url() -> str:
    host = os.environ.get("HINDSIGHT_API_HOST", "127.0.0.1")
    port = os.environ.get("HINDSIGHT_API_PORT", "8888")
    return f"http://{host}:{port}"


def get_json(url: str, timeout: float = 30.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def normalize(value: Any) -> Any:
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize(value[k]) for k in sorted(value)}
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default=env_default_base_url())
    ap.add_argument("--namespace", default="default")
    ap.add_argument("--banks", nargs="+", default=DEFAULT_BANKS)
    ap.add_argument("--config-dir", default="config/banks")
    ap.add_argument("--field", action="append", dest="fields", help="Field to compare; can be repeated. Defaults to critical bank fields.")
    args = ap.parse_args()

    fields = args.fields or CHECK_FIELDS
    failed = False
    base = args.base_url.rstrip("/")
    config_dir = Path(args.config_dir)

    for bank in args.banks:
        local_path = config_dir / f"{bank}.json"
        print(f"\n## {bank}")
        if not local_path.exists():
            print(f"FAIL local config missing: {local_path}")
            failed = True
            continue

        local = json.loads(local_path.read_text(encoding="utf-8"))
        local_cfg = local.get("config") or {}
        url = f"{base}/v1/{urllib.parse.quote(args.namespace, safe='')}/banks/{urllib.parse.quote(bank, safe='')}/config"
        try:
            remote = get_json(url)
            remote_cfg = remote.get("config") or remote
        except Exception as e:  # noqa: BLE001
            print(f"FAIL API read failed: {e}")
            failed = True
            continue

        bank_ok = True
        for field in fields:
            lv = normalize(local_cfg.get(field))
            rv = normalize(remote_cfg.get(field))
            if lv != rv:
                bank_ok = False
                failed = True
                print(f"FAIL {field}: local={json.dumps(lv, ensure_ascii=False)[:220]} remote={json.dumps(rv, ensure_ascii=False)[:220]}")
        if bank_ok:
            print("OK critical config matches repo")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
