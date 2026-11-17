# Developer handoff — 15 November 2026

## Current direct-main expansion checkpoint — 17 November 2026

The owner now requires small verified milestones pushed directly to origin/main,
superseding prior PR/branch instructions. Starting fetched main for this update:
`7992107b613c680dee2a750045b6b7e1ff42e581` (the verified prior handoff delivery).
The expanded goal covers image/text/multi-image assets AND environments, geometry,
materials,rigs/motion,AI agents and future fine-tuning. Read the updated root
[task handoff](../../PROJECT_STATUS_AND_TASKS.md) and new [research.md](../../research.md).
This milestone adds the core vision and15research cards; detailed capability,
structure/testing expansion follows as the next documentation checkpoint. No new
runtime tests,inference or training ran. Existing253test executions remain dated.
Update goal/research/README/navigation/inventories and preservation hashes together;
the actual containing SHA is discoverable via Git,then recorded in the following
verified checkpoint. Existing28software tasks remain open;WEB-01 or RES-01/02 CPU
charter/recipe research are useful next work. No continuous watcher is configured.


## Current execution handoff — 17 November 2026

Start with [PROJECT_STATUS_AND_TASKS.md](../../PROJECT_STATUS_AND_TASKS.md) for
the source-reconciled feature status, every-file/folder guide, 28 scoped task
cards, 14 later workstreams and acceptance/review requirements. The next tool
should open focused PRs; the recommended first task is WEB-01 polling and stale
completion correctness. This documentation adds no runtime feature or new test
result. PRs can be brought to Codex for review in an active session; no continuous
watcher is configured. Current PR/check metadata still needs an authorized live
interface rather than an inferred status from historical notes.

## Post-restructure validation authorized — 17 November 2026

The owner subsequently requested **“pls test all”**, lifting the earlier pause.
All available local first-party suites now pass after correcting Vitest's missing
`@/` alias. See the [current validation report](../../AnalyseFuture/validation/2026-11-17/REPORT.md)
for counts, the initial regression, runtime checks and infrastructure limits.
Earlier no-tests notes below are historical migration records, not a current ban.


## Historical restructuring snapshot — 17 November 2026

During this phase the owner deferred tests, before the later authorization above.
The complete
functional reorganization moves 45 files (42 starting tracked,3 newly authored) into
project/architecture/development/operations/research/continuity documentation,
Compose infrastructure, identity configuration, packaging helpers and web
studio/assets/jobs/client/server collections. Existing package/publicHTTP/schema
boundaries remain. All original content and earlier recovery work are preserved.

Read [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md), the
[complete inventory](../../AnalyseFuture/COMPLETE_FILE_INVENTORY.txt),
[feature inventory](../../AnalyseFuture/FEATURE_INVENTORY.txt),
[path mapping](../../AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt) and
[validation record](../../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt).
At that delivery, tests preceded the final moves and final-layout validation
was deferred. That restructuring delivery used `[skip ci]` and an ordinary main
push without force or history rewrite. Refer to the delivery receipt/Git refs
for actual publication evidence rather than inferring success from a plan.


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

- Browser: first-party Next.js/React/Three.js rather than vendoring Open3DStudio. See [ADR 0001](../architecture/adr/0001-web-studio-foundation.md).
- Storage: filesystem default + optional S3-compatible backend; no public object URLs yet. See [OBJECT_STORAGE.md](../operations/OBJECT_STORAGE.md).
- Public identity: Better Auth is the preferred candidate. Immutable external-identity mapping is now implemented; the remaining gate is short-lived cryptographically verified issuer/audience-bound BFF→API identity plus full account lifecycle. See [IDENTITY_AND_ACCOUNT_LIFECYCLE.md](../architecture/IDENTITY_AND_ACCOUNT_LIFECYCLE.md).
- Upstream model policy: zero production models approved by default.
- Non-idempotent upstream generation POSTs: never automatically replay an uncertain submission.

## Current first-GPU candidate

TripoSR is the current **qualification candidate**, not an approved production model. Pinned evidence and the proposed AWS L4 envelope are in [FIRST_REAL_GPU_RUNBOOK.md](../operations/FIRST_REAL_GPU_RUNBOOK.md). Stock Step1X and TripoSG runtime paths remain rejected for the documented commercial/worldwide use because of runtime/license dependencies.

The TripoSR source/checkpoint evidence is promising. `services/generation/triposr_candidate` now ports only the reviewed marching-cubes behavior from MIT fork `vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7` onto the pinned current TripoSR source. The preparation script verifies exact upstream file blob IDs, uses `scikit-image==0.25.2`, forces a local DINO architecture config and local checkpoint, verifies checkpoint size/SHA256, requests `torch.load(..., weights_only=True)`, requires `--no-remove-bg`, and rejects hidden Hub/model downloads. The candidate base image is recorded by immutable Linux/amd64 manifest digest. This still does **not** approve or run the model.

## Still not verified

No real AI model was loaded. No real text/image generation was executed. No GPU or paid cloud resource was launched. No generated GLB has yet been proven in both the browser viewer and Blender. No public signup/password-reset/account-deletion flow is enabled. No real S3 bucket was provisioned or migrated. No billing or production deployment exists.

## Highest-value next work

1. Build and inspect the digest-pinned TripoSR candidate image; record the actual Python/CUDA/PyTorch/system-library inventory, resolve and hash the full transitive wheel set, and verify headless ModernGL/xatlas texture baking plus checkpoint `weights_only=True` loading **without running paid GPU inference**.
2. Obtain owner/legal approval for that exact source+checkpoint+runtime/data chain and the bounded AWS GPU budget in [FIRST_REAL_GPU_RUNBOOK.md](../operations/FIRST_REAL_GPU_RUNBOOK.md).
3. After those approvals, execute one real image → generation → baked texture → embedded validated GLB → product API → browser viewer → Blender import vertical slice and record timing/cost/checksums/screenshots.
4. Trusted assertion/JWKS validation is merged and remains disabled by default. The next identity layer is Better Auth browser/session lifecycle in a dedicated staging database, with signup/verification/reset/logout/deletion and CSRF/session-rotation tests before public enablement.
5. Storage lifecycle now has merged persistent byte quotas, read-only inventory scanning and verified copy-only filesystem→S3 migration. The web studio also surfaces used/limit/remaining quota and near-limit warnings. Remaining storage work is retention policy, customer/operator deletion semantics, audit logging for destructive actions and eventual removal of verified legacy copies.

## Reproduce CPU checks

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e "./apps/gateway[test]" -e "./apps/api[test]"
python -m pytest -q apps/api/tests apps/gateway/tests
python -m compileall -q apps/api/src apps/gateway/src
python -m pip wheel --no-deps ./apps/gateway ./apps/api -w dist
python scripts/packaging/check_api_wheel.py

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


## Archive organization — 17 November 2026

Historical paths in this section were subsequently relocated under `AnalyseFuture/`; see [the current structure](../../PROJECT_STRUCTURE.md).

The owner's archive extraction request uses these paths:

- `third_party/3daigc-api/`: supplied 3DAIGC-API source, with its original license and internal layout.
- `third_party/triposr/`: supplied TripoSR source, with its original license and internal layout.
- `assets/reference/autorig/`: example bundle, preserving its model, demo and diagram hierarchy.

The three root ZIP files are removed after extraction verification. Existing first-party application/service paths stay in place. See [source snapshot notes](../../AnalyseFuture/third_party/README.md), [reference asset notes](../../AnalyseFuture/assets/reference/README.md) and [archive inventory](../../AnalyseFuture/repository-inventory/ARCHIVE_IMPORTS.json).

Treat all imported files as **RESEARCH_ONLY**. The source snapshots are independent references, not newly enabled product integrations. The 3DAIGC-API archive omits its declared submodule source, and the example bundle has no supplied license. No model approval or inference result follows from this organization change. The owner explicitly requested a direct `main` update without a PR or additional branch; verify live Git state before subsequent work.

Validation for this organization change: all 241 extracted file hashes matched the supplied ZIPs; all 240 content files matched the staged Git blobs (only macOS `.DS_Store` remains ignored). The 136 first-party Python tests, four web unit tests and TypeScript check passed. Imported source and model assets were not executed.


## Session preservation and next resume — 17 November 2026

The owner requested preservation of useful session work directly on `main` before the workspace is lost, with other development deferred. Archive extraction and organization were already pushed in commit `b32f88a`. The files below preserve the subsequent planning and environment work.

- [BUILD_3D_AI_PROJECT_IDEA.txt](../project/BUILD_3D_AI_PROJECT_IDEA.txt) preserves the detailed product concept, implemented foundation, proposed capabilities, near-term priorities, hard limits, conditional one-/two-/later-year horizons and responsible roles. Future capabilities remain proposals, not completed implementation, external commitments or spending authorization.
- [CLOUD_DEVELOPMENT_ENVIRONMENT.md](../development/CLOUD_DEVELOPMENT_ENVIRONMENT.md) records how to recreate the development workflow. Its repository helpers are [install.sh](../../scripts/cloud/install.sh), [run_web.py](../../scripts/cloud/run_web.py) and [playwright.config.cjs](../../scripts/cloud/playwright.config.cjs).

A Git backup does not retain running services, installed dependencies, caches or private smoke-test credentials. Restore dependencies and restart services using the guide; regenerate private test credentials when needed without committing or printing their values. Preserve any actual private application data through an appropriate private backup separately.

On resume, inspect live source and Git state, follow the development guide, and prioritize qualification of one genuine generation-to-textured-GLB-to-Blender workflow. Existing exact model/runtime rights, dependency verification and explicit bounded GPU budget gates still apply.

Preservation validation: the relocated web wrapper passed TypeScript checks and all six browser contract tests using the retained system-Chromium configuration. The installer passed `bash -n`, and the browser configuration passed `node --check`; the installer was not rerun end-to-end for this save. The project idea copy matched its original SHA256 (`03382c3d8c373253713f2aef266403db3f675bcfcbd8b5070d22d7f4a55ae2d9`). Generated Next.js file changes were restored.

## Main project goal adopted — 17 November 2026

The owner designated [BUILD_3D_AI_PROJECT_IDEA.txt](../project/BUILD_3D_AI_PROJECT_IDEA.txt) as the repository's main project goal and requested a direct `main` update. The README now presents it prominently, and agent instructions and the concise product vision point to it as the primary product direction. This supersedes its earlier status as an unadopted planning proposal, while future features, timing, acceptance and spending remain subject to their stated decisions and gates. Build on the existing implementation and prioritize a focused real-generation qualification before broader expansion.

## Preservation-first structure review — 17 November 2026

The owner reported compromised access and disrupted files, and requested a direct `main` restructure preserving uncertain material in `AnalyseFuture/`. The inspected local and remote main matched previously verified `e4b05f4`; no later main-branch changes were observed. This is not a conclusion about GitHub account access or an independent compromise clearance.

All 242 tracked reference files from `third_party/` and `assets/reference/` were preserved under the corresponding paths in `AnalyseFuture/`. All 240 source/asset files retain their hashes; original copies of the two navigation notes are also retained under `AnalyseFuture/history/`. Active app, qualification service, script, Compose and dependency paths remain compatible. The file index, archive relocation records, [structure guide](../../PROJECT_STRUCTURE.md) and [dated audit](../../AnalyseFuture/recovery-notes/REPOSITORY_AUDIT_2026-11-17.md) document the move and its limits. Default pytest discovery and root Docker context exclude the inactive review area.

The [main project goal TXT](../project/BUILD_3D_AI_PROJECT_IDEA.txt) now includes a structure-review addendum while preserving the detailed vision, existing work, limitations, one-/two-/longer-year horizons and roles. The first real qualified generation/browser/Blender workflow remains the next gated priority; reference relocation does not grant model or spending approval.

Structure-review validation: 136 default first-party Python tests, three preparation-helper tests, four web unit tests, six browser contracts, TypeScript checks, the production web build and both Compose configuration checks passed. File-hash checks retained all 242 original tracked references and all 241 extracted local files (one ignored metadata file); reference scripts/weights were not executed. See the dated audit for boundaries.
