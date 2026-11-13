# Phase 0: Public Repository Reuse Audit (Partial)

**Research date:** 2026-11-13. **Status:** Code/README/license sources inspected. No GPU tests, model loading, npm build, or full dependency clearance performed.

This is the first deliverable toward [Issue #2](https://github.com/kawakaze430/build-3d-ai/issues/2). See [LICENSE_MATRIX.md](LICENSE_MATRIX.md) for the model-license deployment gate.

## Verified upstream source revisions

| Candidate | Source at audit | Examined | Current decision |
|---|---|---|---|
| [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) | `f2e403eb11a2c33077e9f353fa240974edb06981` | `README.md`, `package.json`, `LICENSE` | Frontend candidate; no installed build tested |
| [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) | `9c5643f99cbfd8d47b81922790f0d0a36be57e81` | `README.md`, `.gitmodules`, `api/routers/system.py`, `mesh_generation.py`, `file_upload.py`, `users.py`, `LICENSE` | Backend candidate; documented API integration currently tested through mocked transport |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | `cb5ac944709c6c913109070c7b90c3447f57f3d4` | `README.md` and `LICENSE` | Fine-tuning candidate, no training attempted |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | `75fbf0183001ed9876c8dbb35de6b68552ee08bd` | `README.md`, `LICENSE` | R&D only until renderer license chain resolved |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | `6793c6640ff01c8fb389f3993434124bb43d2933` | `LICENSE` | Body rigging evaluation pending |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | `273b691d35989d71cd17ff2895fdc735097b92d1` | `LICENSE` | Alternate rigging evaluation pending |

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
2. Build Open3DStudio in a clean Node environment; run its actual tests; report failures.
3. Build CPU-only backend dependencies in a clean sandbox; inspect API router contracts and security settings.
4. Select a model with permission for our full intended geographic and commercial SaaS use, including all texture/render dependencies.
5. Record realistic GPU resource needs, AWS instance access, budget and private networking plan—**do not launch paid GPUs without owner approval**.
6. Update the model policy with a reviewed exact ID and weight hash only after approval.
7. Execute image→mesh→GLB using a real GPU and evaluate format validity, UV/PBR, backside quality, elapsed time and cost.
8. Mark only verified feature tasks complete in the checklist.

## Decision so far

**Keep Open3DStudio + 3DAIGC-API as evaluation candidates and continue the narrow real-API gateway. Do not claim production commercial model approval.** The new model policy defaults to no generation until explicitly reviewed.
