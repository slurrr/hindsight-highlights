#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv sync "$@"

# Local workstation runtime policy: upstream Hindsight routes torch to CPU for
# portable installs; this machine should use CUDA for local embeddings/reranker.
uv pip install --reinstall-package torch --index-url https://download.pytorch.org/whl/cu130 'torch>=2.6.0'

.venv/bin/python - <<'PY'
import sys
import torch
print(f"torch={torch.__version__} cuda={torch.version.cuda} available={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA torch is not available after sync")
PY
