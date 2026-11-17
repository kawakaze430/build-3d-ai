#!/usr/bin/env bash
# Reproduce the CPU development setup validated during cloud onboarding.
set -euo pipefail
build3d_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$build3d_root"
export PIP_CACHE_DIR="${BUILD3D_CACHE_DIR:-/workspace/.cache}/pip"
export npm_config_cache="${BUILD3D_CACHE_DIR:-/workspace/.cache}/npm"
python -m venv .venv
.venv/bin/python -m pip install -c requirements.lock -e './apps/gateway[test]' -e './apps/api[test]'
(cd apps/web && npm ci --no-audit --no-fund)
.venv/bin/build3d-admin migrate
.venv/bin/python -m pip check
