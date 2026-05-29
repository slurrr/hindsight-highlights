#!/usr/bin/env python3
"""Narrow Hindsight consolidation/observation canary.

Focuses on structure, not broad theory:
- Uses a canary bank cloned from local-agent-implementation-work.
- Retains several Pi-shaped session-end documents with overlapping facts.
- Relies on enable_auto_consolidation from the bank config.
- Polls operations for completed consolidation.
- Verifies observations are stored as fact_type=observation and carry useful tags/entities/recall structure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BANK_DIR = ROOT / "config" / "banks"
DEFAULT_ENV = ROOT / "env" / "hindsight.env"
SOURCE_BANK = "local-agent-implementation-work"

EXPECTED_CONTROLLED_TAGS = {
    "work_phase:build",
    "artifact_type:decision",
    "work_status:done",
    "agent_role:orchestrator",
}
REQUIRED_TERM_GROUPS = (
    ("session_shutdown", "session shutdown"),
    ("replace", "replacing"),
    ("pi-session",),
)

DOCS = [
    (
        "root-final",
        """[2026-05-27T20:00:01.000Z] [user]: Implementation decision: the Pi Hindsight client should retain at session_shutdown only, not every turn. Use update_mode replace and document_id pi-session:{session_id}:root for the resumed root session.

[2026-05-27T20:00:02.000Z] [assistant]: Accepted. The stable backend policy is session_shutdown retain with replace and stable pi-session document IDs.

[2026-05-27T20:00:03.000Z] [tool result: bash]: TRANSIENT_DEBUG_NOISE token_budget=888 temporary_probe_id=consolidation-noise""",
    ),
    (
        "resume-final",
        """[2026-05-27T20:10:01.000Z] [user]: Resume confirmation: resumed Pi sessions should keep the same logical pi-session document_id and replace the previous root document at shutdown.

[2026-05-27T20:10:02.000Z] [assistant]: Confirmed. Resume does not retain at session_start; it retains on later session_shutdown using replace.""",
    ),
    (
        "fork-final",
        """[2026-05-27T20:20:01.000Z] [user]: Fork implementation decision: fork documents should retain only turns after the fork point, while parent lineage stays in metadata and tags.

[2026-05-27T20:20:02.000Z] [assistant]: Accepted. Fork-specific suffix documents prevent repeated parent facts while preserving lineage.""",
    ),
]


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


def load_config() -> dict[str, Any]:
    return json.loads((BANK_DIR / f"{SOURCE_BANK}.json").read_text())["config"]


def apply_bank(bank_id: str) -> None:
    config = load_config()
    if not config.get("enable_auto_consolidation"):
        raise RuntimeError(f"{SOURCE_BANK} does not have enable_auto_consolidation enabled")
    request("PUT", f"/v1/default/banks/{q(bank_id)}", json={"name": f"Consolidation canary {bank_id}"})
    request("PATCH", f"/v1/default/banks/{q(bank_id)}/config", json={"updates": config})


def retain_docs(bank_id: str) -> None:
    for i, (doc_suffix, content) in enumerate(DOCS, 1):
        payload = {
            "async": False,
            "items": [{
                "content": content,
                "context": "Pi session-end consolidation canary. Repeated evidence should consolidate into structured observations.",
                "document_id": f"pi-session:consolidation:{doc_suffix}",
                "update_mode": "replace",
                "timestamp": f"2026-05-27T20:{i:02d}:00Z",
                "metadata": {"canary": "consolidation", "doc_suffix": doc_suffix, "event": "session_shutdown"},
                "tags": ["canary", "pi", "event:session_shutdown"],
                "observation_scopes": [
                    ["artifact_type:decision"],
                    ["work_phase:build", "artifact_type:decision"],
                    ["agent_role:orchestrator", "artifact_type:decision"],
                ],
            }],
        }
        t0 = time.time()
        res = request("POST", f"/v1/default/banks/{q(bank_id)}/memories", json=payload)
        u = res.get("usage") or {}
        print(f"retain {doc_suffix}: wall={time.time()-t0:.2f}s input={u.get('input_tokens')} output={u.get('output_tokens')}")


def operations(bank_id: str) -> list[dict[str, Any]]:
    return request("GET", f"/v1/default/banks/{q(bank_id)}/operations", params={"limit": 100}).get("operations", [])


def wait_for_consolidation(bank_id: str, timeout_s: int) -> list[dict[str, Any]]:
    deadline = time.time() + timeout_s
    last: list[dict[str, Any]] = []
    while time.time() < deadline:
        last = operations(bank_id)
        consol = [op for op in last if op.get("task_type") == "consolidation"]
        active = [op for op in consol if op.get("status") in {"pending", "processing"}]
        completed = [op for op in consol if op.get("status") == "completed"]
        failed = [op for op in consol if op.get("status") == "failed"]
        print(f"operations: consolidation completed={len(completed)} active={len(active)} failed={len(failed)}", end="\r")
        if completed and not active:
            print()
            return last
        time.sleep(3)
    print()
    return last


def list_memories(bank_id: str) -> list[dict[str, Any]]:
    return request("GET", f"/v1/default/banks/{q(bank_id)}/memories/list", params={"limit": 200}).get("items", [])


def recall_observations(bank_id: str) -> list[dict[str, Any]]:
    payload = {
        "query": "What is the stable Pi Hindsight retain policy for session shutdown, replace, and pi-session document IDs?",
        "types": ["observation"],
        "budget": "mid",
        "max_tokens": 2000,
        "tags": ["artifact_type:decision"],
        "tags_match": "any_strict",
        "include": {"entities": {"max_tokens": 500}, "source_facts": {}},
    }
    return request("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=payload).get("results", [])


def audit(bank_id: str, ops: list[dict[str, Any]]) -> int:
    failures = 0
    consol = [op for op in ops if op.get("task_type") == "consolidation"]
    completed = [op for op in consol if op.get("status") == "completed"]
    failed = [op for op in consol if op.get("status") == "failed"]
    print(f"consolidation operations: total={len(consol)} completed={len(completed)} failed={len(failed)}")
    if not completed:
        print("FAIL no completed consolidation operation observed")
        failures += 1
    if failed:
        print("FAIL failed consolidation operations:")
        for op in failed:
            print(" -", op.get("id"), op.get("error_message"))
        failures += 1

    memories = list_memories(bank_id)
    observations = [m for m in memories if m.get("fact_type") == "observation"]
    source_facts = [m for m in memories if m.get("fact_type") != "observation"]
    print(f"memory units: total={len(memories)} observations={len(observations)} source_facts={len(source_facts)}")
    if not observations:
        print("FAIL no fact_type=observation memories stored")
        failures += 1
        return failures

    tagged_observations = [m for m in observations if m.get("tags")]
    if len(tagged_observations) != len(observations):
        print(f"FAIL untagged observations: {len(observations) - len(tagged_observations)}")
        for m in observations:
            if not m.get("tags"):
                print(" -", m.get("text"))
        failures += 1

    controlled_tagged = [m for m in observations if EXPECTED_CONTROLLED_TAGS.intersection(set(m.get("tags") or []))]
    if not controlled_tagged:
        print("FAIL no observation carries expected controlled tags", sorted(EXPECTED_CONTROLLED_TAGS))
        failures += 1

    def has_policy_terms(text: str) -> bool:
        text = text.lower()
        return all(any(term in text for term in group) for group in REQUIRED_TERM_GROUPS)

    useful = [m for m in observations if has_policy_terms(m.get("text", ""))]
    if not useful:
        print("FAIL no observation contains required policy term groups", REQUIRED_TERM_GROUPS)
        for m in observations[:5]:
            print(" -", m.get("text"), "tags=", m.get("tags"))
        failures += 1
    else:
        print("PASS observation contains session policy terms")

    noise = [m for m in observations if re.search(r"temporary_probe_id|token_budget|TRANSIENT_DEBUG_NOISE", m.get("text", ""), re.I)]
    if noise:
        print("FAIL debug/tool noise appeared in observations")
        failures += 1

    unconsolidated_sources = [m for m in source_facts if not m.get("consolidated_at") and not m.get("consolidation_failed_at")]
    print(f"source facts without consolidation marker: {len(unconsolidated_sources)}")
    if len(unconsolidated_sources) == len(source_facts) and source_facts:
        print("FAIL no source facts show consolidated_at/consolidation_failed_at markers")
        failures += 1

    recalled = recall_observations(bank_id)
    print(f"strict observation recall: {len(recalled)}")
    if not recalled:
        print("FAIL no observation recall result with strict artifact_type:decision")
        failures += 1
    else:
        r0 = recalled[0]
        print("top observation:", r0.get("text"))
        print("top tags:", r0.get("tags"))
        print("top source_fact_ids:", r0.get("source_fact_ids"))
        if not r0.get("tags"):
            print("FAIL recalled observation has no tags")
            failures += 1
        if r0.get("type") not in {"observation", None}:
            print("FAIL recalled observation type unexpected:", r0.get("type"))
            failures += 1

    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default=str(int(time.time())))
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    bank_id = f"canary-consolidation-{args.suffix}"
    apply_bank(bank_id)
    retain_docs(bank_id)
    ops = wait_for_consolidation(bank_id, args.timeout)
    failures = audit(bank_id, ops)
    print(f"summary: failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
