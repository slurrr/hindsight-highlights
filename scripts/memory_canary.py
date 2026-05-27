#!/usr/bin/env python3
"""Incremental canary tests for local Hindsight memory bank configs.

Non-destructive by default: writes to canary-* bank IDs and uses stable document IDs
so repeated runs upsert the same test documents instead of accumulating duplicates.

Examples:
  uv run python scripts/memory_canary.py --source-bank local-agent-framework-procedural
  uv run python scripts/memory_canary.py --source-bank local-agent-framework-procedural --suffix run-001
  uv run python scripts/memory_canary.py --all
"""

from __future__ import annotations

import argparse
import json
import os
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


@dataclass(frozen=True)
class MemoryExpectation:
    name: str
    text_terms: tuple[str, ...]
    required_tags: tuple[str, ...]
    forbidden_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    content: list[dict[str, str]]
    context: str
    query: str
    strict_tag: str
    expected_tag_prefixes: tuple[str, ...]
    expected_text_terms: tuple[str, ...]
    expectations: tuple[MemoryExpectation, ...]


SCENARIOS: dict[str, Scenario] = {
    "local-agent-user-profile": Scenario(
        content=[
            {"role": "user", "timestamp": "2026-05-27T09:00:00Z", "content": "Communication style preference: when you talk to me about planning work, use concise bullet summaries first, then a concrete checklist. Please avoid long narrative unless I ask."},
            {"role": "assistant", "timestamp": "2026-05-27T09:01:00Z", "content": "Understood. I will lead with bullets and checklists for planning work."},
            {"role": "user", "timestamp": "2026-05-27T09:02:00Z", "content": "My long-term goal is to turn the Atlas assistant idea into a local multi-agent product planning system."},
        ],
        context="Canary conversation with the main user-facing agent about durable user preferences and goals.",
        query="How should planning summaries be formatted for the user?",
        strict_tag="profile_area:communication_style",
        expected_tag_prefixes=("profile_area:", "durability:", "source_system:"),
        expected_text_terms=("bullet", "checklist", "planning"),
        expectations=(
            MemoryExpectation(
                name="communication style preference",
                text_terms=("bullet", "checklist"),
                required_tags=("profile_area:communication_style", "durability:stable", "source_system:main_agent"),
            ),
            MemoryExpectation(
                name="long-term Atlas goal",
                text_terms=("atlas", "multi-agent", "product planning"),
                required_tags=("profile_area:goals", "durability:stable", "source_system:main_agent"),
            ),
        ),
    ),
    "local-agent-product-strategy": Scenario(
        content=[
            {"role": "user", "timestamp": "2026-05-27T10:00:00Z", "content": "Product plan: Atlas should help one user turn ideas into high-level product plans, then convert accepted plans into implementation specs."},
            {"role": "assistant", "timestamp": "2026-05-27T10:01:00Z", "content": "Decision captured: the MVP scope is idea to plan to implementation spec, not autonomous deployment."},
            {"role": "user", "timestamp": "2026-05-27T10:02:00Z", "content": "Open question: how much scheduled assistant output should be shown to the user versus hidden behind summaries?"},
        ],
        context="Canary product planning session for Atlas MVP scope, decisions, and open questions.",
        query="What is the Atlas MVP product scope?",
        strict_tag="planning_artifact:product_plan",
        expected_tag_prefixes=("planning_artifact:", "product_area:", "status:"),
        expected_text_terms=("idea", "product", "implementation", "spec"),
        expectations=(
            MemoryExpectation(
                name="MVP product-plan fact",
                text_terms=("accepted plans", "implementation specification"),
                required_tags=("planning_artifact:product_plan", "product_area:scope"),
                forbidden_tags=("status:rejected",),
            ),
            MemoryExpectation(
                name="MVP accepted decision",
                text_terms=("mvp", "scope", "autonomous deployment"),
                required_tags=("planning_artifact:decision", "product_area:scope", "status:accepted"),
            ),
            MemoryExpectation(
                name="scheduled output open question",
                text_terms=("open question", "scheduled assistant", "summaries"),
                required_tags=("product_area:ux", "status:open_question"),
                forbidden_tags=("status:accepted",),
            ),
        ),
    ),
    "local-agent-implementation-work": Scenario(
        content=[
            {"role": "researcher", "timestamp": "2026-05-27T11:00:00Z", "content": "Research finding: Hindsight recall supports strict tag filtering with tags_match=any_strict, which we should use for memory shape isolation."},
            {"role": "builder", "timestamp": "2026-05-27T11:03:00Z", "content": "Implementation decision: canary tests will use separate canary banks and stable document IDs to avoid modifying production memory banks."},
            {"role": "tester", "timestamp": "2026-05-27T11:06:00Z", "content": "Test result: the framework-procedural bank must return procedure_type:rule memories when strict-filtered for rule recall."},
        ],
        context="Canary delegated implementation handoff with research, build, and test findings.",
        query="What did the tester say strict rule recall must return?",
        strict_tag="work_phase:test",
        expected_tag_prefixes=("work_phase:", "artifact_type:", "agent_role:"),
        expected_text_terms=("strict", "rule", "recall"),
        expectations=(
            MemoryExpectation(
                name="research strict filtering finding",
                text_terms=("strict", "tag", "filter"),
                required_tags=("work_phase:research", "artifact_type:finding", "agent_role:researcher"),
            ),
            MemoryExpectation(
                name="canary bank implementation decision",
                text_terms=("canary", "stable document", "production"),
                required_tags=("work_phase:build", "artifact_type:decision", "agent_role:builder"),
            ),
            MemoryExpectation(
                name="tester strict rule recall result",
                text_terms=("strict", "rule", "recall"),
                required_tags=("work_phase:test", "artifact_type:test_result", "agent_role:tester"),
            ),
        ),
    ),
    "local-agent-assistant-ops": Scenario(
        content=[
            {"role": "scheduled_assistant", "timestamp": "2026-05-27T12:00:00Z", "content": "Email triage summary: email messages from Vectorize about Hindsight releases should be included in the daily technical digest."},
            {"role": "scheduled_assistant", "timestamp": "2026-05-27T12:01:00Z", "content": "Email triage standing rule candidate: do not show raw newsletter email text to the user; summarize only important changes and follow-ups."},
            {"role": "scheduled_assistant", "timestamp": "2026-05-27T12:02:00Z", "content": "Email triage follow-up: ask the main agent to mention the Hindsight structured-output testing result if it fails."},
        ],
        context="Canary scheduled assistant output for email triage rules, summaries, and follow-ups.",
        query="What email triage standing rule should the main agent know?",
        strict_tag="assistant_domain:email",
        expected_tag_prefixes=("assistant_domain:", "ops_memory_type:", "attention_level:"),
        expected_text_terms=("summar", "hindsight", "digest"),
        expectations=(
            MemoryExpectation(
                name="email digest source rule",
                text_terms=("vectorize", "daily technical digest"),
                required_tags=("assistant_domain:email", "ops_memory_type:summary_output", "attention_level:informational"),
            ),
            MemoryExpectation(
                name="newsletter standing rule",
                text_terms=("newsletter", "summar", "raw"),
                required_tags=("assistant_domain:email", "ops_memory_type:standing_rule"),
            ),
            MemoryExpectation(
                name="structured output failure follow-up",
                text_terms=("structured-output", "testing", "fails"),
                required_tags=("ops_memory_type:follow_up", "attention_level:needs_review"),
            ),
        ),
    ),
    "local-agent-framework-procedural": Scenario(
        content=[
            {"role": "orchestrator", "timestamp": "2026-05-27T13:00:00Z", "content": "Framework rule: only the main_user_agent may communicate directly with the user; peer agents must return structured handoffs."},
            {"role": "orchestrator", "timestamp": "2026-05-27T13:01:00Z", "content": "Memory routing procedure: product decisions go to product-strategy, implementation handoffs go to implementation-work, and reusable operating rules go to framework-procedural."},
            {"role": "reviewer", "timestamp": "2026-05-27T13:02:00Z", "content": "Review checklist: before delegation, confirm the spec has acceptance criteria, open questions, and test expectations."},
        ],
        context="Canary framework procedure note for agent roles, user communication rules, memory routing, and review checklist.",
        query="Who is allowed to communicate directly with the user?",
        strict_tag="procedure_type:rule",
        expected_tag_prefixes=("procedure_area:", "procedure_type:", "agent_class:"),
        expected_text_terms=("main", "user", "communicat"),
        expectations=(
            MemoryExpectation(
                name="main user agent communication rule",
                text_terms=("main_user_agent", "communicate", "user"),
                required_tags=("procedure_area:user_communication", "procedure_type:rule", "agent_class:main_user_agent"),
                forbidden_tags=("procedure_type:procedure", "procedure_type:checklist"),
            ),
            MemoryExpectation(
                name="memory routing procedure",
                text_terms=("product-strategy", "implementation-work", "framework-procedural"),
                required_tags=("procedure_area:memory_routing", "procedure_type:procedure"),
                forbidden_tags=("procedure_type:rule", "procedure_type:checklist"),
            ),
            MemoryExpectation(
                name="review checklist",
                text_terms=("acceptance criteria", "open questions", "test expectations"),
                required_tags=("procedure_area:review_test", "procedure_type:checklist", "agent_class:reviewer"),
                forbidden_tags=("procedure_type:rule", "procedure_type:procedure"),
            ),
        ),
    ),
}


def base_url() -> str:
    load_dotenv(DEFAULT_ENV)
    host = os.getenv("HINDSIGHT_API_HOST", "127.0.0.1")
    port = os.getenv("HINDSIGHT_API_PORT", "8888")
    return f"http://{host}:{port}"


def request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{base_url()}{path}"
    r = httpx.request(method, url, timeout=120.0, **kwargs)
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:4000]
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.response.status_code}: {body}") from exc
    if r.content:
        return r.json()
    return {}


def q(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def load_bank_config(source_bank: str) -> dict[str, Any]:
    path = BANK_DIR / f"{source_bank}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    config = data.get("config")
    if not isinstance(config, dict):
        raise SystemExit(f"{path} missing config object")
    return config


def canary_bank_id(source_bank: str, suffix: str | None) -> str:
    return f"canary-{source_bank}" + (f"-{suffix}" if suffix else "")


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def allowed_label_tags(config: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Return (allowed key:value tags, controlled key prefixes) from bank entity_labels."""
    allowed: set[str] = set()
    prefixes: set[str] = set()
    for group in config.get("entity_labels") or []:
        if not isinstance(group, dict):
            continue
        key = group.get("key")
        if not isinstance(key, str) or not key:
            continue
        prefixes.add(f"{key}:")
        for value in group.get("values") or []:
            if isinstance(value, dict) and isinstance(value.get("value"), str):
                allowed.add(f"{key}:{value['value']}")
    return allowed, prefixes


def memory_matches(memory: dict[str, Any], terms: tuple[str, ...]) -> bool:
    text = str(memory.get("text", "")).lower()
    return all(term.lower() in text for term in terms)


def audit_structured_output(
    *,
    scenario: Scenario,
    memory_items: list[dict[str, Any]],
    tag_values: set[str | None],
    entity_names: list[Any],
    allowed_tags: set[str],
    controlled_prefixes: set[str],
) -> tuple[int, int]:
    """Audit whether extraction produced the expected structured labels per fact."""
    failures = 0
    warnings = 0
    print_section("structured output audit")

    controlled_tags = sorted(
        tag for tag in tag_values
        if isinstance(tag, str) and any(tag.startswith(prefix) for prefix in controlled_prefixes)
    )
    invalid_controlled_tags = [tag for tag in controlled_tags if allowed_tags and tag not in allowed_tags]
    if invalid_controlled_tags:
        print("FAIL invalid controlled label tag(s):", ", ".join(invalid_controlled_tags))
        failures += len(invalid_controlled_tags)
    else:
        print(f"controlled label tags valid: {len(controlled_tags)}")

    controlled_entities = [name for name in entity_names if isinstance(name, str) and any(name.startswith(prefix) for prefix in controlled_prefixes)]
    free_form_entities = [name for name in entity_names if isinstance(name, str) and name not in controlled_entities]
    print(f"controlled entities: {len(controlled_entities)}; free-form entities: {len(free_form_entities)}")
    if not controlled_entities:
        print("FAIL no controlled label entities found")
        failures += 1
    if len(free_form_entities) > max(10, len(controlled_entities) * 3):
        print("WARN free-form entities greatly outnumber controlled labels; graph may be noisy")
        warnings += 1

    for expected in scenario.expectations:
        matches = [memory for memory in memory_items if memory_matches(memory, expected.text_terms)]
        if not matches:
            print(f"FAIL {expected.name}: no memory matched text terms {expected.text_terms}")
            failures += 1
            continue
        # Prefer the match with the most required tags; this handles occasional merged facts.
        best = max(matches, key=lambda memory: len(set(memory.get("tags") or []) & set(expected.required_tags)))
        actual_tags = set(best.get("tags") or [])
        missing = [tag for tag in expected.required_tags if tag not in actual_tags]
        forbidden = [tag for tag in expected.forbidden_tags if tag in actual_tags]
        text_preview = str(best.get("text", "")).replace("\n", " ")[:220]
        if missing or forbidden:
            print(f"FAIL {expected.name}: {text_preview}")
            if missing:
                print("  missing required tag(s):", ", ".join(missing))
            if forbidden:
                print("  has forbidden tag(s):", ", ".join(forbidden))
            print("  actual tags:", ", ".join(sorted(actual_tags)))
            failures += 1
        else:
            print(f"PASS {expected.name}: required tags present")

    return failures, warnings


def run_one(source_bank: str, suffix: str | None, skip_apply: bool) -> int:
    if source_bank not in SCENARIOS:
        raise SystemExit(f"no scenario for {source_bank}")
    scenario = SCENARIOS[source_bank]
    bank_id = canary_bank_id(source_bank, suffix)
    config = load_bank_config(source_bank)
    allowed_tags, controlled_prefixes = allowed_label_tags(config)
    failures = 0
    warnings = 0

    print_section(f"{source_bank} -> {bank_id}")

    if not skip_apply:
        try:
            request("PUT", f"/v1/default/banks/{q(bank_id)}", json={"name": f"Canary for {source_bank}"})
        except RuntimeError as exc:
            print(f"WARN create bank failed: {exc}")
            warnings += 1
        request("PATCH", f"/v1/default/banks/{q(bank_id)}/config", json={"updates": config})
        print("applied config")

    document_id = f"canary:{source_bank}"
    payload = {
        "async": False,
        "items": [
            {
                "content": json.dumps(scenario.content, ensure_ascii=False),
                "context": scenario.context,
                "document_id": document_id,
                "timestamp": scenario.content[0]["timestamp"],
                "metadata": {"source_bank": source_bank, "canary": "true"},
                "tags": ["canary", f"source_bank:{source_bank}"],
                "observation_scopes": "combined",
            }
        ],
    }

    t0 = time.time()
    retain = request("POST", f"/v1/default/banks/{q(bank_id)}/memories", json=payload)
    print(f"retain completed in {time.time() - t0:.1f}s")
    print(json.dumps(retain, indent=2, sort_keys=True)[:1600])

    stats = request("GET", f"/v1/default/banks/{q(bank_id)}/stats")
    print("stats:", json.dumps(stats, sort_keys=True)[:1200])

    memories = request("GET", f"/v1/default/banks/{q(bank_id)}/memories/list", params={"limit": 25})
    memory_items = memories.get("items", [])
    print(f"memory units: {len(memory_items)} shown / total {memories.get('total')}")
    if not memory_items:
        print("FAIL no memory units extracted")
        failures += 1

    tags = request("GET", f"/v1/default/banks/{q(bank_id)}/tags", params={"limit": 200})
    tag_values = {item.get("tag") for item in tags.get("items", [])}
    print("tags:", ", ".join(sorted(t for t in tag_values if t)[:80]))
    for prefix in scenario.expected_tag_prefixes:
        if not any((tag or "").startswith(prefix) for tag in tag_values):
            print(f"WARN no extracted tag with prefix {prefix!r}")
            warnings += 1

    entities = request("GET", f"/v1/default/banks/{q(bank_id)}/entities", params={"limit": 50})
    entity_names = [item.get("canonical_name") for item in entities.get("items", [])]
    print("entities:", ", ".join(str(e) for e in entity_names[:50]))
    if len(entity_names) < 3:
        print("WARN very few entities extracted; graph may be underpopulated")
        warnings += 1

    audit_failures, audit_warnings = audit_structured_output(
        scenario=scenario,
        memory_items=memory_items,
        tag_values=tag_values,
        entity_names=entity_names,
        allowed_tags=allowed_tags,
        controlled_prefixes=controlled_prefixes,
    )
    failures += audit_failures
    warnings += audit_warnings

    recall_payload = {
        "query": scenario.query,
        "budget": "mid",
        "max_tokens": 2048,
        "include": {"entities": {"max_tokens": 500}},
        "trace": True,
    }
    recall = request("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=recall_payload)
    results = recall.get("results", [])
    print(f"recall results: {len(results)}")
    for item in results[:5]:
        print("-", item.get("text"), "tags=", item.get("tags"))
    joined = "\n".join(str(item.get("text", "")).lower() for item in results)
    for term in scenario.expected_text_terms:
        if term.lower() not in joined:
            print(f"WARN recall text did not include expected term fragment {term!r}")
            warnings += 1

    strict_payload = dict(recall_payload)
    strict_payload.update({"tags": [scenario.strict_tag], "tags_match": "any_strict"})
    strict = request("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=strict_payload)
    strict_results = strict.get("results", [])
    print(f"strict recall {scenario.strict_tag}: {len(strict_results)} result(s)")
    for item in strict_results[:5]:
        print("-", item.get("text"), "tags=", item.get("tags"))
    if not strict_results:
        print(f"FAIL strict tag recall returned no results for {scenario.strict_tag}")
        failures += 1
    elif any(scenario.strict_tag not in (item.get("tags") or []) for item in strict_results):
        print("FAIL strict recall returned at least one result missing the strict tag")
        failures += 1

    print(f"summary: failures={failures} warnings={warnings}")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-bank", choices=sorted(SCENARIOS))
    group.add_argument("--all", action="store_true")
    ap.add_argument("--suffix", help="Optional suffix for creating a fresh canary bank instead of reusing stable canary-* IDs")
    ap.add_argument("--skip-apply", action="store_true", help="Do not apply config before retaining; useful when testing a manually tuned canary bank")
    args = ap.parse_args()

    banks = sorted(SCENARIOS) if args.all else [args.source_bank]
    failures = 0
    for bank in banks:
        failures += run_one(bank, args.suffix, args.skip_apply)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
