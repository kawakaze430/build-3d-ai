#!/usr/bin/env python3
"""Run a web command and restore files Next.js generates or rewrites on exit."""
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[2] / 'apps' / 'web'
paths = [root / p for p in ('tsconfig.json', 'next-env.d.ts', 'AGENTS.md', 'tsconfig.tsbuildinfo')]
before = {p: p.read_bytes() if p.exists() else None for p in paths}
try:
    result = subprocess.run(sys.argv[1:], cwd=root)
    code = result.returncode
finally:
    for p, content in before.items():
        if content is None:
            p.unlink(missing_ok=True)
        else:
            p.write_bytes(content)
sys.exit(code)
