#!/usr/bin/env python3
"""Concurrent Hindsight retain canary for realistic Pi session-end bursts.

Simulates several Pi/worker sessions ending at about the same time and retaining to
different memory banks. This is a backend stability/capacity check, not a replacement
for the structured per-bank quality audit in memory_canary.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Barrier
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from memory_canary import SCENARIOS  # noqa: E402

BANK_DIR = ROOT / "config" / "banks"
DEFAULT_ENV = ROOT / "env" / "hindsight.env"


def base_url() -> str:
    load_dotenv(DEFAULT_ENV)
    return f"http://{os.getenv('HINDSIGHT_API_HOST', '127.0.0.1')}:{os.getenv('HINDSIGHT_API_PORT', '8888')}"


def q(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def request(method: str, path: str, **kwargs: Any) -> Any:
    r = httpx.request(method, f"{base_url()}{path}", timeout=240.0, **kwargs)
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{method} {path} HTTP {exc.response.status_code}: {exc.response.text[:4000]}") from exc
    return r.json() if r.content else {}


def load_config(source_bank: str) -> dict[str, Any]:
    return json.loads((BANK_DIR / f"{source_bank}.json").read_text())["config"]


def apply_bank(source_bank: str, bank_id: str) -> None:
    request("PUT", f"/v1/default/banks/{q(bank_id)}", json={"name": f"Concurrent canary {source_bank}"})
    request("PATCH", f"/v1/default/banks/{q(bank_id)}/config", json={"updates": load_config(source_bank)})


def pi_transcript(source_bank: str) -> str:
    scenario = SCENARIOS[source_bank]
    lines = [f"Pi session-end concurrency canary for {source_bank}."]
    for i, turn in enumerate(scenario.content, 1):
        lines.append(f"[2026-05-27T19:{i:02d}:00.000Z] [{turn['role']}]: {turn['content']}")
    lines.append("[tool result: bash]: TRANSIENT_DEBUG_NOISE token_budget=777 temporary_probe_id=concurrency-noise")
    return "\n\n".join(lines)


def retain_one(source_bank: str, bank_id: str, barrier: Barrier) -> dict[str, Any]:
    scenario = SCENARIOS[source_bank]
    barrier.wait()
    payload = {
        "async": False,
        "items": [{
            "content": pi_transcript(source_bank),
            "context": f"Concurrent Pi session_shutdown retain canary for {source_bank}.",
            "document_id": f"pi-session:concurrency:{source_bank}",
            "update_mode": "replace",
            "timestamp": "2026-05-27T19:00:00Z",
            "metadata": {"canary": "pi-concurrency", "source_bank": source_bank, "event": "session_shutdown"},
            "tags": ["canary", "pi", "event:session_shutdown", "concurrency"],
            "observation_scopes": "combined",
        }],
    }
    t0 = time.time()
    result = request("POST", f"/v1/default/banks/{q(bank_id)}/memories", json=payload)
    return {"source_bank": source_bank, "bank_id": bank_id, "wall_seconds": round(time.time() - t0, 2), "usage": result.get("usage") or {}}


def recall_check(source_bank: str, bank_id: str) -> bool:
    scenario = SCENARIOS[source_bank]
    payload = {"query": scenario.query, "budget": "mid", "max_tokens": 1200, "tags": [scenario.strict_tag], "tags_match": "any_strict"}
    results = request("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=payload).get("results", [])
    if not results:
        return False
    joined = "\n".join(r.get("text", "") for r in results).lower()
    return any(term.lower() in joined for term in scenario.expected_text_terms)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default=str(int(time.time())))
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    source_banks = list(SCENARIOS)
    bank_ids = {b: f"canary-pi-concurrency-{b}-{args.suffix}" for b in source_banks}
    print("preparing banks...")
    for b in source_banks:
        apply_bank(b, bank_ids[b])

    failures = 0
    barrier = Barrier(len(source_banks))
    print(f"retaining concurrently: {len(source_banks)} banks")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(retain_one, b, bank_ids[b], barrier) for b in source_banks]
        for fut in as_completed(futs):
            try:
                r = fut.result()
                u = r["usage"]
                print(f"PASS retain {r['source_bank']}: wall={r['wall_seconds']}s input={u.get('input_tokens')} output={u.get('output_tokens')}")
            except Exception as exc:
                print(f"FAIL retain: {exc}")
                failures += 1

    for b in source_banks:
        try:
            ok = recall_check(b, bank_ids[b])
        except Exception as exc:
            print(f"FAIL recall {b}: {exc}")
            failures += 1
            continue
        print(("PASS" if ok else "FAIL"), "strict recall", b)
        failures += 0 if ok else 1

    print(f"summary: failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
