# Current State Audit — Build 3D AI
Date: 2026-11-15
Baseline reviewed: main at 477b3bff3fd5449dba1d1dd7a9e4e062f99856a3
Method: read the main-branch tree, key source modules, existing tests, CI workflows, and PR/Actions metadata. This is a targeted source-level audit, not a completed penetration test, runtime deployment audit or every-line review.

## Architecture and actual integration path

Browser (apps/web/src/components/studio.tsx and model-viewer.tsx)
  -> Next.js BFF (apps/web/src/app/api/session and api/product/... routes)
  -> tenant API (apps/api/src/build3d_api/main.py; owner-scoped Bearer API keys)
  -> SQLAlchemy store + Alembic migrations (store.py, db.py, migrations/)
  -> durable fenced worker (worker.py; source job and image kept in DB)
  -> private gateway (apps/gateway/src/build3d_gateway/main.py, upstream.py)
  -> configured 3DAIGC-compatible model service (NOT running in CI)
  -> bounded GLB preflight (download.py, glb_validation.py)
  -> filesystem or optional S3-compatible artifact storage (storage.py)
  -> checked private API download -> existing Three.js/R3F GLB viewer

This integration is implemented as CPU/HTTP contracts and mock-backend tests. No genuine model inference has traversed the complete path. The gateway is operator-only; the customer API does not expose arbitrary upstream job IDs or model selection.

## Verified source-level components

| Component | Actual code | State / evidence |
|---|---|---|
| Web studio | apps/web/src/components/studio.tsx; lib/api.ts; BFF routes | IMPLEMENTED; typecheck, Vitest, Next build and Playwright contract tests in Web Studio CI on previous main |
| GLB viewer | apps/web/src/components/model-viewer.tsx | IMPLEMENTED; synthetic GLB browser contract only, no real AI-generated model proof |
| Private API keys and projects | apps/api/src/build3d_api/main.py, store.py | IMPLEMENTED/TESTED; no public signup/reset/deletion |
| Durable jobs and fencing | apps/api/src/build3d_api/worker.py, store.py | IMPLEMENTED/TESTED; real GPU backend unproven |
| Trusted external identity | apps/api/src/build3d_api/trusted_identity.py; migrations 0002/0004 | IMPLEMENTED but DISABLED BY DEFAULT; Better Auth browser lifecycle incomplete |
| Artifact quotas, inventory and copy-only migration | apps/api/storage.py, maintenance.py, migrations/0003 | IMPLEMENTED/TESTED; no automated destructive retention policy |
| Operator gateway | apps/gateway/main.py, upstream.py, model_policy.py | IMPLEMENTED/TESTED with transport fixtures; no approved production model |
| Structural GLB validator + packaging | apps/gateway/glb_validation.py, textured_glb.py | IMPLEMENTED/TESTED on synthetic bytes; not full geometry/PBR/Blender quality |
| TripoSR exact source patch | services/generation/triposr_candidate/prepare_runtime.py | IMPLEMENTED/CI-TESTED without checkpoint/GPU; external source pinned and modified blobs guarded |
| Image/text/multi-image generation | Gateway API contract; model backend not provisioned | REAL INFERENCE BLOCKED; text and image-to-3D acceptance not met |
| Auto-rigging, face, lip-sync, scene authoring | No production feature modules in main | PLANNED; study candidates only |
| Commercial accounts, payments, SaaS deployment | No complete public identity/billing/production infrastructure | NOT DEPLOYED |

## Tests actually observed

- Before the catalog commit, main b149ac390f1e118738536633cde22d7eea7598fe had successful Gateway CI, Product API CI, Web Studio CI and TripoSR Qualification CI workflows.
- On catalog commit 477b3bff3fd5449dba1d1dd7a9e4e062f99856a3, the path-triggered Gateway CI and Product API CI completed successfully.
- Existing TripoSR CI clones upstream SHA 107cefdc244c39106fa830359024f6a2f1c78871, runs guarded source patch, compiles, performs pip dry-run and CPU marching-cubes tests. It does NOT build the candidate Docker image.
- In this work session, eight new dependency-audit unit tests ran locally with Python 3.12 stdlib unittest and passed. They are synthetic metadata contract tests; GitHub's Python 3.10 PR workflow is the additional requested validation.
- No real GPU, CUDA inference, model checkpoint loading, external S3 bucket, Blender import of generated content or payment processing was executed.

## Current PR and branch state at audit

- 16 historical PRs on this repository: 13 merged, three closed/superseded (#11–#13, consolidated through #14), no open PRs before this new work branch.
- Main is not branch-protected in the observed GitHub branches endpoint; this is a governance risk for direct code pushes. Prefer review + required CI for implementation.
- Main retains 16 old development branches. Their existence does not mean their PRs remain open.
- Branch for this work: research/triposr-resolved-dependency-audit (PR under review; not merged).

## Important documentation discrepancies

- docs/ARCHITECTURE.md still describes the browser UI and S3 as proposed or absent in its 14 Nov status paragraph. Main now contains both a browser studio and an optional S3-compatible adapter. Read the more recent CODEX_HANDOFF/PRODUCT_BACKBONE/OBJECT_STORAGE and source first.
- Some checklist's broad Phase 1 items remain unchecked even though subsets are done. This is correct for their broader public-release acceptance criteria; do not mark them complete just because private tests pass.
- Model approval defaults to empty even though TripoSR source patch code exists. This is intentional and must remain fail-closed.

## Critical blockers (dependency order)

1. Exact TripoSR candidate image build, runtime package/wheel provenance and OS-library/license inventory; currently lacks a built image digest and byte-verified offline wheelhouse.
2. Headless ModernGL/xatlas texture bake and strict local-only checkpoint load at the approved source/weight revision.
3. Formal owner/legal signoff for source, weights, training data, transitive dependencies and intended worldwide SaaS use.
4. Owner approval of GPU provider/region/quota/hourly and total budget before any paid GPU execution.
5. One genuine image -> texture -> validated GLB -> private API -> browser preview -> Blender import, with timings/VRAM/cost/checksums.
6. Public identity/session lifecycle, billing/ledger, deployment, monitoring and retention for commercial launch.
7. Multiview, professional retopology/PBR editing, reusable adult character facial rigs/motions, scene authoring, fine-tuning.

## Reuse boundary to preserve

Do not rewrite the private product API, tenant authorization, durable worker, owned browser studio, GLB validator or storage abstraction. Add adapters or separately pinned GPU services. The two primary study repositories and shortlist are in TWO_PRIMARY_REPOSITORIES_DECISION.md; the ordered path is in EXECUTION_PLAN.md.

This report records source-level inspection and CI observations only. It does not certify production readiness or legal permission.
