# Build 3D AI — Independent AI 3D Creation Platform

> **Main project goal:** [Read the complete Build 3D AI project goal (.txt)](docs/BUILD_3D_AI_PROJECT_IDEA.txt). Adopted by the owner on 17 November 2026 as the repository's primary product direction.

Build an independent AI-assisted 3D creation studio for reusable, editable assets, with a long-term focus on consistent stylized adult characters and environments for Blender animation. Build on the existing product foundation, prove a focused real asset workflow first, and expand through measured quality and practical artist control.

> **Implementation baseline (15 Nov 2026):** `main` now contains the authenticated gateway, durable private product API/worker, browser studio/GLB viewer, and filesystem + optional S3-compatible artifact storage. Follow the [complete ordered checklist](docs/IMPLEMENTATION_CHECKLIST.md), [current handoff](docs/CODEX_HANDOFF.md), and [product backend runbook](docs/PRODUCT_BACKBONE.md). **No real GPU inference or production SaaS is deployed yet.**

> **Verification boundary:** GitHub CI covers Python 3.11/3.12 gateway/API tests, SQLite/PostgreSQL behavior, TypeScript/unit/build checks and Playwright browser-contract tests. Browser/storage GLB fixtures are synthetic; they do not prove model quality, GPU cost, Blender import, commercial model clearance or production deployment.

> **Long-chat recovery / permanent project context:** Start with [Master Project Memory and Continuation Handbook](docs/PROJECT_MEMORY_MASTER.md). It preserves the available research, conversations, architecture chart, all study/reference links, exact decisions, PR/CI history, the original 954-line assignment and the next Codex task. Read the date and verify current GitHub state before acting.

## Mission

Build and operate an **independently branded, commercially viable AI 3D software platform** that can compete with leading products such as **Meshy** and **Tripo** on model quality, controllability, production readiness, cost, and user experience.

The owner controls the product, brand, website, infrastructure, source repository, first-party code and customer relationships. We will **reuse proven public technology rather than waste Codex credits rewriting it**, while respecting all third-party code, model, weight, data and dependency licenses. Open-source building blocks are not exclusively owned by this project.

**Strategic model:** one product monorepo, multiple independently maintained GPU/model services, strong quality benchmarks, specialization through fine-tuning, and incremental production deployments using Codex and cloud GPUs.

## Key product goals

1. **Text → 3D:** prompts become geometry, textures, previews and exportable assets; an initial implementation may use text → generated image → 3D, clearly labeled.
2. **Single image → 3D:** generate a high-quality mesh; openly disclose inferred/unseen geometry.
3. **Multi-image / multi-view → 3D:** improved consistency from multiple reference views.
4. **Professional 3D:** PBR materials, texture editing, UVs, mesh cleanup, retopology, segmentation, polygon budgets and export.
5. **Animation-ready characters:** body rigging, skinning, Blender-compatible motions, eye controls, blinking, brows, jaw, mouth interior, expressions, visemes and lip-sync.
6. **Objects, characters and environments:** editable scenes, buildings, terrain and object placement; support splat-based worlds as a separate representation.
7. **Commercial product:** accounts, private projects, generation history, credits, subscriptions, API, billing, job queues, safe downloads, monitoring and cost controls.
8. **Custom AI:** run open weights under approved terms, fine-tune licensed datasets, evaluate improvements, own our adaptation artifacts to the extent permitted, and version model releases.

**Initial differentiation:** reusable stylized adult characters and environments for Blender animation workflows, rather than just appealing single-view renders. Long-term scope remains a complete general-purpose 3D creation studio.

## Current implementation

- **Gateway:** private 3DAIGC-API integration, fail-closed approved-model policy, bounded GLB verification and an explicit-spend GPU smoke runner.
- **Product API/worker:** operator-provisioned API keys, projects, durable text/image jobs, idempotency, rate/active-job limits, fenced leases, uncertain-submission reconciliation and owner-scoped verified downloads.
- **Browser studio:** original Next.js UI for projects, text/image submission, approved-model state, full persisted job history and a Three.js/R3F GLB viewport with orbit/zoom/reset/wireframe/statistics. Current login is a private API-key mechanism contained in an HttpOnly BFF cookie, not public signup.
- **Artifact storage:** owner-scoped atomic filesystem storage by default plus an optional private S3-compatible backend behind configuration. S3 tests use an in-process synthetic client; no bucket was provisioned.
- **Identity direction:** Better Auth is the preferred public-browser identity candidate, but it remains disabled until an immutable external-identity mapping and trusted BFF→API assertion boundary are implemented.

Merged implementation milestones: PR #1, consolidation PR #14, browser-studio PR #15 and object-storage PR #16. PRs #11–#13 were superseded by #14 after their reviewed final tree was transplanted cleanly onto `main`.

**Project state:** generation is intentionally unavailable unless an exact model is placed in the reviewed approval policy. No real model inference has been executed or benchmarked by this project.

### Run the private product backend and studio locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e "./apps/gateway[test]" -e "./apps/api[test]"
build3d-admin migrate
build3d-admin create-user --name "Owner"
uvicorn build3d_api.main:create_app --factory --host 127.0.0.1 --port 8081

# separate terminal
cd apps/web
cp .env.example .env.local
npm install --no-audit --no-fund
npm run dev
```

Save the API key printed by `create-user` privately; it is displayed only once. Use it in the studio's private login. The Next.js server validates and retains it in an HttpOnly SameSite cookie; browser JavaScript does not persist it. The default approval policy disables generation, and starting the API/studio does not start a GPU or worker.

See [browser studio details](apps/web/README.md), [artifact storage](docs/OBJECT_STORAGE.md) and [identity/account lifecycle decision](docs/IDENTITY_AND_ACCOUNT_LIFECYCLE.md).

## Repository layout

```text
apps/                                  First-party web studio, product API and gateway
services/                              First-party model/service qualification work
config/                                Reviewed configuration examples
scripts/                               Development and cloud setup helpers
docs/                                  Main goal, memory, audits and runbooks
.github/                               Active first-party CI and repository templates
AnalyseFuture/third_party/3daigc-api/    Preserved upstream source snapshot
AnalyseFuture/third_party/triposr/       Preserved upstream source snapshot
AnalyseFuture/assets/reference/autorig/ Preserved example models, demos and diagrams
```

The [structure guide](docs/REPOSITORY_STRUCTURE.md) explains active components, compatibility paths and preserved research material. The [17 November repository audit](docs/REPOSITORY_AUDIT_2026-11-17.md) records the review prompted by the owner's reported disruption. The review began at the expected `e4b05f4` baseline; this does not independently confirm compromise or establish account security.

Existing product applications, qualification services and runtime configuration stay in their working locations. The supplied source snapshots and asset bundle are preserved under [AnalyseFuture](AnalyseFuture/README.md) for review, with a [file index](AnalyseFuture/FILE_INDEX.json), [source snapshot notes](AnalyseFuture/third_party/README.md), [reference asset notes](AnalyseFuture/assets/reference/README.md) and [archive inventory](docs/ARCHIVE_IMPORTS.json).

Imported source and assets remain **RESEARCH_ONLY**. The 3DAIGC-API ZIP omitted its declared submodule source, and the example asset bundle supplied no license. These references are separate from the product applications; relocating them does not approve a model or enable inference. `AnalyseFuture` identifies deferred reference material, not confirmed malware, and is not an execution sandbox.

## Session preservation — 17 November 2026

The [main project goal](docs/BUILD_3D_AI_PROJECT_IDEA.txt) preserves the adopted product direction, existing foundation, proposed roadmap and technical limits. Its future features remain proposals, not evidence of implementation or approval to spend. The [cloud development guide](docs/CLOUD_DEVELOPMENT_ENVIRONMENT.md) records reproducible setup and startup using the helpers in [`scripts/cloud/`](scripts/cloud/).

Archive organization was already pushed to `main` in commit `b32f88a`. Git preserves committed files; running processes, installed dependencies, caches and private smoke-test credentials require separate restoration or regeneration. Resume with the cloud guide, then qualify one real generation workflow under the existing model, license and budget gates.

## Architecture in brief

```text
User browser / Public API
         |
  Web Studio + Viewer
         |
 Authentication + Backend API
         |
 Database + Durable Jobs + GPU Router
         |
 +------------------+-------------------+---------------------+
 | 3D Generation    | Texture / UV      | Rig / Scene Workers |
 | Model Adapters   | Mesh Processing   | Blender Automation  |
 +------------------+-------------------+---------------------+
         |
 Validated Export + Private Object Storage
         |
 Customer downloads: GLB initially; other formats when validated
```

## Public projects to evaluate (NOT automatically approved)

- App foundation: [Open3DStudio](https://github.com/FishWoWater/Open3DStudio) and [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API)
- Model research: [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), [TripoSG](https://github.com/VAST-AI-Research/TripoSG)
- Rigging: [UniRig](https://github.com/VAST-AI-Research/UniRig), [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens)
- Established utilities: [Blender](https://www.blender.org/), [xatlas](https://github.com/jpcy/xatlas), [glTF Transform](https://github.com/donmccurdy/glTF-Transform), [Three.js](https://github.com/mrdoob/three.js)
- Alternative workflows and environment R&D: [AssetFurnace](https://github.com/Bingeljell/image-to-3dlab), [WorldGen](https://github.com/ZiYang-xie/WorldGen), [worldgen-forge](https://github.com/Ardynai/worldgen-forge)

Do **not** indiscriminately merge these projects. Pin versions, test actual functionality, and audit commercial/SaaS terms of models, weights, datasets and transitive dependencies. Some research dependencies are non-commercial or geographically restricted.

## Read this documentation

| Document | Why it exists |
|---|---|
| [Main project goal (.txt)](docs/BUILD_3D_AI_PROJECT_IDEA.txt) | Owner-adopted product direction, future horizons and limits |
| [Repository structure](docs/REPOSITORY_STRUCTURE.md) | Active code, compatible runtime paths and preserved references |
| [Repository audit — 17 November 2026](docs/REPOSITORY_AUDIT_2026-11-17.md) | Observations, preservation work and remaining uncertainties |
| [Vision and scope](docs/PRODUCT_VISION.md) | What we are trying to become and who it serves |
| [Feature matrix](docs/FEATURE_MATRIX.md) | Complete goals, priorities and acceptance tests |
| [Architecture](docs/ARCHITECTURE.md) | How independent components fit into one system |
| [Public repository strategy](docs/OPEN_SOURCE_STRATEGY.md) | Reuse-first decisions, license gates and candidate URLs |
| [Model and data plan](docs/AI_MODELS_AND_DATA.md) | Fine-tuning, provenance, benchmarks and deployment |
| [Roadmap](docs/ROADMAP.md) | Milestones and release gates |
| [Engineering backlog](docs/BACKLOG.md) | First tasks for developers and Codex |
| [Benchmark plan](docs/BENCHMARKS.md) | How to prove competitiveness |
| [Security and cost controls](docs/OPERATIONS_SECURITY.md) | Protect customers and GPU budget |
| [Decision register](docs/DECISIONS.md) | What is decided vs still unverified |
| [Codex agent instructions](AGENTS.md) | Non-negotiable coding-agent rules |
| [Contribution guide](CONTRIBUTING.md) | How developers can join |

## Development reality

Codex/Astra can write, review and test code in the repository. **Codex Cloud is not the product's production GPU host**; real AI inference and training require separately provisioned resources (AWS is the intended primary provider, subject to quotas, credits and budget approval). A coding agent cannot guarantee unlimited work, zero GPU cost or superior quality without evaluation.

Every feature must have a real end-to-end acceptance test and a clear status: **planned / implemented / tested / deployed**. No mocks should be presented as completed AI generation.

**Next step:** finish the exact code/weight/runtime license audit and select one commercially cleared generation stack. Only after explicit owner approval for that stack and a bounded GPU budget, run one real image-to-3D vertical slice through generation → validated GLB → product API → browser viewer → Blender import and record quality, latency, VRAM, checksum and actual cost.

## Licensing

This repository contains project-original planning material. **No blanket license to reuse project-original content is granted unless the owner adds one.** Every upstream source, model, weight, dataset and dependency remains subject to its respective license. This statement is not legal advice.
