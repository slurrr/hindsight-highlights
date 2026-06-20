#!/usr/bin/env python3
"""Check local Hindsight + Grafana LGTM monitoring wiring."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import Any

API = "http://127.0.0.1:8888"
GRAFANA = "http://127.0.0.1:3000"
PROM_PROXY = f"{GRAFANA}/api/datasources/proxy/uid/prometheus"
LOKI_PROXY = f"{GRAFANA}/api/datasources/proxy/uid/loki"


def fetch(url: str, timeout: float = 10.0) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def get_json(url: str, timeout: float = 10.0) -> Any:
    return json.loads(fetch(url, timeout).decode("utf-8"))


def prom_query(query: str) -> list[dict[str, Any]]:
    url = f"{PROM_PROXY}/api/v1/query?" + urllib.parse.urlencode({"query": query})
    data = get_json(url)
    return data.get("data", {}).get("result", [])


def main() -> int:
    failed = False

    print("Hindsight API /metrics:")
    try:
        metrics = fetch(f"{API}/metrics", timeout=5).decode("utf-8", "replace")
        has_llm = "hindsight_llm_calls_total" in metrics
        print(f"  OK reachable, hindsight_llm_calls_total={has_llm}")
        failed = failed or not has_llm
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL {e}")
        failed = True

    print("\nGrafana/Prometheus readiness:")
    try:
        ready = fetch(f"{PROM_PROXY}/-/ready", timeout=5).decode("utf-8", "replace").strip()
        print(f"  OK {ready}")
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL {e}")
        failed = True

    print("\nPrometheus scrape targets:")
    try:
        targets = get_json(f"{PROM_PROXY}/api/v1/targets")
        active = targets.get("data", {}).get("activeTargets", [])
        if not active:
            print("  FAIL no active targets")
            failed = True
        for target in active:
            health = target.get("health")
            err = target.get("lastError") or ""
            print(f"  {health.upper():4} {target.get('scrapeUrl')} {err}")
            failed = failed or health != "up"
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL {e}")
        failed = True

    print("\nPrometheus Hindsight metric queries:")
    for query in [
        "up{job=\"hindsight-api\"}",
        "hindsight_llm_calls_total",
        "hindsight_llm_duration_seconds_count",
        "hindsight_llm_tokens_output_tokens_total",
        "hindsight_http_requests_total",
    ]:
        try:
            result = prom_query(query)
            print(f"  {query}: {len(result)} series")
            failed = failed or (query != "up{job=\"hindsight-api\"}" and len(result) == 0)
        except Exception as e:  # noqa: BLE001
            print(f"  {query}: FAIL {e}")
            failed = True

    print("\nLoki Hindsight logs:")
    try:
        url = f"{LOKI_PROXY}/loki/api/v1/labels"
        labels = get_json(url).get("data", [])
        print(f"  labels available={len(labels)}")
        query_url = f"{LOKI_PROXY}/loki/api/v1/query_range?" + urllib.parse.urlencode({"query": '{job="hindsight-journal"}', "limit": 5})
        result = get_json(query_url).get("data", {}).get("result", [])
        print(f"  hindsight-journal streams={len(result)}")
        if not result:
            print("  WARN no Hindsight journal logs in Loki yet; restart monitoring or generate a service log line")
    except Exception as e:  # noqa: BLE001
        print(f"  WARN Loki check failed: {e}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
