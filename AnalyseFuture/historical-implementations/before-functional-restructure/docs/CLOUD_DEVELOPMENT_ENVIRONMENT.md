# Restore the development environment

These instructions preserve the CPU development workflow prepared on
17 November 2026. Use the existing checkout; each cloud task is isolated, so
do not create a Git worktree unless requested. The cloud configuration draft
also contains installation and startup instructions; saving that draft did not
publish an environment snapshot. The files here provide a repository copy of
the useful commands and helpers if this workspace is lost.

## Reinstall dependencies

The setup was validated with Python 3.12.14, Node.js 24.22.1 and npm 11.9.0.
Python dependencies are constrained by `requirements.lock`. Web dependencies
use the existing package declarations; no npm lockfile was introduced.

From the repository root:

```bash
bash scripts/cloud/install.sh
```

This installs the API/gateway in `.venv`, installs web dependencies without
creating a lockfile, migrates the default SQLite database, and checks Python
dependency consistency. It does not provision cloud resources, start workers,
download model weights, or create a user. The default caches are under
`/workspace/.cache` because the onboarding user's home caches were unwritable.
For another machine, set `BUILD3D_CACHE_DIR` to a writable cache directory.

## Start the API and studio

From the repository root, keep the API running in a terminal:

```bash
.venv/bin/build3d-admin migrate
.venv/bin/uvicorn build3d_api.main:create_app --factory --host 127.0.0.1 --port 8081
```

In a separate retained terminal, also from the repository root:

```bash
BUILD3D_API_URL=http://127.0.0.1:8081 python scripts/cloud/run_web.py npm run dev -- --hostname 127.0.0.1 --port 3000
```

The web helper runs its command in `apps/web`. On exit it restores the original
contents or absence of `tsconfig.json`, `next-env.d.ts`, `AGENTS.md` and
`tsconfig.tsbuildinfo`, which Next.js may create or rewrite. Stop the child
server normally and let the helper finish; forcibly killing the helper skips
cleanup. Avoid editing those four files while the helper is running.

Use local requests for readiness: API `/health` must report `status: ok`, a
request to `/v1/projects` without credentials must return 401, and the studio
root must return 200. Loopback addresses are internal checks, not supported
onboarding preview links. A PID or open port alone does not establish readiness.

The default database and artifact directory are ignored local development data.
For a new local user, the `build3d-admin create-user --name "Local developer"`
command emits an API key once. Capture it only in a new ignored, permission-0600
file rather than a tool transcript; use it for the studio's private login.
Do not commit keys or databases. The earlier setup-only credentials are not
part of this Git backup and are unnecessary for recreating the environment.

Functional login verification: POST `/api/session` with JSON `apiKey`, retain
its cookie, then GET `/api/session`, `/api/product/v1/projects`,
`/api/product/v1/models` and `/api/product/v1/storage`. These should return 200.
The development server supports the loopback HTTP session. Production uses
a Secure cookie and requires an HTTPS deployment for browser sessions.

## Run the existing checks

From the repository root:

```bash
.venv/bin/python -m pytest -q apps/api/tests apps/gateway/tests
python scripts/cloud/run_web.py npm run typecheck -- --incremental false
python scripts/cloud/run_web.py npm test
python scripts/cloud/run_web.py npm run build
```

The exact first-party test paths avoid collecting the imported upstream tests,
which can require other runtimes or GPUs. Inspect Git status before and after
commands and preserve any user changes.

For browser contracts, stop the actual studio on port 3000 first. The browser
configuration starts its own synthetic backend on 8099 and studio on 3000; it
does not reuse a production studio. Run from the repository root:

```bash
python scripts/cloud/run_web.py npm run test:e2e -- --config ../../scripts/cloud/playwright.config.cjs
```

This retained configuration uses the managed environment's installed
`/usr/bin/chromium` with `--no-sandbox`; browser work still runs inside the
managed environment's isolation. The configuration paths now resolve relative
to the checkout. Reports go to `/tmp/build3d-playwright-results`.
The original browser download failed with a network-policy 403 for
`cdn.playwright.dev`; installed Chromium was used successfully instead. On a
different machine, provide a supported browser rather than assuming this path
exists. The repository's normal Playwright configuration is still available.

## Verified results and limits

Earlier onboarding passed 136 Python tests, four web unit tests, TypeScript
checks, the production build and six browser contract tests. The archive
organization change reran Python/web unit/type checks and verified extracted
file hashes. The detailed project idea records those evidence boundaries.
Browser and storage fixtures are synthetic; they do not establish real model
inference, actual cloud storage, Blender import, or production deployment.

The preserved helpers were relocated from workspace-only files into
`scripts/cloud/`; helper validation for this save is recorded in the handoff.
Live servers, installed dependencies, caches and local smoke data are not
retained by a Git commit. Reinstall dependencies and restart services in a
fresh workspace. An environment snapshot, if separately published through the
product, has its own persistence and runtime contracts.

The default approval list still contains zero production models. No real GPU
inference, training, real S3 bucket or paid infrastructure was started in this
session. Continue next time with the exact runtime/license review and bounded
owner-approved qualification in [FIRST_REAL_GPU_RUNBOOK.md](FIRST_REAL_GPU_RUNBOOK.md).
Do not start a worker or paid compute merely to recreate this development setup.
