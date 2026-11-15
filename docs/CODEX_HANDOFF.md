# Developer handoff — 15 November 2026

## Main is now the product baseline

The old stacked PR handoff is obsolete.

Merged into `main` during the consolidation session:

- PR #1 → Phase-0 gateway/checklist baseline.
- PR #14 → clean consolidation of the reviewed #11/#12/#13 stack: fail-closed model policy, GLB verification, durable product API/worker, PostgreSQL/SQLite CI and recovery semantics.
- PR #15 → first-party `apps/web` browser studio, secure API-key BFF session, project/generation/job UI, real product GLB viewer/download path and browser tests.
- PR #16 → artifact storage abstraction, owner-scoped filesystem layout and optional private S3-compatible backend.
- PR #17 → current baseline documentation and public-identity architecture decision.
- PR #18 → expanded exact-revision reuse/license audit, including rejection of restricted stock Step1X/TripoSG runtime paths.
- PR #19 → immutable external identity mapping foundation; no public JWT/session acceptance yet.
- PR #20 → TripoSR qualification evidence plus strict embedded-texture GLB packager.

PRs #11, #12 and #13 were closed as superseded after PR #14 preserved their final reviewed/tested tree on the post-#1 main baseline.

## What is actually implemented and tested

### `apps/gateway`

Private upstream 3DAIGC API client, control authentication, fail-closed approved-model policy, bounded GLB structural verification and explicit-spend GPU smoke CLI.

The gateway includes a strict first-party xatlas-style OBJ + baked PNG → self-contained PBR GLB packager on the TripoSR qualification milestone. This addresses the stock texture-export format gap without copying xatlas's exporter and reuses the product GLB validator. Its automated tests prove CPU structure/integrity only; a real texture still needs browser/Blender visual checking.

### `apps/api`

Database-backed users/API keys/projects/jobs/artifacts, tenant isolation, bounded image normalization, idempotent local admission, active-job/rate limits, fenced worker leases, uncertain non-idempotent submission quarantine, restartable polling, operator reconciliation and verified artifact downloads.

Migration `0002` adds immutable external identity mappings keyed by provider issuer+subject with operator-only link/list/unlink commands. This is an ownership boundary only; `apps/api` still accepts only product API keys over HTTP and does not trust external JWT/session claims yet.

Artifact bytes now go through an `ArtifactStorage` abstraction. Filesystem remains default. An S3-compatible backend is available only when configured and verifies size/SHA metadata before DB completion; API downloads materialize then revalidate GLB structure/checksum before serving.

### `apps/web`

Next.js browser studio with:
- private operator-provisioned user-key login through an HttpOnly SameSite cookie;
- strict server-side BFF allowlist to the tenant API;
- project create/list/open;
- approved-model state and honest disabled-generation state;
- text/image job submission and persisted history;
- distinct uncertain/recovery states;
- real GLB download/viewer route with orbit/zoom/reset/wireframe and mesh statistics;
- responsive UI;
- Vitest and Playwright contract/browser coverage.

No production UI path uses a sample mesh. The Playwright backend/triangle GLB are explicitly synthetic fixtures.

## Verification evidence

PR #14: Gateway CI + Product API CI passed.

PR #15 on commit `c8fe3c7b3e2c77eb49ef7cd1078d3b823a183c12`:
- Gateway CI: passed.
- Product API CI: passed.
- Web Studio CI: dependency install, TypeScript typecheck, Vitest, Next production build, Chromium install and Playwright browser tests all passed.

PR #16 on commit `9c4478194fcdacb2765bb8925fc357ff8906bbf8`:
- Gateway CI: passed.
- Product API CI: passed, including filesystem/S3-compatible storage tests with an in-process synthetic object-store client.

Do not infer Docker, paid cloud or GPU validation from those results.

## Current architecture decisions

- Browser: first-party Next.js/React/Three.js rather than vendoring Open3DStudio. See [ADR 0001](adr/0001-web-studio-foundation.md).
- Storage: filesystem default + optional S3-compatible backend; no public object URLs yet. See [OBJECT_STORAGE.md](OBJECT_STORAGE.md).
- Public identity: Better Auth is the preferred candidate. Immutable external-identity mapping is now implemented; the remaining gate is short-lived cryptographically verified issuer/audience-bound BFF→API identity plus full account lifecycle. See [IDENTITY_AND_ACCOUNT_LIFECYCLE.md](IDENTITY_AND_ACCOUNT_LIFECYCLE.md).
- Upstream model policy: zero production models approved by default.
- Non-idempotent upstream generation POSTs: never automatically replay an uncertain submission.

## Current first-GPU candidate

TripoSR is the current **qualification candidate**, not an approved production model. Pinned evidence and the proposed AWS L4 envelope are in [FIRST_REAL_GPU_RUNBOOK.md](FIRST_REAL_GPU_RUNBOOK.md). Stock Step1X and TripoSG runtime paths remain rejected for the documented commercial/worldwide use because of runtime/license dependencies.

The TripoSR source/checkpoint evidence is promising. `services/generation/triposr_candidate` now ports only the reviewed marching-cubes behavior from MIT fork `vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7` onto the pinned current TripoSR source. The preparation script verifies exact upstream file blob IDs, uses `scikit-image==0.25.2`, forces a local DINO architecture config and local checkpoint, verifies checkpoint size/SHA256, requests `torch.load(..., weights_only=True)`, requires `--no-remove-bg`, and rejects hidden Hub/model downloads. The candidate base image is recorded by immutable Linux/amd64 manifest digest. This still does **not** approve or run the model.

## Still not verified

No real AI model was loaded. No real text/image generation was executed. No GPU or paid cloud resource was launched. No generated GLB has yet been proven in both the browser viewer and Blender. No public signup/password-reset/account-deletion flow is enabled. No real S3 bucket was provisioned or migrated. No billing or production deployment exists.

## Highest-value next work

1. Build and inspect the digest-pinned TripoSR candidate image; record the actual Python/CUDA/PyTorch/system-library inventory, resolve and hash the full transitive wheel set, and verify headless ModernGL/xatlas texture baking plus checkpoint `weights_only=True` loading **without running paid GPU inference**.
2. Obtain owner/legal approval for that exact source+checkpoint+runtime/data chain and the bounded AWS GPU budget in [FIRST_REAL_GPU_RUNBOOK.md](FIRST_REAL_GPU_RUNBOOK.md).
3. After those approvals, execute one real image → generation → baked texture → embedded validated GLB → product API → browser viewer → Blender import vertical slice and record timing/cost/checksums/screenshots.
4. In parallel, implement the **trusted assertion/JWKS validation half** of the identity boundary behind a disabled-by-default feature flag; the external mapping half is complete.
5. Storage lifecycle is partially hardened in PR #22: persistent per-user artifact-byte quotas and a bounded read-only missing/orphan scanner cover both filesystem and S3-compatible storage. Remaining work is explicit legacy→object migration, retention policy and an audited destructive deletion flow.

## Reproduce CPU checks

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e "./apps/gateway[test]" -e "./apps/api[test]"
python -m pytest -q apps/api/tests apps/gateway/tests
python -m compileall -q apps/api/src apps/gateway/src
python -m pip wheel --no-deps ./apps/gateway ./apps/api -w dist
python scripts/check_api_wheel.py

cd apps/web
npm install --no-audit --no-fund
npm run typecheck
npm test
npm run build
npx playwright install --with-deps chromium
npm run test:e2e
```

Do not run `build3d-worker --confirm-gpu-spend` or `build3d-gpu-smoke --confirm-gpu-spend` as routine validation.

## Owner gates for live inference

- approved provider/account, region, quota, maximum hourly/total budget and shutdown conditions;
- written engineering/legal clearance for one exact code + weight + runtime dependency chain for the intended commercial geography/use;
- private authenticated runtime that attests it is serving the approved revision/checkpoint.

These gates block live inference, not further CPU-only engineering.
