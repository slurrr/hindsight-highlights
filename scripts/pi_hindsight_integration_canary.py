#!/usr/bin/env python3
"""Pi-shaped Hindsight integration canaries.

Tests the intended production shape rather than generic memory theory:
- Pi lifecycle triggers via a real pi RPC process + extension event log.
- Pi JSONL transcript serialization using real session-file structure.
- Hindsight retain with full active-branch transcript + update_mode=replace.
- Resume/update, fork/clone lineage, compaction-entry artifact handling.

All Hindsight writes go to canary-* banks.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
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


def base_url() -> str:
    load_dotenv(DEFAULT_ENV)
    return f"http://{os.getenv('HINDSIGHT_API_HOST', '127.0.0.1')}:{os.getenv('HINDSIGHT_API_PORT', '8888')}"


def hreq(method: str, path: str, **kwargs: Any) -> Any:
    r = httpx.request(method, f"{base_url()}{path}", timeout=180.0, **kwargs)
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{method} {path} HTTP {exc.response.status_code}: {exc.response.text[:4000]}") from exc
    return r.json() if r.content else {}


def q(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def load_bank_config() -> dict[str, Any]:
    return json.loads((BANK_DIR / f"{SOURCE_BANK}.json").read_text())["config"]


def apply_canary_bank(bank_id: str) -> None:
    hreq("PUT", f"/v1/default/banks/{q(bank_id)}", json={"name": f"Pi integration canary {bank_id}"})
    hreq("PATCH", f"/v1/default/banks/{q(bank_id)}/config", json={"updates": load_bank_config()})


def entry(ts: str, typ: str, eid: str, parent: str | None, **kw: Any) -> dict[str, Any]:
    d = {"type": typ, "id": eid, "parentId": parent, "timestamp": ts}
    d.update(kw)
    return d


def synthetic_session(path: Path, include_resume_tail: bool = True) -> dict[str, str]:
    sid = "pi-hindsight-canary-session"
    header = {"type": "session", "version": 3, "id": sid, "timestamp": "2026-05-27T18:00:00.000Z", "cwd": str(ROOT)}
    rows: list[dict[str, Any]] = [header]
    rows += [
        entry("2026-05-27T18:00:01.000Z", "message", "u0000001", None, message={"role": "user", "timestamp": 1790436001000, "content": "Decision: the Pi memory extension should retain to Hindsight on session_shutdown for quit, new, resume, and fork, not after every turn."}),
        entry("2026-05-27T18:00:02.000Z", "message", "a0000002", "u0000001", message={"role": "assistant", "timestamp": 1790436002000, "content": [{"type": "text", "text": "Accepted implementation decision: use session_shutdown lifecycle events as the minimal session-end trigger for Hindsight retain."}], "provider": "canary", "model": "synthetic", "api": "openai", "usage": {}, "stopReason": "stop"}),
        entry("2026-05-27T18:00:03.000Z", "message", "u0000003", "a0000002", message={"role": "user", "timestamp": 1790436003000, "content": "API contract: full Pi active-branch transcripts should use document_id pi-session:<session_id>:<leaf_id> with update_mode replace."}),
        entry("2026-05-27T18:00:04.000Z", "message", "a0000004", "u0000003", message={"role": "assistant", "timestamp": 1790436004000, "content": [{"type": "toolCall", "id": "call_noise", "name": "bash", "arguments": {"command": "echo DEBUG_TOKEN_BUDGET=999999 temporary_probe_id=noise"}}, {"type": "text", "text": "The document identifier and replace mode contract is accepted."}], "provider": "canary", "model": "synthetic", "api": "openai", "usage": {}, "stopReason": "stop"}),
        entry("2026-05-27T18:00:05.000Z", "message", "t0000005", "a0000004", message={"role": "toolResult", "timestamp": 1790436005000, "toolCallId": "call_noise", "toolName": "bash", "content": [{"type": "text", "text": "DEBUG_TOKEN_BUDGET=999999 temporary_probe_id=noise stacktrace_marker=ignore_me"}], "isError": False}),
        entry("2026-05-27T18:00:06.000Z", "compaction", "c0000006", "t0000005", summary="Compaction summary: the accepted rule is retain on session_shutdown only, and use pi-session document IDs with replace mode.", firstKeptEntryId="u0000003", tokensBefore=64000, details={"readFiles": ["docs/pi-sessions.md"], "modifiedFiles": ["scripts/pi_hindsight_integration_canary.py"]}),
    ]
    if include_resume_tail:
        rows += [
            entry("2026-05-27T18:10:01.000Z", "message", "u0000007", "c0000006", message={"role": "user", "timestamp": 1790436601000, "content": "Resume update decision: on session_compact, retain a separate compaction artifact with document_id pi-compaction:<session_id>:<compaction_entry_id>."}),
            entry("2026-05-27T18:10:02.000Z", "message", "a0000008", "u0000007", message={"role": "assistant", "timestamp": 1790436602000, "content": [{"type": "text", "text": "Accepted: compaction entries are retained as separate artifacts and not treated as whole-session endings."}], "provider": "canary", "model": "synthetic", "api": "openai", "usage": {}, "stopReason": "stop"}),
        ]
    rows += [
        entry("2026-05-27T18:20:01.000Z", "message", "u00000f1", "u0000003", message={"role": "user", "timestamp": 1790437201000, "content": "Fork task A result: branch-specific memory must keep fork lineage separate from the parent session."}),
        entry("2026-05-27T18:20:02.000Z", "message", "a00000f2", "u00000f1", message={"role": "assistant", "timestamp": 1790437202000, "content": [{"type": "text", "text": "Fork A completed: branch lineage should be represented in metadata and tags, not merged into the parent transcript."}], "provider": "canary", "model": "synthetic", "api": "openai", "usage": {}, "stopReason": "stop"}),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return {"session_id": sid, "root_leaf": "a0000008" if include_resume_tail else "c0000006", "fork_leaf": "a00000f2", "compaction_id": "c0000006", "fork_entry": "u0000003"}


def read_entries(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return rows[0], {r["id"]: r for r in rows[1:] if "id" in r}


def path_to_leaf(entries: dict[str, dict[str, Any]], leaf: str) -> list[dict[str, Any]]:
    out = []
    cur = leaf
    while cur:
        e = entries[cur]
        out.append(e)
        cur = e.get("parentId")
    return list(reversed(out))


def text_blocks(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if b.get("type") == "text":
            parts.append(b.get("text", ""))
        elif b.get("type") == "toolCall":
            parts.append(f"[tool call: {b.get('name')} {json.dumps(b.get('arguments', {}), ensure_ascii=False)}]")
        elif b.get("type") == "thinking":
            continue
    return "\n".join(p for p in parts if p)


def serialize_entry(e: dict[str, Any], *, include_compactions: bool = True) -> str:
    typ = e["type"]
    if typ == "message":
        m = e["message"]
        role = m.get("role")
        if role == "toolResult":
            body = text_blocks(m.get("content"))[:2000]
            return f"[{e['timestamp']}] [Tool result: {m.get('toolName')}]: {body}"
        return f"[{e['timestamp']}] [{role}]: {text_blocks(m.get('content'))}"
    if typ == "compaction":
        if not include_compactions:
            return ""
        return f"[{e['timestamp']}] [Compaction summary id={e['id']} tokensBefore={e.get('tokensBefore')}]: {e.get('summary')}"
    if typ == "branch_summary":
        return f"[{e['timestamp']}] [Branch summary from={e.get('fromId')}]: {e.get('summary')}"
    return f"[{e['timestamp']}] [{typ}]: {json.dumps(e, ensure_ascii=False)}"


def serialize_session(path: Path, leaf: str, *, after_id: str | None = None, include_compactions: bool = False) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    header, entries = read_entries(path)
    branch = path_to_leaf(entries, leaf)
    if after_id:
        idx = next((i for i, e in enumerate(branch) if e["id"] == after_id), -1)
        if idx >= 0:
            branch = branch[idx + 1:]
    rendered = [serialize_entry(e, include_compactions=include_compactions) for e in branch]
    return header, "\n\n".join(s for s in rendered if s), branch


def retain_document(bank_id: str, document_id: str, content: str, context: str, metadata: dict[str, str], tags: list[str]) -> dict[str, Any]:
    payload = {"async": False, "items": [{"content": content, "context": context, "document_id": document_id, "update_mode": "replace", "timestamp": "2026-05-27T18:30:00Z", "metadata": metadata, "tags": tags, "observation_scopes": "combined"}]}
    t0 = time.time()
    res = hreq("POST", f"/v1/default/banks/{q(bank_id)}/memories", json=payload)
    res["wall_seconds"] = round(time.time() - t0, 2)
    return res


def list_memories(bank_id: str) -> list[dict[str, Any]]:
    return hreq("GET", f"/v1/default/banks/{q(bank_id)}/memories/list", params={"limit": 100}).get("items", [])


def recall(bank_id: str, query: str, tags: list[str] | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"query": query, "budget": "mid", "max_tokens": 2048}
    if tags:
        payload.update({"tags": tags, "tags_match": "any_strict"})
    return hreq("POST", f"/v1/default/banks/{q(bank_id)}/memories/recall", json=payload).get("results", [])


def norm_fact(text: str) -> str:
    text = text.split(" | ", 1)[0]
    return re.sub(r"[^a-z0-9:_<>]+", " ", text.lower()).strip()


def audit(bank_id: str) -> int:
    failures = 0
    memories = list_memories(bank_id)
    joined = "\n".join(m.get("text", "") for m in memories).lower()
    checks = [
        ("shutdown retain decision", ["session_shutdown", "quit", "resume", "fork"]),
        ("pi-session document contract", ["pi-session", "replace"]),
        ("compaction document contract", ["pi-compaction", "session_compact"]),
        ("fork lineage", ["fork", "lineage", "parent"]),
    ]
    print(f"memory units: {len(memories)}")
    for name, terms in checks:
        ok = all(t.lower() in joined for t in terms)
        print(("PASS" if ok else "FAIL"), name)
        failures += 0 if ok else 1
    noise = [m for m in memories if re.search(r"DEBUG_TOKEN_BUDGET|temporary_probe_id|stacktrace_marker", m.get("text", ""), re.I)]
    if noise:
        print("FAIL tool/debug noise became memory")
        failures += 1
    normalized = [norm_fact(m.get("text", "")) for m in memories if m.get("text")]
    duplicate_count = len(normalized) - len(set(normalized))
    if duplicate_count:
        print(f"WARN duplicate-ish facts after timestamp stripping: {duplicate_count}")
    strict = recall(bank_id, "What implementation decision controls Hindsight retain timing for Pi?", ["artifact_type:decision"])
    print(f"strict artifact_type:decision recall: {len(strict)}")
    if not strict:
        failures += 1
    return failures


def run_retain_canary(suffix: str, keep_tmp: bool = False) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pi-hindsight-canary-"))
    try:
        session_path = tmp / "sessions" / "synthetic.jsonl"
        ids = synthetic_session(session_path, include_resume_tail=False)
        bank_id = f"canary-pi-integration-{suffix}"
        apply_canary_bank(bank_id)

        # Initial session-end retain, then resumed-session replace with same logical document id.
        header, content, _ = serialize_session(session_path, ids["root_leaf"])
        doc_id = f"pi-session:{header['id']}:root"
        r1 = retain_document(bank_id, doc_id, content, "Pi session_shutdown retain canary before resume tail.", {"pi_session_id": header["id"], "pi_leaf_id": ids["root_leaf"], "event": "session_shutdown"}, ["canary", "pi", "event:session_shutdown", "mode:replace"])
        ids = synthetic_session(session_path, include_resume_tail=True)
        header, content, _ = serialize_session(session_path, ids["root_leaf"])
        r2 = retain_document(bank_id, doc_id, content, "Pi resumed session shutdown retain canary; same document replaced with full active branch.", {"pi_session_id": header["id"], "pi_leaf_id": ids["root_leaf"], "event": "session_shutdown", "resume": "true"}, ["canary", "pi", "event:session_shutdown", "mode:replace"])

        # Fork branch as separate lineage document.
        header, fcontent, _ = serialize_session(session_path, ids["fork_leaf"], after_id=ids["fork_entry"], include_compactions=False)
        r3 = retain_document(bank_id, f"pi-session:{header['id']}:fork-a", fcontent, "Pi fork/clone lineage canary; this document intentionally contains only fork-specific turns after the fork point, with parent lineage in metadata.", {"pi_session_id": header["id"], "pi_leaf_id": ids["fork_leaf"], "parent_leaf_id": ids["root_leaf"], "fork_point_entry_id": ids["fork_entry"], "event": "session_shutdown", "fork": "true"}, ["canary", "pi", "event:fork", "branch:fork-a"])

        # Compaction artifact as its own document.
        _, entries = read_entries(session_path)
        c = entries[ids["compaction_id"]]
        cdoc_id = f"pi-compaction:{header['id']}:{c['id']}"
        ctext = f"Compaction retain contract: on Pi session_compact, retain this separate artifact with document_id {cdoc_id}.\n\n" + serialize_entry(c, include_compactions=True)
        r4 = retain_document(bank_id, cdoc_id, ctext, "Pi session_compact artifact canary; separate from full-session retain.", {"pi_session_id": header["id"], "compaction_entry_id": c["id"], "event": "session_compact"}, ["canary", "pi", "event:session_compact"])

        print("retain usage:")
        for label, r in [("initial", r1), ("resume_replace", r2), ("fork", r3), ("compaction", r4)]:
            u = r.get("usage") or {}
            print(f"  {label}: wall={r['wall_seconds']}s input={u.get('input_tokens')} output={u.get('output_tokens')}")
        return audit(bank_id)
    finally:
        if keep_tmp:
            print(f"kept temp: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


def write_event_extension(path: Path, log_path: Path) -> None:
    path.write_text(textwrap.dedent(f'''
        import type {{ ExtensionAPI }} from "@earendil-works/pi-coding-agent";
        import * as fs from "node:fs";
        const log = {json.dumps(str(log_path))};
        function rec(name: string, event: any, ctx: any) {{
          fs.appendFileSync(log, JSON.stringify({{name, event, sessionFile: ctx.sessionManager?.getSessionFile?.(), ts: Date.now()}}) + "\\n");
        }}
        export default function(pi: ExtensionAPI) {{
          for (const name of ["session_start", "session_shutdown", "session_before_switch", "session_before_fork", "session_before_compact", "session_compact", "session_before_tree", "session_tree", "agent_end", "turn_end"] as const) {{
            pi.on(name, async (event, ctx) => rec(name, event, ctx));
          }}
        }}
    '''))


def rpc_send(proc: subprocess.Popen[str], obj: dict[str, Any], timeout: float = 15) -> dict[str, Any]:
    assert proc.stdin and proc.stdout
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if msg.get("type") == "response" and ("id" not in obj or msg.get("id") == obj.get("id")):
            return msg
    raise TimeoutError(f"no RPC response for {obj}")


def run_event_canary(suffix: str, keep_tmp: bool = False) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pi-event-canary-"))
    try:
        session_path = tmp / "seed.jsonl"
        ids = synthetic_session(session_path, include_resume_tail=True)
        log_path = tmp / "events.jsonl"
        ext_path = tmp / "event-log.ts"
        write_event_extension(ext_path, log_path)
        cmd = ["pi", "--mode", "rpc", "--offline", "--no-extensions", "--extension", str(ext_path), "--session", str(session_path), "--session-dir", str(tmp / "session-dir"), "--no-context-files", "--no-skills", "--no-prompt-templates", "--no-themes", "--model", "openai/gpt-4o-mini"]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT))
        failures = 0
        try:
            state = rpc_send(proc, {"id": "state", "type": "get_state"}, 25)
            forks = rpc_send(proc, {"id": "forkmsgs", "type": "get_fork_messages"}, 25)
            fork_entry = ids["fork_entry"]
            if forks.get("success"):
                msgs = forks.get("data", {}).get("messages", [])
                if msgs:
                    fork_entry = msgs[0].get("entryId", fork_entry)
            rpc_send(proc, {"id": "clone", "type": "clone"}, 25)
            rpc_send(proc, {"id": "new", "type": "new_session"}, 25)
            rpc_send(proc, {"id": "switch", "type": "switch_session", "sessionPath": str(session_path)}, 25)
            rpc_send(proc, {"id": "fork", "type": "fork", "entryId": fork_entry}, 25)
        finally:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        time.sleep(0.5)
        events = [json.loads(l) for l in log_path.read_text().splitlines() if l.strip()] if log_path.exists() else []
        names = [e["name"] for e in events]
        print("pi event log:", log_path)
        print("events:", names)
        for required in ["session_start", "session_shutdown", "session_before_switch", "session_before_fork"]:
            if required not in names:
                print("FAIL missing event", required)
                failures += 1
            else:
                print("PASS event", required)
        reasons = [e.get("event", {}).get("reason") for e in events if e["name"] in {"session_start", "session_shutdown", "session_before_switch"}]
        print("reasons:", reasons)
        if not any(r == "fork" for r in reasons):
            print("FAIL no fork reason observed")
            failures += 1
        if keep_tmp:
            print(f"kept temp: {tmp}")
        return failures
    finally:
        if not keep_tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default=str(int(time.time())))
    ap.add_argument("--events", action="store_true")
    ap.add_argument("--retain", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--keep-tmp", action="store_true")
    args = ap.parse_args()
    if not (args.events or args.retain or args.all):
        args.all = True
    failures = 0
    if args.events or args.all:
        print("\n== Pi lifecycle event canary ==")
        failures += run_event_canary(args.suffix, args.keep_tmp)
    if args.retain or args.all:
        print("\n== Pi transcript → Hindsight retain canary ==")
        failures += run_retain_canary(args.suffix, args.keep_tmp)
    print(f"\nsummary: failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
