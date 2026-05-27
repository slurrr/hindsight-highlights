#!/usr/bin/env python3
"""Compare Hindsight replace vs append for a growing long-session transcript.

This intentionally uses canary-* banks only. It applies the selected source bank config,
then runs the same evolving transcript through two banks:

- replace: re-retain the full transcript after every step with update_mode=replace
- append: retain the first step, then retain only new turns with update_mode=append

The final audit checks fact density, duplicate-ish facts, required labels, strict recall,
and whether noisy tool/debug chatter became stored facts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BANK_DIR = ROOT / "config" / "banks"
DEFAULT_ENV = ROOT / "env" / "hindsight.env"
SOURCE_BANK = "local-agent-product-strategy"


@dataclass(frozen=True)
class ExpectedFact:
    name: str
    text_terms: tuple[str, ...]
    required_tags: tuple[str, ...]
    forbidden_tags: tuple[str, ...] = ()


STEPS: list[list[dict[str, str]]] = [
    [
        {"role": "user", "timestamp": "2026-05-27T14:00:00Z", "content": "Product plan: Atlas should help one user turn rough ideas into high-level product plans, then convert accepted plans into implementation specs."},
        {"role": "assistant", "timestamp": "2026-05-27T14:01:00Z", "content": "I will keep the plan focused on idea capture, plan shaping, and spec generation."},
    ],
    [
        {"role": "user", "timestamp": "2026-05-27T14:05:00Z", "content": "Decision: the MVP scope excludes autonomous deployment and direct production changes. It should stop at ticket-ready specs and delegated local implementation work."},
        {"role": "assistant", "timestamp": "2026-05-27T14:06:00Z", "content": "Accepted: no autonomous deployment in the MVP; specs and delegated work are in scope."},
    ],
    [
        {"role": "tool", "timestamp": "2026-05-27T14:08:00Z", "content": "NOISE DEBUG LOG: retry=0 cache_hit=true token_budget=123456 stacktrace_marker=not-a-product-fact temporary_probe_id=abc123"},
        {"role": "assistant", "timestamp": "2026-05-27T14:09:00Z", "content": "Ignoring transient debug chatter. Open question: how much scheduled assistant output should be shown directly to the user versus hidden behind summaries?"},
    ],
    [
        {"role": "user", "timestamp": "2026-05-27T14:15:00Z", "content": "Decision: scheduled assistant output should be summarized in a daily digest, but urgent or approval-needed items should be surfaced immediately by the main user-facing agent."},
        {"role": "assistant", "timestamp": "2026-05-27T14:16:00Z", "content": "Accepted UX rule: daily digest by default, immediate surfacing for urgent or approval-needed items."},
    ],
    [
        {"role": "user", "timestamp": "2026-05-27T14:25:00Z", "content": "Implementation spec: the memory test harness must compare replace versus append, count facts, audit controlled tags, check strict recall, and flag debug-log fact spam."},
        {"role": "assistant", "timestamp": "2026-05-27T14:26:00Z", "content": "Acceptance criteria: both modes should produce product-plan, decision, UX, and implementation-spec memories without duplicate spam or debug-log memories."},
    ],
]

EXPECTATIONS = (
    ExpectedFact(
        name="Atlas product plan",
        text_terms=("rough ideas", "product plans", "implementation spec"),
        required_tags=("planning_artifact:product_plan", "product_area:scope"),
    ),
    ExpectedFact(
        name="MVP scope decision",
        text_terms=("mvp", "excludes", "autonomous deployment"),
        required_tags=("planning_artifact:decision", "product_area:scope", "status:accepted"),
    ),
    ExpectedFact(
        name="scheduled assistant UX decision",
        text_terms=("daily digest", "urgent", "approval"),
        required_tags=("planning_artifact:decision", "product_area:ux", "status:accepted"),
        forbidden_tags=("status:open_question",),
    ),
    ExpectedFact(
        name="memory harness implementation spec",
        text_terms=("compare", "replace", "append"),
        required_tags=("planning_artifact:implementation_spec",),
    ),
)

NOISE_TERMS = ("debug log", "token_budget", "stacktrace_marker", "temporary_probe_id")


def base_url() -> str:
    load_dotenv(DEFAULT_ENV)
    return f"http://{os.getenv('HINDSIGHT_API_HOST', '127.0.0.1')}:{os.getenv('HINDSIGHT_API_PORT', '8888')}"


def request(method: str, path: str, **kwargs: Any) -> Any:
    r = httpx.request(method, f"{base_url()}{path}", timeout=180.0, **kwargs)
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{method} {path} HTTP {exc.response.status_code}: {exc.response.text[:4000]}") from exc
    return r.json() if r.content else {}


def q(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def load_config() -> dict[str, Any]:
    return json.loads((BANK_DIR / f"{SOURCE_BANK}.json").read_text(encoding="utf-8"))["config"]


def allowed_label_tags(config: dict[str, Any]) -> tuple[set[str], set[str]]:
    allowed: set[str] = set()
    prefixes: set[str] = set()
    for group in config.get("entity_labels") or []:
        if not isinstance(group, dict) or not isinstance(group.get("key"), str):
            continue
        key = group["key"]
        prefixes.add(f"{key}:")
        for value in group.get("values") or []:
            if isinstance(value, dict) and isinstance(value.get("value"), str):
                allowed.add(f"{key}:{value['value']}")
    return allowed, prefixes


def normalize_text(text: str) -> str:
    # Drop Hindsight's generated annotation suffixes so "same fact | When..." counts as duplicate-ish.
    text = text.split(" | ", 1)[0]
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def matching_memory(memories: list[dict[str, Any]], terms: tuple[str, ...]) -> dict[str, Any] | None:
    matches = [m for m in memories if all(t.lower() in str(m.get("text", "")).lower() for t in terms)]
    if not matches:
        return None
    return max(matches, key=lambda m: len(str(m.get("text", ""))))


def apply_bank(bank_id: str, config: dict[str, Any]) -> None:
    request("PUT", f"/v1/default/banks/{q(bank_id)}", json={"name": f"Session evolution canary {bank_id}"})
    request("PATCH", f"/v1/default/banks/{q(bank_id)}/config", json={"updates": config})


def format_transcript(turns: list[dict[str, str]]) -> str:
    # Append concatenates document text, so use a line-oriented transcript format that remains valid as it grows.
    return "\n".join(f"[{turn['timestamp']}] {turn['role']}: {turn['content']}" for turn in turns)


def retain_step(bank_id: str, mode: str, step_index: int, all_turns: list[dict[str, str]], new_turns: list[dict[str, str]]) -> dict[str, Any]:
    document_id = f"session-evolution:{mode}"
    if mode == "replace" or step_index == 0:
        content_turns = all_turns
        update_mode = "replace"
    else:
        content_turns = new_turns
        update_mode = "append"

    payload = {
        "async": False,
        "items": [{
            "content": format_transcript(content_turns),
            "context": f"Session evolution canary for {SOURCE_BANK}; mode={mode}; step={step_index + 1}",
            "document_id": document_id,
            "timestamp": content_turns[0]["timestamp"],
            "metadata": {"canary": "session-evolution", "mode": mode, "step": str(step_index + 1)},
            "tags": ["canary", "session:evolution", f"mode:{mode}"],
            "update_mode": update_mode,
            "observation_scopes": "combined",
        }],
    }
    t0 = time.time()
    result = request("POST", f"/v1/default/banks/{q(bank_id)}/memories", json=payload)
    result["wall_seconds"] = round(time.time() - t0, 2)
    result["sent_turns"] = len(content_turns)
    result["update_mode"] = update_mode
    return result


def recall(bank_id: str, query: str, tags: list[str] | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"query": query, "budget": "mid", "max_tokens": 2048, "include": {"entities": {"max_tokens": 500}}}
    if tags:
        payload.update({"tags": tags, "tags_match": "any_strict"})
    return request("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=payload).get("results", [])


def audit_bank(bank_id: str, mode: str, config: dict[str, Any], retain_results: list[dict[str, Any]]) -> int:
    failures = 0
    allowed_tags, prefixes = allowed_label_tags(config)
    memories = request("GET", f"/v1/default/banks/{q(bank_id)}/memories/list", params={"limit": 100}).get("items", [])
    tags = {item.get("tag") for item in request("GET", f"/v1/default/banks/{q(bank_id)}/tags", params={"limit": 200}).get("items", [])}
    entities = [item.get("canonical_name") for item in request("GET", f"/v1/default/banks/{q(bank_id)}/entities", params={"limit": 100}).get("items", [])]

    print(f"\n== final audit: {mode} ({bank_id}) ==")
    print(f"memory units: {len(memories)}")
    print("retain steps:")
    for i, result in enumerate(retain_results, 1):
        usage = result.get("usage") or {}
        print(f"  step {i}: mode={result['update_mode']} sent_turns={result['sent_turns']} wall={result['wall_seconds']}s input={usage.get('input_tokens')} output={usage.get('output_tokens')}")

    invalid = sorted(t for t in tags if isinstance(t, str) and any(t.startswith(p) for p in prefixes) and t not in allowed_tags)
    if invalid:
        print("FAIL invalid controlled tags:", ", ".join(invalid))
        failures += 1
    controlled_entities = [e for e in entities if isinstance(e, str) and any(e.startswith(p) for p in prefixes)]
    free_entities = [e for e in entities if isinstance(e, str) and e not in controlled_entities]
    print(f"controlled entities={len(controlled_entities)} free_form_entities={len(free_entities)}")

    normalized = [normalize_text(str(m.get("text", ""))) for m in memories]
    duplicateish = len(normalized) - len(set(normalized))
    if duplicateish:
        print(f"FAIL duplicate exact-normalized facts: {duplicateish}")
        failures += 1

    noisy = [m for m in memories if any(term in str(m.get("text", "")).lower() for term in NOISE_TERMS)]
    if noisy:
        print("FAIL noise/debug chatter became facts:")
        for m in noisy:
            print(" -", m.get("text"), "tags=", m.get("tags"))
        failures += 1

    for expected in EXPECTATIONS:
        match = matching_memory(memories, expected.text_terms)
        if not match:
            print(f"FAIL {expected.name}: no matching memory for terms {expected.text_terms}")
            failures += 1
            continue
        actual = set(match.get("tags") or [])
        missing = [t for t in expected.required_tags if t not in actual]
        forbidden = [t for t in expected.forbidden_tags if t in actual]
        if missing or forbidden:
            print(f"FAIL {expected.name}: {match.get('text')}")
            if missing:
                print("  missing:", ", ".join(missing))
            if forbidden:
                print("  forbidden:", ", ".join(forbidden))
            print("  tags:", ", ".join(sorted(actual)))
            failures += 1
        else:
            print(f"PASS {expected.name}")

    strict_plan = recall(bank_id, "What is the Atlas product plan?", ["planning_artifact:product_plan"])
    strict_spec = recall(bank_id, "What does the memory test harness implementation spec require?", ["planning_artifact:implementation_spec"])
    print(f"strict product_plan recall: {len(strict_plan)}")
    print(f"strict implementation_spec recall: {len(strict_spec)}")
    if not strict_plan or not strict_spec:
        failures += 1

    print(f"summary {mode}: failures={failures}")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default=str(int(time.time())), help="Suffix for canary bank IDs")
    args = ap.parse_args()

    config = load_config()
    failures = 0
    for mode in ("replace", "append"):
        bank_id = f"canary-session-evolution-{mode}-{args.suffix}"
        apply_bank(bank_id, config)
        all_turns: list[dict[str, str]] = []
        retain_results: list[dict[str, Any]] = []
        print(f"\n== running {mode}: {bank_id} ==")
        for i, step in enumerate(STEPS):
            all_turns.extend(step)
            result = retain_step(bank_id, mode, i, all_turns, step)
            retain_results.append(result)
            usage = result.get("usage") or {}
            print(f"step {i+1}: {result['update_mode']} sent_turns={result['sent_turns']} wall={result['wall_seconds']}s input={usage.get('input_tokens')} output={usage.get('output_tokens')}")
        failures += audit_bank(bank_id, mode, config, retain_results)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
