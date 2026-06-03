#!/usr/bin/env python3
"""Monitor GPU memory usage for a target PID and record baseline/delta.

Example:
  uv run python scripts/monitor_hindsight_vram.py --pid 2602608
  uv run python scripts/monitor_hindsight_vram.py --pid-name hindsight-api
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = Path.home() / "runs" / "hindsight-highlights"

STOP = False


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pid", type=int, help="PID to monitor")
    p.add_argument("--pid-name", default="hindsight-api", help="Fallback process name to resolve if --pid is omitted")
    p.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds")
    p.add_argument("--baseline-samples", type=int, default=10, help="Number of initial samples used to establish baseline")
    p.add_argument("--outdir", type=Path, default=DEFAULT_RUNS_DIR, help="Directory for logs")
    p.add_argument("--log-file", type=Path, help="Explicit log file path (overrides default naming)")
    return p.parse_args()


def resolve_pid(pid: int | None, pid_name: str) -> int:
    if pid is not None:
        return pid
    try:
        out = subprocess.check_output(["pgrep", "-f", pid_name], text=True).splitlines()
    except subprocess.CalledProcessError:
        raise SystemExit(f"could not resolve PID from --pid-name {pid_name!r}")
    pids = [int(x) for x in out if x.strip()]
    if not pids:
        raise SystemExit(f"no process matched --pid-name {pid_name!r}")
    return pids[0]


def query_used_memory(pid: int) -> int | None:
    cmd = [
        "nvidia-smi",
        f"--query-compute-apps=pid,used_memory",
        "--format=csv,noheader,nounits",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        try:
            line_pid = int(parts[0])
        except ValueError:
            continue
        if line_pid != pid:
            continue
        digits = "".join(ch for ch in parts[1] if ch.isdigit())
        if not digits:
            return None
        return int(digits)
    return None


def log_line(fp, text: str) -> None:
    print(text, flush=True)
    fp.write(text + "\n")
    fp.flush()


def main() -> int:
    global STOP
    args = parse_args()
    pid = resolve_pid(args.pid, args.pid_name)

    args.outdir.mkdir(parents=True, exist_ok=True)
    log_file = args.log_file or args.outdir / f"vram-monitor-{utc_stamp()}-pid{pid}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    def handle_stop(signum, frame):
        global STOP
        del signum, frame
        STOP = True

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    with log_file.open("a", encoding="utf-8") as fp:
        log_line(fp, f"START ts={utc_stamp()} pid={pid} interval={args.interval}s baseline_samples={args.baseline_samples}")
        log_line(fp, f"LOG_FILE {log_file}")

        baseline_samples: list[int] = []
        while len(baseline_samples) < max(1, args.baseline_samples) and not STOP:
            mem = query_used_memory(pid)
            if mem is not None:
                baseline_samples.append(mem)
                log_line(fp, f"BASELINE_SAMPLE ts={utc_stamp()} mem_mib={mem}")
            else:
                log_line(fp, f"BASELINE_SAMPLE ts={utc_stamp()} mem_mib=NA")
            time.sleep(args.interval)

        if not baseline_samples:
            log_line(fp, f"ERROR ts={utc_stamp()} unable to read memory for pid={pid}")
            return 2

        baseline = int(statistics.median(baseline_samples))
        baseline_min = min(baseline_samples)
        baseline_max = max(baseline_samples)
        log_line(
            fp,
            f"BASELINE ts={utc_stamp()} mem_mib={baseline} min_mib={baseline_min} max_mib={baseline_max} samples={len(baseline_samples)}",
        )

        max_mem = baseline
        max_delta = 0
        last_mem: int | None = None

        while not STOP:
            mem = query_used_memory(pid)
            ts = utc_stamp()
            if mem is None:
                log_line(fp, f"SAMPLE ts={ts} mem_mib=NA delta_mib=NA max_delta_mib={max_delta}")
            else:
                delta = mem - baseline
                if mem > max_mem:
                    max_mem = mem
                    max_delta = max(max_delta, delta)
                    log_line(fp, f"NEW_MAX ts={ts} mem_mib={mem} delta_mib={delta} baseline_mib={baseline}")
                elif last_mem is None or mem != last_mem:
                    log_line(fp, f"SAMPLE ts={ts} mem_mib={mem} delta_mib={delta} max_delta_mib={max_delta}")
                last_mem = mem
            time.sleep(args.interval)

        log_line(
            fp,
            f"STOP ts={utc_stamp()} baseline_mib={baseline} max_mem_mib={max_mem} max_delta_mib={max_mem - baseline}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
