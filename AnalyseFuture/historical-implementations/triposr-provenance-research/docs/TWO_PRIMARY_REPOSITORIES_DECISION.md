# Exactly Two Primary Repositories — Research Decision (2026-11-15)

Status: engineering shortlist/decision, NOT commercial model approval or proof of GPU inference.

## Research method and 112-entry inventory

The entire 112-entry catalog in OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt was screened for role, GitHub-reported license, archival/last activity and fit to existing Build3D. This is **metadata filtering, not deep code or license audit of 112 projects**. Exact revisions and existing findings were cross-checked against LICENSE_MATRIX.md and REUSE_AUDIT.md. Fresh source-level inspections were performed for 3DAIGC-API, TripoSR, AssetFurnace, TRELLIS.2 and Stable Fast 3D. For other candidates only the earlier pinned source audits or published docs were used.

All 112 entries fall into these study tracks: application orchestration; image/text/multiview generation; visual preprocessing; mesh/UV/PBR/GLB; skeleton and skinning; facial/lip-sync/audio; world generation and Gaussian splats; browser editor/viewer; SaaS backend/storage/security/CI; model training and GPU infrastructure. The .txt catalog provides URL, purpose, priority, maintenance metadata and preliminary license warnings for EACH candidate.

### Comparative scorecard: 12 finalists

Weights: existing fit 20%, capability 20%, commercial feasibility 20%, maturity 15%, GPU/cost envelope 10%, integration effort 10%, extensibility 5%. Each dimension scored 0–5, rescaled to /100. Scores are engineering triage estimates, not benchmarks; actual quality and VRAM remain unknown until measured. A stock runtime with a confirmed incompatible license is disqualified regardless of score.

| Candidate | Score | Result |
|---|---:|---|
| FishWoWater/3DAIGC-API | 69 | **PRIMARY #1: compatible API/orchestration contract** |
| VAST-AI-Research/TripoSR | 68 | **PRIMARY #2: first guarded image-to-3D qualification** |
| Bingeljell/image-to-3dlab (AssetFurnace) | 59 | Selective multi-stage workflow comparison |
| Stability-AI/stable-fast-3d | 58 | Revenue/registration/weight terms need permission analysis |
| microsoft/TRELLIS | 55 | Benchmark R&D, runtime license chain not cleared |
| VAST-AI-Research/SkinTokens | 54 | Specialized skinning research, not primary generator |
| VAST-AI-Research/UniRig | 53 | Specialized body rigging research |
| microsoft/TRELLIS.2 | 47 | Stock renderer commercial path blocked |
| VAST-AI-Research/TripoSG | 46 | Stock worldwide SaaS runtime rejected |
| FishWoWater/Open3DStudio | 45 | First-party Next.js already replaces its core UI role |
| stepfun-ai/Step1X-3D | 44 | Stock nvdiffrast commercial path rejected |
| Tencent-Hunyuan/Hunyuan3D-2.1 | 44 | Community territory restrictions block worldwide service |

The shortlist intentionally includes specialized rigs as candidate comparisons, not as extra primary repositories.

## PRIMARY REPOSITORY #1 — FishWoWater/3DAIGC-API

GitHub: https://github.com/FishWoWater/3DAIGC-API
Reviewed SHA: 9c5643f99cbfd8d47b81922790f0d0a36be57e81
License: top-level Apache-2.0. Third-party submodules and their weights/dependencies have INDEPENDENT licenses; none are blanket approved.

**Observed source:** api/routers/mesh_generation.py contains typed text/image/textured-mesh requests, feature/model validation and job submission. api/routers/system.py defines backend status/model/job contracts. api/routers/auto_rigging.py contains a separate FBX-only auto-rigging response path, not proof of a tested facial rig. .gitmodules at this SHA names TRELLIS, PartField, PartPacker, Hunyuan3D-2.1, UniRig, PartUV, TRELLIS.2 and more separately licensed backends.

**Why chosen:** apps/gateway/src/build3d_gateway/upstream.py ALREADY implements a small compatible subset of this API. It is the fastest way to preserve our own FastAPI tenant service and independent browser studio while gaining a stable model-job adapter contract. This is a study/adaptation of contracts, not a plan to vendor all its source or install restricted submodules.

**Modules to study selectively:** api/routers/mesh_generation.py, system.py, api/dependencies.py, core/scheduler interfaces and file-store contracts. Keep our own model allowlist, owner-scoped authorization, durable fenced worker, rate limiting and GLB validators. Avoid upstream public registration, unrestricted file paths, user-selected arbitrary checkpoints and automatic loading of unreviewed submodules.

**Next integration:** add an exact-model attestation and private model service that speaks a reviewed submit/poll/download contract; normalize errors and artifact size limits. Typical scope: ~2–5 engineer-days after model runtime exists, excluding upstream license audits. Acceptance: two-way API contract tests, blocked unknown models, no cross-tenant job access, one genuine approved backend run and validated GLB proof. Risk: upstream submodules may bring restricted code, memory limits, security and CUDA conflicts.

## PRIMARY REPOSITORY #2 — VAST-AI-Research/TripoSR

GitHub: https://github.com/VAST-AI-Research/TripoSR
Reviewed SHA: 107cefdc244c39106fa830359024f6a2f1c78871
Checkpoint revision: stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08
Checkpoint SHA256: 429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee
Checkpoint bytes: 1,677,246,742
License: MIT top-level source and published weight-card label; curated Objaverse CC-BY data description; transitive/runtime/data commercial clearance remains OPEN.

**Observed source:** run.py implements single-image preprocessing, TSR.from_pretrained, shape extraction and optional xatlas texture baking. tsr/system.py handles pretrained config/checkpoint, tsr/models/isosurface.py extracts geometry, tsr/models/tokenizers/image.py initializes DINO. Stock requirements.txt includes unpinned Git torchmcubes, rembg and Gradio; the stock code can load remote assets. Stock xatlas export path is OBJ-oriented and does not guarantee a valid textured GLB solely from naming the file .glb.

**Why chosen:** a narrowly testable, pinned first-generation checkpoint and source path with a credible commercial research case, lower integration risk than already-blocked high-end stock runtimes. Our existing services/generation/triposr_candidate/prepare_runtime.py guards source blobs, fixes local-only model/config, replaces torchmcubes with scikit-image, disables hidden first-run downloads. Our gateway textured_glb.py creates self-contained GLB from reviewed OBJ + PNG inputs and tests structural integrity.

**Modules to study selectively:** run.py, tsr/system.py, tsr/models/isosurface.py, tsr/bake_texture.py, tsr/models/tokenizers/image.py. Do not use stock unpinned torchmcubes, arbitrary weights, hidden model downloads or unverified texture export.

**Next integration:** inventory exact transitive wheels/OS libraries; build the image by digest; verify headless ModernGL/xatlas; load the exact local checkpoint using weights_only; gain owner/legal and capped cloud authorization; run one REAL image -> textured GLB -> gateway -> private tenant API -> browser viewer -> Blender, recording SHA/VRAM/time/cost. Roughly 3–10 engineer-days after approvals, with high uncertainty in CUDA/GL and output quality. Acceptance requires genuine artifact, embedded texture, correct viewer/Blender import and no remote downloads during inference.

**Limitations:** this is a single-image model, not exact hidden-face recovery, motion-ready adult facial topology, multi-view or a comprehensive PBR authoring/scene system. No real GPU model load or generated GLB has yet been tested.

## Why this pair wins and what could change it

3DAIGC-API supplies a compatible orchestration boundary we already use; TripoSR supplies the first isolated 3D inference candidate. Together they minimize new moving parts for one end-to-end CPU/API/GPU proof, preserve first-party SaaS control, and keep future models swappable. The pair does NOT provide premium retopology, eye blinking, jaw/visemes, animation retarget, multiview, editable worlds, billing or fine-tuning; those are later specialized adapters (not additional primaries).

Alternative evidence:
- AssetFurnace's inspected NOTICE explicitly retains separate Hunyuan, Stability, DINO, Qwen and other model licenses; its broad Python/native dependency set complicates replatforming.
- TRELLIS.2 upstream README advertises full PBR/high-resolution/H100 timings, but its standard NVIDIA renderer path includes noncommercial constraints; owner measurements unavailable.
- SF3D LICENSE.md explicitly includes a community commercial registration and USD 1M annual-revenue condition; weights are gated. It cannot be treated as universally unrestricted.
- Stock Step1X runtime uses noncommercial nvdiffrast; stock TripoSG includes noncommercial RMBG and restricted Hunyuan/FlashVDM-derived components; Hunyuan3D 2.1 has geographic restrictions.
- UniRig/SkinTokens/Puppeteer become useful only after a real tested mesh; Open3DStudio duplicates our working studio.

If an alternate model demonstrates superior held-out character quality/rigging suitability, fits budget AND passes the entire source+weight+data+renderer+SaaS license gate, update this decision via reviewed ADR and exact pins. Never silently change the production approval file.

This decision is not legal advice or a promise of first-model production readiness.
