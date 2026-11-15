# Integration Decisions — Commercial Build 3D AI
Updated 2026-11-15. Research/adoption status is NOT legal clearance. Read LICENSE_MATRIX.md and TWO_PRIMARY_REPOSITORIES_DECISION.md before deployment.

## Exactly two primary study repositories

1. FishWoWater/3DAIGC-API@9c5643f99cbfd8d47b81922790f0d0a36be57e81 — SELECTIVE API CONTRACT REUSE. Existing apps/gateway integrates this contract; do not replace our own tenant API, browser identity or durable worker. Third-party submodules each require separate license/runtime approval.
2. VAST-AI-Research/TripoSR@107cefdc244c39106fa830359024f6a2f1c78871 — FIRST GPU QUALIFICATION CANDIDATE ONLY. Existing source-preparation patchset remains the baseline; no checkpoint approved or GPU run performed. Exact model revision, checkpoint digest and runtime blockers are in FIRST_REAL_GPU_RUNBOOK.md.

## Other technologies — specialized, not additional primary repos

| Technology | Decision | Engineering rationale / gate |
|---|---|---|
| Our first-party Next.js + React/Three.js studio | KEEP | Existing tested project/job/viewer UI, no need to vendor Open3DStudio |
| Our FastAPI/SQLAlchemy worker and immutable storage | KEEP | Authenticated tenant-scoped durable jobs, leases, artifact integrity; avoid reimplementation |
| xatlas and xatlas-python | KEEP CANDIDATE | UV algorithm and OBJ binding inspected, but GLB packaging is first-party and needs real bake QA |
| glTF-Transform, Khronos glTF Validator, trimesh | STUDY SPECIALIST | Prefer tested mesh processing/QA over custom algorithms; exact release/notice review still required |
| Blender | STUDY SPECIALIST | Final rig, facial control, export and validation; GPL execution/distribution boundary matters |
| UniRig / SkinTokens / Puppeteer | RESEARCH_ONLY | Evaluate skeleton, weights and motion once a real mesh baseline is available |
| AssetFurnace | SELECTIVE REFERENCE | Useful multi-stage/character workflow; NOTICE confirms different model/weight licenses |
| Open3DStudio | UX REFERENCE ONLY | React Scripts/Electron coupling and already tested original Build3D frontend |
| Stable Fast 3D | NEEDS_LICENSE_REVIEW | Gated weights; Stability Community terms include registration/revenue restrictions |
| microsoft/TRELLIS | RESEARCH_ONLY | Multi-image/quality comparison; no exact runtime approval or Build3D benchmark |
| microsoft/TRELLIS.2 | BLOCK STOCK RENDERER | nvdiffrast/nvdiffrec non-commercial issue; no commercial deployment as-is |
| Step1X-3D | REJECT STOCK COMMERCIAL RUNTIME | Published runtime dependency on noncommercial nvdiffrast |
| TripoSG | REJECT STOCK WORLDWIDE RUNTIME | BRIA RMBG-1.4 + FlashVDM/Hunyuan inherited licensing/territory risks |
| Hunyuan3D-2.1 | REJECT STOCK WORLDWIDE RUNTIME | Community license excludes intended territories |
| WorldGen, BlenderProc, Infinigen, OpenUSD | RESEARCH_ONLY | Future editable environments. Splat output is not a polygon scene |
| Gaussian splat/NeRF repos | SEPARATE FUTURE MODE | Distinct representation, GPU costs, rendering and legal gates |
| PySpine, rigby2d, Konva | OUT OF 3D SCOPE | They belong to separately discussed 2D animation product |

## Decision gates

Before importing any new code or model: (1) exact revision and license/notice, (2) weight/card and dataset usage rights, (3) renderer/CUDA/system dependency chain, (4) worldwide commercial SaaS terms, (5) relevant QA against current baseline, (6) adapter API/security contract, (7) CI and measured GPU cost, (8) rollback. Anything unknown remains RESEARCH_ONLY; anything confirmed incompatible remains blocked.

User-facing product/branding, credential ownership, database, billing and first-party differentiation remain independently controlled. Open-source technology cannot become exclusive first-party intellectual property merely by using it.
