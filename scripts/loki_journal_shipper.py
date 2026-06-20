#!/usr/bin/env python3
"""Ship Hindsight user-service journald logs to local Loki.

Small host-side helper because the current promtail image is not built with
journald support. Intended to be started by scripts/run-monitoring.sh.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any


def ts_ns(entry: dict[str, Any]) -> str:
    raw = entry.get("__REALTIME_TIMESTAMP")
    try:
        return str(int(raw) * 1000)  # journald usec -> nsec
    except Exception:
        return str(int(datetime.now(timezone.utc).timestamp() * 1_000_000_000))


def push_loki(url: str, labels: dict[str, str], timestamp_ns: str, line: str) -> None:
    body = json.dumps({"streams": [{"stream": labels, "values": [[timestamp_ns, line]]}]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loki-url", default="http://127.0.0.1:3100/loki/api/v1/push")
    ap.add_argument("--unit", default="hindsight-api.service")
    ap.add_argument("--since", default="now", help="journalctl --since value; use '1 hour ago' for backfill")
    args = ap.parse_args()

    cmd = ["journalctl", "--user", "-u", args.unit, "-o", "json", "--since", args.since, "-n", "200", "-f"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    assert proc.stdout is not None

    labels = {"job": "hindsight-journal", "unit": args.unit, "syslog_identifier": "hindsight-api"}
    pending: list[tuple[str, str]] = []
    last_error_at = 0.0

    try:
        for raw in proc.stdout:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            msg = str(entry.get("MESSAGE") or "")
            if not msg:
                continue
            pending.append((ts_ns(entry), msg))

            next_pending: list[tuple[str, str]] = []
            for stamp, line in pending[-1000:]:
                try:
                    push_loki(args.loki_url, labels, stamp, line)
                except Exception as exc:  # noqa: BLE001
                    next_pending.append((stamp, line))
                    now = time.time()
                    if now - last_error_at > 30:
                        print(f"loki_journal_shipper: Loki push failed: {exc}", flush=True)
                        last_error_at = now
                    break
            pending = next_pending
    finally:
        proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
