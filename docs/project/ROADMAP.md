# Multi-Phase Roadmap

**Planning estimate only, not a promise.** These phases may overlap; timing depends on team size, GPU resources, code quality and license clearance.

| Phase | Focus | Target / exit gate |
|---|---|---|
| 0 | Source audit and GPU proof | 1–3 weeks: documented reuse/license decisions, working permitted inference, measured cost |
| 1 | Real basic platform | ~1–3 months: auth, job queue, viewer, GLB, image/text-to-3D, private projects |
| 2 | Commercial and production mesh tools | ~3–6 months: billing, UVs, material refinement, exports, observability, rigging beta |
| 3 | Fine-tuning, character quality and multi-reference | ~5–10 months: licensed custom model, user-tested character workflow, Blender export |
| 4 | Facial animation, scene creation, API | ~8–18+ months: validated expression/lip-sync and scene production modules |
| 5 | Competitive scale | Continuous: measured model/user experience improvements and reliability |

## Phase 0 — must happen before large spending

- Review Open3DStudio, 3DAIGC-API and AssetFurnace code, maintainer activity and actual testability.
- Audit all candidate model weights and transitive graphics dependencies for commercial deployment.
- Validate ONE real GPU pipeline image → mesh → textures → actual GLB. No placeholder inference.
- Record hardware, VRAM, elapsed time, quality from multiple views and per-job cost.
- Choose adapter approach and publish Go/No-Go decision; request owner approval for paid GPU or training.

## Phase 1 exit

Authenticated users can upload permitted content, launch a durable job, see real status/errors, inspect a real textured mesh and download verified GLB. Jobs are isolated, retried predictably, metered, and backed up. CI and deploy instructions are reproducible.

## Phase 2 exit

Usable editing and UV/material outputs; correct payments/credits; cost alerts; reliable common export formats; documented model and dependency licenses. QA beyond a one-angle screenshot.

## Phase 3 exit

Licensed training pipeline, trackable experiment and custom checkpoint that shows an actual advantage vs baseline. Character body rig and Blender import tests pass on a held-out set.

## Phase 4 exit

Face rigs demonstrate eye movement, blinks, jaw/mouth and expressions in a downstream editor; editable scene assembly works with real objects. Splats remain separately labeled from polygons.

## No false “done” statuses

Code written ≠ integrated ≠ tested ≠ deployed. Mark each feature explicitly. If a license, permission or GPU requirement blocks work, record the blocker instead of bypassing it.
