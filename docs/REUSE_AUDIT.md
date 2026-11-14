# Phase 0: Public Repository Reuse Audit (Partial)

**Research dates:** 2026-11-13 through 2026-11-15. **Status:** Exact source revisions, representative code/package files and license/notice evidence inspected. No GPU tests, model loading or full transitive dependency clearance performed. Frontend product work now uses a first-party studio rather than vendoring Open3DStudio.

This is the first deliverable toward [Issue #2](https://github.com/kawakaze430/build-3d-ai/issues/2). See [LICENSE_MATRIX.md](LICENSE_MATRIX.md) for the model-license deployment gate.

## Verified upstream source revisions

| Candidate | Source at audit | Examined | Current decision |
|---|---|---|---|
| [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) | `f2e403eb11a2c33077e9f353fa240974edb06981` | `README.md`, `package.json`, `LICENSE`, application/API coupling | **RESEARCH_ONLY**; not selected as product frontend. ADR 0001 chose a first-party Next.js studio. |
| [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) | `9c5643f99cbfd8d47b81922790f0d0a36be57e81` | `README.md`, `.gitmodules`, `api/routers/system.py`, `mesh_generation.py`, `file_upload.py`, `users.py`, `LICENSE` | Backend candidate; documented API integration currently tested through mocked transport |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | `cb5ac944709c6c913109070c7b90c3447f57f3d4` | `README.md` and `LICENSE` | Fine-tuning candidate, no training attempted |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | `75fbf0183001ed9876c8dbb35de6b68552ee08bd` | `README.md`, `LICENSE` | R&D only until renderer license chain resolved |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | `6793c6640ff01c8fb389f3993434124bb43d2933` | `LICENSE` | Body rigging evaluation pending |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | `273b691d35989d71cd17ff2895fdc735097b92d1` | `LICENSE` | **RESEARCH_ONLY** pending weights/dependency/functional audit |
| [AssetFurnace](https://github.com/Bingeljell/image-to-3dlab) | `52b8cf560d3f4629342113b7a8b13312f4b05073` (v0.5.10 release head) | `README.md`, `pyproject.toml`, `LICENSE`, `NOTICE` | **RESEARCH_ONLY** as a whole; Apache-2.0 app code is promising, but its selectable model/encoder backends intentionally carry separate licenses |
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | `fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c` | `README.md`, `requirements.txt`, `LICENSE`, `NOTICE`, published weight card | **RESEARCH_ONLY / NEEDS_PERMISSION** for the default end-to-end path; source/main weights are MIT-labeled, but the documented pipeline auto-downloads BRIA RMBG-1.4 and NOTICE includes community-licensed derived code |
| [xatlas](https://github.com/jpcy/xatlas) | `f700c7790aaa030e794b52ba7791a05c085faf0c` | repository metadata + MIT license | **APPROVED** as a source-license candidate for UV parameterization; integration/build/quality tests still required |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | `8e2a94a2616d293c4b503d0fb6a4b42e6ec7c62f` | `package.json`, repository license metadata | **APPROVED** as a source/package candidate; active TypeScript glTF tooling, not yet integrated |
| [Three.js](https://github.com/mrdoob/three.js) | `b529cbbda2ba956a8444545a5634f6db22b68385` (repo head inspected; app pins 0.187.0) | `package.json`, `LICENSE`, test scripts | **APPROVED** for browser rendering; version 0.187.0 is already used by `apps/web` and passed product web CI |

## 15 Nov 2026 reuse/license findings

### AssetFurnace

AssetFurnace is unusually relevant as an integration/reference project because its application code is Apache-2.0 and the inspected v0.5.10 head is actively maintained. It already composes image generation, multiple 3D engines, finishing, rigging and animation rather than claiming one model solves the entire product.

It is **not** a blanket commercial shortcut. Its own NOTICE explicitly says model weights are not shipped under the app's Apache license and names separate Tencent Hunyuan, Stability, DINOv3, Qwen and other terms. The README's backend table mixes permissive and community/research-limited components. Therefore reuse should be selective: architecture ideas, provenance UX and isolated Apache-licensed code can be reviewed file-by-file; no bundled backend choice is automatically approved.

### TripoSG

The TripoSG repository is MIT at the inspected commit, and the published `VAST-AI/TripoSG` weight repository currently labels the main model MIT. That is useful evidence but still not enough to approve the documented runtime as-is.

The repository README automatically downloads `briaai/RMBG-1.4` for background removal. BRIA's published model card states RMBG-1.4 is non-commercial by default and commercial use requires a commercial agreement. TripoSG's NOTICE also records code derived from HunyuanDiT and FlashVDM under Tencent community licenses. So the **default TripoSG pipeline is not approved for this commercial SaaS**. A future evaluation may replace RMBG-1.4 with a commercially cleared preprocessor and must separately review every derived runtime component.

### Utility libraries

- **xatlas** is MIT and has no model-weight licensing layer. The inspected source head is old (2022 commit), so use should be gated by a build/quality adapter test rather than maintenance claims.
- **glTF Transform** is MIT, actively maintained at the inspected 2026 commit, and is a strong candidate for deterministic glTF inspection/optimization tasks where it saves custom code.
- **Three.js** is MIT, actively maintained, and already powers the first-party browser viewer at pinned npm version 0.187.0. Web CI validates our usage path. This does not imply every Three.js example asset/addon is licensed identically; only imported packages/code are in scope.

These statuses are engineering reuse gates, not legal advice.

## Why reuse this backend

The actual 3DAIGC-API router files expose:

- `POST /api/v1/file-upload/image`: saves an uploaded image and returns `file_id`, requiring an accepted filename extension.
- `POST /api/v1/mesh-generation/image-to-textured-mesh`: uses `image_file_id` and `model_preference`.
- `POST /api/v1/mesh-generation/text-to-textured-mesh`: accepts a prompt and model preference.
- `GET /api/v1/system/models`: model catalog; availability still depends on installed weights.
- `GET /api/v1/system/jobs/{job_id}` and `GET /api/v1/system/jobs/{job_id}/download`: job polling/output.
- `POST /api/v1/users/login` and `register`: upstream authentication mode exists, but it is **not** a substitute for our own product's secure multi-tenant accounts.

The current owner-only FastAPI gateway speaks these routes. **HTTP contract tests use in-memory responses**, not actual loaded AI weights. Do not mistake passed CI for successful GPU generation.

## Why not vendor all upstream code immediately

3DAIGC-API has many submodules/forks with separate licenses and potentially incompatible CUDA environments. Open3DStudio uses a Create React App/React Scripts + Electron toolchain; our target monorepo can adapt these components or build a new frontend based on measured maintainability. Neither choice has been signed off. Mass cloning everything would raise costs and license uncertainty.

## Step1X fine-tuning reality

Step1X-3D documents `train.py` and `system.use_lora=True`. Its README also credits code borrowed from MV-Adapter, bpy-render and Hunyuan 3D 2.0. Before training or shipping, review those dependencies, weights license, actual datasets and preprocessing requirements. A LoRA command is not proof of a trained custom model.

## Required Codex work to finish the audit

1. Clone exact revisions and record submodule SHAs, lockfiles, Python package trees and LICENSE/NOTICE files.
2. Do not spend critical-path time building Open3DStudio unless ADR 0001 is reconsidered; the product frontend is now first-party. Continue file-level reuse review only for components we actually intend to import.
3. Build CPU-only backend dependencies in a clean sandbox; inspect API router contracts and security settings.
4. Select a model with permission for our full intended geographic and commercial SaaS use, including all texture/render dependencies.
5. Record realistic GPU resource needs, AWS instance access, budget and private networking plan—**do not launch paid GPUs without owner approval**.
6. Update the model policy with a reviewed exact ID and weight hash only after approval.
7. Execute image→mesh→GLB using a real GPU and evaluate format validity, UV/PBR, backside quality, elapsed time and cost.
8. Mark only verified feature tasks complete in the checklist.

## Decision so far

**Keep 3DAIGC-API as the private serving-contract candidate, use the first-party browser studio, and selectively reuse permissive utility code. Do not claim production commercial model approval.** The new model policy defaults to no generation until explicitly reviewed.

## Private product backend reuse decision — 14 Nov 2026

Implemented a bounded first-party orchestration layer in `apps/api`; reused the existing gateway client, model policy and GLB verifier instead of adding another model adapter or renderer. No upstream AI code, model weights, viewer or mesh algorithm was rewritten or imported.

| Candidate | Actual fit / decision | Pinned release / evidence | Limit |
|---|---|---|---|
| SQLAlchemy | Reuse Core transactions, constraints and conditional updates for durable project/job state | `2.0.57`; installed package/license files inspected; [transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [SQLite behavior](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html) | SQLite for development; PostgreSQL integration and concurrency tests required |
| Alembic | Reuse versioned migration engine; freeze initial DDL independent of current application metadata | `1.20.1`; [official tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) | No automatic migrations on web-server startup; operator migration command |
| psycopg | Reuse maintained PostgreSQL driver | `3.3.9` with matching binary wheel; installed LGPL license inspected | Binary bundle and distribution obligations require release review |
| Pillow | Reuse real image parsers, size checks, orientation handling and PNG encoder | `12.3.0`; installed license and image decode tests | Decoder dependency updates and sandbox/ingress limits still matter |
| AWS SQS | Evaluated for later distributed scheduling; not provisioned in this slice | [Official at-least-once semantics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html) | A queue cannot make a non-idempotent remote generation POST safe to replay |
| Upstream account APIs | Keep private serving authentication separate from product users | Prior pinned 3DAIGC router audit above | No evidence these implement this product's owner isolation, key management or billing policy |

`requirements.lock` pins installed CPU/test release versions. [CPU_DEPENDENCY_INVENTORY.json](CPU_DEPENDENCY_INVENTORY.json) records declared licenses and hashes of installed license files. These are package release pins, not independently checked source commit SHAs, wheel-integrity locks or approval of GPU dependencies. Existing dependency notices remain in installed distributions; no library source is vendored here.

Integration work is limited to API contracts, database schema, ownership rules, a safe submission/polling state machine and private artifact storage. A maintained SQL toolkit and migration engine avoid building persistence machinery from scratch. This slice needs CPU/database/disk only; running its worker against a real backend is separately gated. Managed identity, object storage/retention, provider budgets and SQS/global scheduling remain required before public service.
