# Hindsight Highlights command surface

This repo uses **systemd** for the Hindsight API.

- **Service/runtime logs:** journald
- **Run artifacts / experiments:** `~/runs/hindsight-highlights/`
- **Legacy unbounded file log:** `/home/poop/runs/hindsight/api.log`

## Service lifecycle

### Install the unit
```bash
sudo cp systemd/hindsight-api.service /etc/systemd/system/hindsight-api.service
```

### Reload systemd after changing the unit file
```bash
sudo systemctl daemon-reload
```

### Enable at boot
```bash
sudo systemctl enable hindsight-api
```

### Enable and start now
```bash
sudo systemctl enable --now hindsight-api
```

### Start / stop / restart
```bash
sudo systemctl start hindsight-api
sudo systemctl stop hindsight-api
sudo systemctl restart hindsight-api
```

### Kill it if needed
```bash
sudo systemctl stop hindsight-api
# if it is hung and you really need to force it:
sudo systemctl kill --signal=SIGKILL hindsight-api
```

### Check status
```bash
sudo systemctl status hindsight-api --no-pager
```

## Journald logs

### Live logs
```bash
sudo journalctl -u hindsight-api -f
```

### Recent logs
```bash
sudo journalctl -u hindsight-api -n 200 --no-pager
```

### Narrow by time window
```bash
sudo journalctl -u hindsight-api --since "2026-05-31 15:20" --until "2026-05-31 15:26" --no-pager
```

### Raw log lines only
```bash
sudo journalctl -u hindsight-api -o cat
```

### Log to a file if needed
```bash
sudo journalctl -u hindsight-api --since "today" --no-pager > /home/poop/runs/hindsight-highlights/hindsight-api-$(date -u +%Y%m%dT%H%M%SZ).log
```

### Journal size / retention
```bash
sudo journalctl --disk-usage
sudo journalctl --vacuum-time=7d
sudo journalctl --vacuum-size=500M
```

## Runtime evidence

### Monitor VRAM for the Hindsight API PID
```bash
uv run python scripts/monitor_hindsight_vram.py --pid <pid>
```

### Inspect the legacy unbounded run log
```bash
less /home/poop/runs/hindsight/api.log
```

## Memory write audits

Read-only workflow for checking latest retained facts and consolidation output. This is for write quality, not recall quality.

### Audit all configured local-agent banks
```bash
uv run python scripts/memory_write_audit.py
```

### Audit one bank with more recent items
```bash
uv run python scripts/memory_write_audit.py --banks local-agent-user-profile --limit 10
```

### Filter memory text while auditing
```bash
uv run python scripts/memory_write_audit.py --banks local-agent-user-profile --q Seth --limit 20
```

### Save a markdown audit report
```bash
uv run python scripts/memory_write_audit.py \
  --output /home/poop/runs/hindsight-highlights/memory-write-audit-$(date -u +%Y%m%dT%H%M%SZ).md
```

The report includes compact bank stats, recent `world` facts, recent `experience` facts, recent `observation` consolidations, and mental model metadata if any models exist.

## Reflect / mental model planning

Current implementation plan:

```bash
less docs/reflect-mental-model-plan.md
```

Reflect and mental models are separate from automatic observation consolidation: `reflect_mission` configures explicit reflect calls, while mental models are saved/curated reflect responses that must be created through the mental-model API/client flow.

## Where to look for evidence

- **Service/runtime logs:** journald (`journalctl -u hindsight-api`)
- **Canary run evidence:** `~/runs/hindsight-highlights/`
- **Actual retained memories/facts:** Hindsight database / API, not journald
