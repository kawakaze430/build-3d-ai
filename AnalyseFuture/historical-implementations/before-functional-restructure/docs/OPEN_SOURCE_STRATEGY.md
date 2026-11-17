# Public Repositories, Reuse Policy and License Audit

**Policy:** Public code or pretrained weights are not necessarily free for commercial SaaS. The projects below are candidates, **not approved integrations**. Audit code + weights + datasets + third-party dependencies + commercial/territorial rights before any production inclusion.

| Public project | Candidate benefit | Decision to test |
|---|---|---|
| [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) | Studio web interface | Foundation candidate |
| [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) | GPU jobs, existing model/mesh adapters | Foundation candidate |
| [AssetFurnace](https://github.com/Bingeljell/image-to-3dlab) | Character-to-animation workflows | Compare; selective reuse |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | Geometry model, LoRA training | Initial fine-tune candidate |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | High-quality image-conditioned 3D | Research; renderer license audit |
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | Alternate image-to-3D engine | Benchmark |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | Body auto-rigging | Evaluate |
| [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | Skeleton + skinning prediction | Evaluate |
| [xatlas](https://github.com/jpcy/xatlas) | UV unwrapping | Reuse if cleared |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform) | GLB inspection/optimization | Reuse if cleared |
| [Three.js](https://github.com/mrdoob/three.js) | Browser 3D viewport | Reuse if cleared |
| [Blender](https://github.com/blender/blender) | Scene/mesh/animation export automation | CLI; GPL handling review |
| [WorldGen](https://github.com/ZiYang-xie/WorldGen) | World/splat research | Separate R&D mode |
| [worldgen-forge](https://github.com/Ardynai/worldgen-forge) | Structured environment workflows | Separate R&D mode |

## Why not one or fifteen repositories?

A single application rarely has all features. Blindly combining everything increases CUDA conflict, security surface, license risk and maintenance cost. Use **one privately controlled product repository**, a small number of chosen existing application components, and individually deployed model adapters.

## Audit checklist for each dependency

- Pin exact upstream revision, source license and NOTICE obligations.
- Validate the model **weights** license separately from source code.
- Validate training-data usage and output restrictions.
- Identify transitive rendering, UV, mesh and segmentation libraries and their commercial terms.
- Check territory restrictions, SaaS hosting rights and distribution obligations.
- Run actual smoke tests: GPU model load, output validity, resource demand, API compatibility and crash behavior.
- Classify: APPROVED / RESEARCH_ONLY / NEEDS_PERMISSION / REJECTED, with date and accountable reviewer.
- Confirm security, maintenance and update/rollback plan.

**Specific caution:** NVIDIA-related renderer/segmentation tooling can have non-commercial license restrictions; some Hunyuan model variants have region-specific terms. Do not treat a permissive top-level repository license as blanket clearance for its included runtime.

## Reuse-first coding rule

Before implementing a feature: (1) document public candidates, (2) license-filter, (3) isolated smoke-test, (4) benchmark and compare integration vs rebuild, (5) record decision, (6) integrate in a separate service, (7) regression test. Code generation credits should be spent on **product differentiation** (reliable workflows, artist controls, character consistency, advanced animation, commercial platform), not mature generic algorithms.

## Documents for Codex to create and maintain during the real audit

- `docs/LICENSE_MATRIX.md`: repository, exact version, licenses, third-party notices, verdict.
- `docs/REUSE_AUDIT.md`: real code inspection, feature evidence, costs, dependencies, compatibility.
- `docs/INTEGRATION_DECISIONS.md`: accepted/rejected vendors and rationale.
- `docs/COST_BASELINES.md`: actual inference costs, cold starts, storage and retries.

These files should contain verified findings, not invented declarations of approval.
