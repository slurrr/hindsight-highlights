#!/usr/bin/env python3
"""Small local observability helpers for the standalone Hindsight service."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

BASE = "http://127.0.0.1:8888"
DB_URL = os.environ.get("HINDSIGHT_API_DATABASE_URL", "postgresql://hindsight:hindsight@127.0.0.1:5432/hindsight")


def get(path: str, timeout: float = 20.0) -> str:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def get_json(path: str, timeout: float = 20.0) -> Any:
    return json.loads(get(path, timeout=timeout))


def parse_labels(s: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r'(\w+)="((?:[^"\\]|\\.)*)"', s):
        out[m.group(1)] = m.group(2).replace('\\"', '"')
    return out


def metric_rows(prefixes: tuple[str, ...]) -> list[tuple[str, dict[str, str], float]]:
    rows = []
    for line in get("/metrics", timeout=30).splitlines():
        if not line or line.startswith("#"):
            continue
        name_part, _, value_part = line.partition(" ")
        if not any(name_part.startswith(p) for p in prefixes):
            continue
        if "{" in name_part:
            name, labels_raw = name_part.split("{", 1)
            labels_raw = labels_raw.rstrip("}")
            labels = parse_labels(labels_raw)
        else:
            name, labels = name_part, {}
        try:
            value = float(value_part.strip())
        except ValueError:
            continue
        rows.append((name, labels, value))
    return rows


def metrics(_: argparse.Namespace) -> int:
    rows = metric_rows(("hindsight_llm_", "hindsight_operation_"))
    sums: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
    for name, labels, value in rows:
        if name.endswith(("_count", "_sum", "_total")):
            key_labels = tuple(sorted((k, v) for k, v in labels.items() if k not in {"le", "token_bucket"}))
            sums[(name, key_labels)] = sums.get((name, key_labels), 0.0) + value

    print("LLM calls since service start:")
    for (name, label_items), value in sorted(sums.items()):
        if name != "hindsight_llm_calls_total":
            continue
        labels = dict(label_items)
        dur = sums.get(("hindsight_llm_duration_seconds_sum", label_items), 0.0)
        in_tok = sums.get(("hindsight_llm_tokens_input_tokens_total", label_items), 0.0)
        out_tok = sums.get(("hindsight_llm_tokens_output_tokens_total", label_items), 0.0)
        count = value or 0.0
        avg = dur / count if count else 0.0
        out_tps = out_tok / dur if dur else 0.0
        print(
            f"  {labels.get('scope','?'):18} {labels.get('model','?'):24} success={labels.get('success','?'):5} "
            f"count={count:.0f} avg={avg:.2f}s out_tps={out_tps:.2f} input={in_tok:.0f} output={out_tok:.0f} total={dur:.1f}s"
        )

    print("\nOperations since service start:")
    for (name, label_items), count in sorted(sums.items()):
        if name != "hindsight_operation_duration_seconds_count":
            continue
        labels = dict(label_items)
        dur = sums.get(("hindsight_operation_duration_seconds_sum", label_items), 0.0)
        avg = dur / count if count else 0.0
        bank = labels.get("bank_id", "-")
        print(f"  {labels.get('operation','?'):10} bank={bank:36} source={labels.get('source','?'):8} success={labels.get('success','?'):5} count={count:.0f} avg={avg:.2f}s")
    return 0


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_age(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds/60:.1f}m"
    return f"{seconds/3600:.1f}h"


def ops_db(args: argparse.Namespace) -> bool:
    try:
        import psycopg2
    except Exception:
        return False
    try:
        conn = psycopg2.connect(DB_URL)
    except Exception as exc:
        print(f"warn: DB operation query unavailable: {exc}; falling back to API", file=sys.stderr)
        return False
    bank_filter = ""
    params: list[Any] = []
    if args.bank:
        bank_filter = "AND bank_id = ANY(%s)"
        params.append(args.bank)
    params.append(args.limit)
    sql = f"""
        SELECT bank_id, operation_type, status, created_at, claimed_at, completed_at,
               updated_at, retry_count, error_message, result_metadata
        FROM async_operations
        WHERE true {bank_filter}
        ORDER BY COALESCE(completed_at, updated_at, created_at) DESC
        LIMIT %s
    """
    with conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    for bank_id, op_type, status, created, claimed, completed, updated, retry_count, error, metadata in rows:
        queue = (claimed - created).total_seconds() if claimed and created else None
        run = ((completed or updated) - claimed).total_seconds() if claimed and (completed or updated) else None
        total = ((completed or updated) - created).total_seconds() if created and (completed or updated) else None
        err = f" error={error}" if error else ""
        print(
            f"{(completed or updated).isoformat()} {bank_id[:34]:34} {op_type:18} {status:10} "
            f"queue={fmt_age(queue):>6} run={fmt_age(run):>6} total={fmt_age(total):>6} retries={retry_count}{err}"
        )
    return True


def ops(args: argparse.Namespace) -> int:
    if ops_db(args):
        return 0
    banks = get_json("/v1/default/banks").get("banks", [])
    bank_ids = [b["bank_id"] for b in banks]
    wanted = set(args.bank or bank_ids)
    rows: list[dict[str, Any]] = []
    for bank_id in bank_ids:
        if bank_id not in wanted:
            continue
        q = urllib.parse.urlencode({"limit": args.limit, "exclude_parents": str(args.exclude_parents).lower()})
        try:
            payload = get_json(f"/v1/default/banks/{urllib.parse.quote(bank_id, safe='')}/operations?{q}")
        except Exception as exc:
            print(f"warn: failed operations for {bank_id}: {exc}", file=sys.stderr)
            continue
        for op in payload.get("operations", []):
            op["bank_id"] = bank_id
            rows.append(op)
    rows.sort(key=lambda o: o.get("updated_at") or o.get("created_at") or "", reverse=True)
    for op in rows[: args.limit]:
        created = parse_dt(op.get("created_at"))
        updated = parse_dt(op.get("updated_at"))
        dur = (updated - created).total_seconds() if created and updated else None
        progress = op.get("progress") or {}
        prog = ""
        if progress:
            prog = f" {progress.get('stage','')} {progress.get('processed','?')}/{progress.get('total','?')}"
        err = f" error={op.get('error_message')}" if op.get("error_message") else ""
        print(f"{op.get('updated_at','?')} {op['bank_id'][:34]:34} {op.get('task_type','?'):18} {op.get('status','?'):10} dur={fmt_age(dur):>6}{prog}{err}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("metrics").set_defaults(func=metrics)
    ops_p = sub.add_parser("ops")
    ops_p.add_argument("--bank", action="append", help="Bank id to include; repeatable. Default: all banks")
    ops_p.add_argument("--limit", type=int, default=20)
    ops_p.add_argument("--exclude-parents", action="store_true", default=True)
    ops_p.set_defaults(func=ops)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
