#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HINDSIGHT_SOURCE_ROOT="${HINDSIGHT_SOURCE_ROOT:-$HOME/code/vendor/hindsight}"
RUN_DIR="${HINDSIGHT_MONITORING_RUN_DIR:-$HOME/runs/hindsight-monitoring}"
mkdir -p "$RUN_DIR"

UPSTREAM_MON="$HINDSIGHT_SOURCE_ROOT/scripts/dev/monitoring"
UPSTREAM_DASH="$HINDSIGHT_SOURCE_ROOT/monitoring/grafana/dashboards"
[[ -f "$UPSTREAM_MON/grafana-dashboards.yaml" ]] || { echo "missing $UPSTREAM_MON/grafana-dashboards.yaml" >&2; exit 1; }
[[ -f "$UPSTREAM_DASH/hindsight-operations.json" ]] || { echo "missing upstream dashboards in $UPSTREAM_DASH" >&2; exit 1; }

# The Hindsight API intentionally binds to 127.0.0.1 on the host. A bridged
# Docker container cannot scrape that through host.docker.internal because the
# service is not bound on the bridge gateway. Run LGTM in host networking and
# scrape 127.0.0.1:8888 from the host namespace.
cat > "$RUN_DIR/prometheus.yaml" <<'EOF_PROM'
global:
  scrape_interval: 5s
  evaluation_interval: 5s
  scrape_native_histograms: true

otlp:
  keep_identifying_resource_attributes: true
  promote_resource_attributes:
    - service.instance.id
    - service.name
    - service.namespace
    - service.version
    - deployment.environment
    - deployment.environment.name
    - host.name

storage:
  tsdb:
    out_of_order_time_window: 10m

scrape_configs:
  - job_name: 'hindsight-api'
    static_configs:
      - targets: ['127.0.0.1:8888']
    metrics_path: '/metrics'
    scrape_interval: 5s
EOF_PROM

cat > "$RUN_DIR/docker-compose.yaml" <<EOF
services:
  grafana-lgtm:
    image: grafana/otel-lgtm:latest
    container_name: hindsight-monitoring
    network_mode: host
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
      - GF_AUTH_DISABLE_LOGIN_FORM=true
    security_opt:
      - label=disable
    volumes:
      - $RUN_DIR/prometheus.yaml:/otel-lgtm/prometheus.yaml:ro
      - $UPSTREAM_DASH/hindsight-operations.json:/otel-lgtm/hindsight-operations.json:ro
      - $UPSTREAM_DASH/hindsight-llm.json:/otel-lgtm/hindsight-llm.json:ro
      - $UPSTREAM_DASH/hindsight-api-service.json:/otel-lgtm/hindsight-api-service.json:ro
      - $UPSTREAM_MON/grafana-dashboards.yaml:/otel-lgtm/grafana/conf/provisioning/dashboards/grafana-dashboards.yaml:ro
    restart: unless-stopped
EOF

echo "hindsight monitoring: Grafana http://localhost:3000" >&2
echo "hindsight monitoring: OTEL http://localhost:4318" >&2

shipper_pid_file="$RUN_DIR/loki-journal-shipper.pid"
if [[ -f "$shipper_pid_file" ]]; then
  old_pid="$(cat "$shipper_pid_file" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" >/dev/null 2>&1; then
    kill "$old_pid" >/dev/null 2>&1 || true
  fi
fi
nohup "$ROOT/.venv/bin/python" "$ROOT/scripts/loki_journal_shipper.py" --since "1 hour ago" >"$RUN_DIR/loki-journal-shipper.log" 2>&1 &
echo $! > "$shipper_pid_file"
echo "hindsight monitoring: Loki journal shipper pid $(cat "$shipper_pid_file")" >&2

cd "$RUN_DIR"
exec docker-compose up "$@"
