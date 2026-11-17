# Phase 0: Public Repository Reuse Audit (Partial)

Current implementation reconciliation: 17 November 2026. The [pre-review version](../../AnalyseFuture/historical-implementations/documentation-before-universal/docs/REUSE_AUDIT.md) preserves the exact document from baseline `56f412f`; historical results remain scoped to their recorded runs.

**Research dates:** 2026-11-13 through 2026-11-15. **Status:** Exact source revisions, representative code/package files and license/notice evidence inspected. No GPU tests, model loading or full transitive dependency clearance performed. Frontend product work now uses a first-party studio rather than vendoring Open3DStudio.

This is the first deliverable toward [Issue #2](https://github.com/kawakaze430/build-3d-ai/issues/2). See [LICENSE_MATRIX.md](LICENSE_MATRIX.md) for the model-license deployment gate.

## Verified upstream source revisions

| Candidate | Source at audit | Examined | Current decision |
|---|---|---|---|
| [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) | `f2e403eb11a2c33077e9f353fa240974edb06981` | `README.md`, `package.json`, `LICENSE`, application/API coupling | **RESEARCH_ONLY**; not selected as product frontend. ADR 0001 chose a first-party Next.js studio. |
| [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) | `9c5643f99cbfd8d47b81922790f0d0a36be57e81` | `README.md`, `.gitmodules`, `api/routers/system.py`, `mesh_generation.py`, `file_upload.py`, `users.py`, `LICENSE` | Backend candidate; documented API integration currently tested through mocked transport |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | `cb5ac944709c6c913109070c7b90c3447f57f3d4` | `README.md`, `LICENSE`, published runtime requirements/model card | **REJECTED standard runtime path** for worldwide commercial deployment: published requirements include nvdiffrast, whose license is non-commercial; alternative renderer path would need a fresh audit |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | `75fbf0183001ed9876c8dbb35de6b68552ee08bd` | `README.md`, `LICENSE` | R&D only until renderer license chain resolved |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | `6793c6640ff01c8fb389f3993434124bb43d2933` | `LICENSE` | Body rigging evaluation pending |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | `273b691d35989d71cd17ff2895fdc735097b92d1` | `LICENSE` | **RESEARCH_ONLY** pending weights/dependency/functional audit |
| [AssetFurnace](https://github.com/Bingeljell/image-to-3dlab) | `52b8cf560d3f4629342113b7a8b13312f4b05073` (v0.5.10 release head) | `README.md`, `pyproject.toml`, `LICENSE`, `NOTICE` | **RESEARCH_ONLY** as a whole; Apache-2.0 app code is promising, but its selectable model/encoder backends intentionally carry separate licenses |
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | `fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c` | `README.md`, `requirements.txt`, `LICENSE`, `NOTICE`, inference preprocessing, published weight card | **REJECTED default worldwide runtime path**: source/main weights are MIT-labeled, but the CLI auto-downloads non-commercial BRIA RMBG-1.4 and NOTICE includes FlashVDM/Hunyuan-derived code with geographic community-license restrictions |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR) | `107cefdc244c39106fa830359024f6a2f1c78871`; model repo `stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08` | source/requirements/run path, MIT license/model card, model hash, DINO config, xatlas texture path | **RESEARCH_ONLY / first GPU qualification candidate**; top-level evidence is promising, but deterministic marching-cubes dependency and full runtime/data release clearance remain open |
| [TripoSR-scikit](https://github.com/vltmedia/TripoSR-scikit) | `fa39422b81217687f16efe7bb3afc136feb87ba7` | MIT fork + exact two-commit diff vs 2024 merge base | **SELECTIVE_REUSE_ONLY**: useful scikit-image marching-cubes patch evidence, but 17 commits behind current upstream; do not base the product runtime on the whole fork |
| [xatlas](https://github.com/jpcy/xatlas) | `f700c7790aaa030e794b52ba7791a05c085faf0c` | repository metadata + MIT license | **APPROVED** as a source-license candidate for UV parameterization; integration/build/quality tests still required |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | `8e2a94a2616d293c4b503d0fb6a4b42e6ec7c62f` | `package.json`, repository license metadata | **APPROVED** as a source/package candidate; active TypeScript glTF tooling, not yet integrated |
| [Three.js](https://github.com/mrdoob/three.js) | `b529cbbda2ba956a8444545a5634f6db22b68385` (repo head inspected; app pins 0.187.0) | `package.json`, `LICENSE`, test scripts | **APPROVED** for browser rendering; version 0.187.0 is already used by `apps/web` and passed product web CI |

## 15 Nov 2026 reuse/license findings

### AssetFurnace

AssetFurnace is unusually relevant as an integration/reference project because its application code is Apache-2.0 and the inspected v0.5.10 head is actively maintained. It already composes image generation, multiple 3D engines, finishing, rigging and animation rather than claiming one model solves the entire product.

It is **not** a blanket commercial shortcut. Its own NOTICE explicitly says model weights are not shipped under the app's Apache license and names separate Tencent Hunyuan, Stability, DINOv3, Qwen and other terms. The README's backend table mixes permissive and community/research-limited components. Therefore reuse should be selective: architecture ideas, provenance UX and isolated Apache-licensed code can be reviewed file-by-file; no bundled backend choice is automatically approved.

### TripoSG

The TripoSG repository is MIT at the inspected commit, and the published `VAST-AI/TripoSG` weight repository currently labels the main model MIT. That is useful evidence but still not enough to approve the documented runtime as-is.

The stock CLI downloads and instantiates `briaai/RMBG-1.4`; BRIA's published model card states RMBG-1.4 is non-commercial by default and commercial use requires a commercial agreement. Inspection of `scripts/image_process.py` confirms a valid RGBA alpha channel can avoid the RMBG inference call, so the model dependency is technically replaceable.

That is **not sufficient** to clear the current source tree. TripoSG's NOTICE records derived code from HunyuanDiT and FlashVDM. The current Tencent Hunyuan FlashVDM community license limits the territory to worldwide **excluding the EU, UK and South Korea**; HunyuanDiT's community license also has territory/use conditions. The intended product is not scoped to those exclusions. Therefore the inspected default TripoSG runtime is **REJECTED for worldwide commercial deployment**, not merely awaiting a model-card check. A future fork may be re-evaluated only if the restricted derived components and RMBG path are demonstrably removed/replaced and the resulting exact tree is audited from scratch.

### TripoSR

TripoSR is the first audited model in this pass whose top-level source and published checkpoint are both MIT-labeled without the already-known nvdiffrast or Tencent territory blocker. The pinned model repository is `2ba2f5591f8eb0821784764ab9ab99a12e1abb08`; its `model.ckpt` is 1,677,246,742 bytes with SHA256 `429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee`. The model card says training used a curated Objaverse subset available under CC-BY. This is useful evidence, but still requires owner/legal review of the exact data/runtime chain before commercial approval.

The source config refers to `facebook/dino-vitb16`; the candidate runbook pins its config to revision `fdc136b8ef48f5a94159af5dd6323ae7a219697a`, whose repository is Apache-2.0. The TripoSR state dict is loaded from the pinned TripoSR checkpoint, but the config fetch must still be revision-pinned for deterministic execution.

Two stock-runtime problems were found:

1. `requirements.txt` uses an unpinned Git URL for torchmcubes. The historical pre-release snapshot inspected around TripoSR's release did not contain a repository license file, so it is not being frozen as a commercial dependency. A known MIT fork, `vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7`, replaces torchmcubes with scikit-image and adjusts face winding. Because that fork is 17 upstream commits behind, reuse should be limited to porting/retesting that small change onto current TripoSR. Qualification pin: `scikit-image==0.25.2` (BSD-3-Clause, Python >=3.10), chosen to fit the conservative candidate PyTorch environment. The Build3D patchset now ports only this marching-cubes behavior onto the pinned current TripoSR source with exact source-blob guards and CPU axis/winding tests.
2. With `--bake-texture`, stock `run.py` calls xatlas-python `export()`. Inspection of xatlas-python v0.0.9 commit `ff6541ec7ed1b5131dd7bf5447da6174e6c82621` shows that helper always writes OBJ text, even if a caller chooses a `.glb` suffix. The project therefore added a first-party, strict OBJ+PNG → embedded PBR GLB packager rather than claiming stock textured-GLB support.

The candidate remains **RESEARCH_ONLY**. The deterministic **source patchset** is now implemented, including local-only configs/checkpoint verification and hidden-download guards, but the full candidate image/transitive wheel/system-library inventory, owner/legal verdict and real GPU/browser/Blender qualification are still incomplete. See [FIRST_REAL_GPU_RUNBOOK.md](../operations/FIRST_REAL_GPU_RUNBOOK.md).

### Utility libraries

- **xatlas** is MIT and has no model-weight licensing layer. The inspected C/C++ source head is old (2022 commit), so use should be gated by a build/quality adapter test rather than maintenance claims. The TripoSR path specifically pins the separate MIT xatlas-python v0.0.9 binding at `ff6541ec7ed1b5131dd7bf5447da6174e6c82621`; only its narrow OBJ output contract is relied on.
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

3DAIGC-API has many submodules/forks with separate licenses and potentially incompatible CUDA environments. Open3DStudio uses a Create React App/React Scripts + Electron toolchain; ADR 0001 has already selected the existing first-party Next.js frontend. Reconsider individual upstream components only after file-level review, rather than reopening the foundation decision by default. Supplied raw source snapshots are preserved under `AnalyseFuture/` for review and are excluded from normal runtime/test/build paths. Mass integration would raise costs and license uncertainty.

## Step1X fine-tuning reality

Step1X-3D documents `train.py` and `system.use_lora=True`. Its README also credits code borrowed from MV-Adapter, bpy-render and Hunyuan 3D 2.0. Before training or shipping, review those dependencies, weights license, actual datasets and preprocessing requirements. A LoRA command is not proof of a trained custom model.

## Required Codex work to finish the audit

1. Clone exact revisions and record submodule SHAs, lockfiles, Python package trees and LICENSE/NOTICE files.
2. Do not spend critical-path time building Open3DStudio unless ADR 0001 is reconsidered; the product frontend is now first-party. Continue file-level reuse review only for components we actually intend to import.
3. Build CPU-only backend dependencies in a clean sandbox; inspect API router contracts and security settings.
4. Finish the TripoSR candidate runtime audit/fork or reject it; permission must cover the full intended geographic and commercial SaaS use, training-data/model terms, marching-cubes and texture/render dependencies.
5. Record realistic GPU resource needs, AWS instance access, budget and private networking plan—**do not launch paid GPUs without owner approval**.
6. Update the model policy with a reviewed exact ID and weight hash only after approval.
7. Execute image→mesh→GLB using a real GPU and evaluate format validity, UV/PBR, backside quality, elapsed time and cost.
8. Mark only verified feature tasks complete in the checklist.

## Decision so far

**Keep 3DAIGC-API as the private serving-contract candidate, use the first-party browser studio, and selectively reuse permissive utility code. Do not claim production commercial model approval.** The new model policy defaults to no generation until explicitly reviewed.

## Private product backend reuse decision — 14 Nov 2026

Implemented a bounded first-party orchestration layer in `apps/api`; reused the existing gateway client, model policy and GLB verifier instead of adding another model adapter or renderer. No upstream AI code, model weights, viewer or mesh algorithm was rewritten or imported into that product runtime change. Later raw archive snapshots in `AnalyseFuture/` are preserved references, not active runtime integration.

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

## Trusted JWT validation reuse decision — 15 Nov 2026

Reuse PyJWT `2.15.1` and pyca/cryptography rather than implementing JOSE signature verification. The Build3D layer adds only provider policy, bounded no-redirect JWKS retrieval/caching, immutable product-owner resolution and database-backed credential rate limiting. No automatic OIDC discovery is used. Symmetric HS* algorithms are not accepted for this trust boundary.


## Recovered dependency-evidence reuse — 17 November 2026

The earlier branch's pip-report auditor and nine fixture tests are recovered into `services/generation/triposr_candidate/`, alongside the preparation code whose direct dependency pins they inspect. This reuses existing work instead of introducing a competing dependency-audit implementation. The tool consumes a separately produced pip JSON report and exact direct requirements, rejects untrusted artifact URLs and inconsistent pins, and records source-archive blockers.

Index-reported artifact hashes are metadata evidence, not independent wheel-byte verification. A green metadata audit does not close the complete wheelhouse, binary/OS notices, candidate-image, checkpoint, model-data rights or GPU qualification gates. Current validation belongs in the [audit validation report](../../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt); historical resolved package counts must remain scoped to the platform/report that produced them.
