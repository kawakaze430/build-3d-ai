# Build 3D AI — Independent AI 3D Creation Platform

> **Status (13 Nov 2026): Project planning.** This repository currently documents our goals and engineering plan. It does **not** claim that a production application, trained model, or GPU deployment is already working.

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

**Next step:** execute [Phase 0](docs/ROADMAP.md): verify candidate repositories and licenses, choose one commercially cleared model, run one real image-to-3D job on a GPU, and record actual quality, latency, VRAM and cost.

## Licensing

This repository contains project-original planning material. **No blanket license to reuse project-original content is granted unless the owner adds one.** Every upstream source, model, weight, dataset and dependency remains subject to its respective license. This statement is not legal advice.
