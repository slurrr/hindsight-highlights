#!/usr/bin/env python3
"""Inspect recent Hindsight writes: facts, observations, stats, and mental models.

This is intentionally read-only. It is for tuning retain/consolidation quality, not recall.

Examples:
  uv run python scripts/memory_write_audit.py
  uv run python scripts/memory_write_audit.py --banks local-agent-user-profile --limit 15
  uv run python scripts/memory_write_audit.py --output /tmp/memory-audit.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import textwrap
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


def env_default_base_url() -> str:
    host = os.environ.get("HINDSIGHT_API_HOST", "127.0.0.1")
    port = os.environ.get("HINDSIGHT_API_PORT", "8888")
    return f"http://{host}:{port}"


def get_json(url: str, timeout: float = 30.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw) if raw.strip() else {}


def api_url(base: str, namespace: str, bank: str, suffix: str, params: dict[str, Any] | None = None) -> str:
    url = f"{base.rstrip('/')}/v1/{urllib.parse.quote(namespace, safe='')}/banks/{urllib.parse.quote(bank, safe='')}/{suffix.lstrip('/')}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean, doseq=True)
    return url


def list_memories(base: str, namespace: str, bank: str, *, fact_type: str | None, limit: int, q: str | None) -> tuple[list[dict[str, Any]], int | None]:
    data = get_json(api_url(base, namespace, bank, "memories/list", {"type": fact_type, "limit": limit, "q": q}))
    return list(data.get("items") or data.get("memories") or []), data.get("total")


def bank_stats(base: str, namespace: str, bank: str) -> dict[str, Any]:
    try:
        return get_json(api_url(base, namespace, bank, "stats"))
    except Exception as e:  # noqa: BLE001 - display diagnostic only
        return {"error": str(e)}


def mental_models(base: str, namespace: str, bank: str, limit: int) -> list[dict[str, Any]]:
    try:
        data = get_json(api_url(base, namespace, bank, "mental-models", {"detail": "metadata", "limit": limit}))
        return list(data.get("items") or data.get("mental_models") or data.get("models") or [])
    except Exception:
        return []


def short(value: Any, width: int = 900) -> str:
    if value is None:
        return ""
    s = str(value).replace("\r", " ").strip()
    s = "\n".join(line.rstrip() for line in s.splitlines())
    return textwrap.shorten(s, width=width, placeholder=" …") if len(s) > width else s


def fmt_item(item: dict[str, Any], idx: int) -> str:
    text = short(item.get("text") or item.get("content") or item.get("fact") or "", 1000)
    tags = item.get("tags") or []
    entities = item.get("entities") or ""
    when = item.get("mentioned_at") or item.get("date") or ""
    mid = item.get("id") or ""
    proof_count = item.get("proof_count")
    consolidated_at = item.get("consolidated_at")
    failed_at = item.get("consolidation_failed_at")
    lines = [f"{idx}. {text}"]
    meta = []
    if when:
        meta.append(f"mentioned={when}")
    if proof_count is not None:
        meta.append(f"proofs={proof_count}")
    if consolidated_at:
        meta.append(f"consolidated={consolidated_at}")
    if failed_at:
        meta.append(f"consolidation_failed={failed_at}")
    if tags:
        meta.append("tags=" + ", ".join(map(str, tags)))
    if entities:
        meta.append(f"entities={short(entities, 220)}")
    if mid:
        meta.append(f"id={mid}")
    if meta:
        lines.append("   " + " | ".join(meta))
    return "\n".join(lines)


def fmt_stats(stats: dict[str, Any]) -> str:
    if not stats:
        return "stats: unavailable"
    if "error" in stats:
        return f"stats error: {stats['error']}"
    keys = [
        "total_memories",
        "total_memory_units",
        "total_observations",
        "total_entities",
        "total_links",
        "unconsolidated_memories",
        "failed_consolidations",
    ]
    parts = [f"{k}={stats[k]}" for k in keys if k in stats]
    if not parts:
        # Compact fallback for unknown server schema.
        parts = [f"{k}={v}" for k, v in stats.items() if isinstance(v, (int, float, str, bool))][:10]
    return "stats: " + (", ".join(parts) if parts else "available")


def fmt_mental_model(model: dict[str, Any], idx: int) -> str:
    name = model.get("name") or model.get("title") or model.get("id") or f"mental-model-{idx}"
    tags = model.get("tags") or []
    updated = model.get("updated_at") or model.get("refreshed_at") or model.get("created_at") or ""
    mmid = model.get("id") or ""
    line = f"{idx}. {name}"
    bits = []
    if updated:
        bits.append(f"updated={updated}")
    if tags:
        bits.append("tags=" + ", ".join(map(str, tags)))
    if mmid:
        bits.append(f"id={mmid}")
    return line + ("\n   " + " | ".join(bits) if bits else "")


def render(args: argparse.Namespace) -> str:
    now = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    lines = [
        f"# Hindsight write audit ({now})",
        "",
        f"base_url: `{args.base_url.rstrip('/')}`",
        f"namespace: `{args.namespace}`",
        f"limit: `{args.limit}` per section",
    ]
    if args.q:
        lines.append(f"query filter: `{args.q}`")
    lines.append("")

    for bank in args.banks:
        lines.extend([f"## {bank}", "", fmt_stats(bank_stats(args.base_url, args.namespace, bank)), ""])

        for label, fact_type in [("Recent world facts", "world"), ("Recent experiences", "experience"), ("Recent observations", "observation")]:
            try:
                items, total = list_memories(args.base_url, args.namespace, bank, fact_type=fact_type, limit=args.limit, q=args.q)
            except Exception as e:  # noqa: BLE001
                lines.extend([f"### {label}", "", f"ERROR: {e}", ""])
                continue
            total_s = f" (total matching type: {total})" if total is not None else ""
            lines.extend([f"### {label}{total_s}", ""])
            if not items:
                lines.extend(["_none_", ""])
            else:
                for idx, item in enumerate(items, 1):
                    lines.append(fmt_item(item, idx))
                lines.append("")

        models = mental_models(args.base_url, args.namespace, bank, args.mental_models_limit)
        lines.extend(["### Mental models", ""])
        if not models:
            lines.extend(["_none or unavailable_", ""])
        else:
            for idx, model in enumerate(models, 1):
                lines.append(fmt_mental_model(model, idx))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default=env_default_base_url())
    ap.add_argument("--namespace", default="default")
    ap.add_argument("--banks", nargs="+", default=DEFAULT_BANKS)
    ap.add_argument("--limit", type=int, default=8, help="Recent items per fact/observation section")
    ap.add_argument("--mental-models-limit", type=int, default=5)
    ap.add_argument("--q", help="Optional full-text filter passed to memories/list")
    ap.add_argument("--output", "-o", help="Write markdown report to this path instead of stdout")
    args = ap.parse_args()

    report = render(args)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"wrote {path}")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
