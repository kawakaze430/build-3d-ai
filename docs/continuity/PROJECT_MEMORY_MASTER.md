# BUILD 3D AI — Master Project Memory and Continuation Handbook

## Post-restructure validation authorized — 17 November 2026

The owner subsequently requested **“pls test all”**, lifting the earlier pause.
All available local first-party suites now pass after correcting Vitest's missing
`@/` alias. See the [current validation report](../../AnalyseFuture/validation/2026-11-17/REPORT.md)
for counts, the initial regression, runtime checks and infrastructure limits.
Earlier no-tests notes below are historical migration records, not a current ban.


## Historical restructuring snapshot — 17 November 2026

During this phase the owner deferred tests, before the later authorization above.
The complete
functional reorganization moves 45 files (42 starting tracked,3 newly authored) into
project/architecture/development/operations/research/continuity documentation,
Compose infrastructure, identity configuration, packaging helpers and web
studio/assets/jobs/client/server collections. Existing package/publicHTTP/schema
boundaries remain. All original content and earlier recovery work are preserved.

Read [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md), the
[complete inventory](../../AnalyseFuture/COMPLETE_FILE_INVENTORY.txt),
[feature inventory](../../AnalyseFuture/FEATURE_INVENTORY.txt),
[path mapping](../../AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt) and
[validation record](../../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt).
At that delivery, tests preceded the final moves and final-layout validation
was deferred. That restructuring delivery used `[skip ci]` and an ordinary main
push without force or history rewrite. Refer to the delivery receipt/Git refs
for actual publication evidence rather than inferring success from a plan.


> Canonical GitHub project: https://github.com/kawakaze430/build-3d-ai
>
> Prepared: 16 November 2026 (user-local date). Baseline checked: main at 477b3bff3fd5449dba1d1dd7a9e4e062f99856a3, followed by the original-assignment archive commit 76b663ed2c45e9acc56eed7c1c2cb58ec11eb26b. Implementation PR #26 is open at the time of this snapshot; always re-check the current default branch and PR status.
>
> Purpose: durable, human-readable memory for the owner, ChatGPT, Codex/Astra and future engineers. Start here whenever a conversation is truncated or an agent joins cold.
>
> **Truth boundary:** This document consolidates accessible conversations, available personal-context summaries, original user instructions, actual GitHub artifacts and verified CI metadata. It is **not a verbatim export of every historical chat message**. Old chat transcripts not available to this session were not fabricated. The original 954-line research assignment was preserved verbatim in archives/RESEARCH_IMPLEMENTATION_ASSIGNMENT_2026-11-15.txt. Code and current CI always outrank an older text summary.

## 0. Five-minute recovery procedure for future agents

1. Inspect AGENTS.md and README.md. Read THIS document, then docs/continuity/CODEX_HANDOFF.md, docs/continuity/IMPLEMENTATION_CHECKLIST.md and docs/operations/FIRST_REAL_GPU_RUNBOOK.md.
2. Fetch the current main SHA, all open PRs, branch heads, GitHub Actions statuses and relevant source/tests. The PR table below is a dated snapshot, never an authorization to merge blindly.
3. Review docs/research/LICENSE_MATRIX.md, docs/research/REUSE_AUDIT.md, docs/operations/MODEL_APPROVAL_GATE.md and docs/research/OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt before selecting or deploying any AI engine.
4. The useful offline auditor/test slice from historical PR #26 was recovered into main during repository consolidation. Compare any remaining branch changes explicitly; do not merge its entire older tree over the current product. Dated branch documents are preserved under AnalyseFuture/historical-implementations/triposr-provenance-research/.
5. Reconcile source code and tests against any stale docs. Explicitly distinguish implemented, tested, partial, planned, blocked and deployed.
6. Work on one small verifiable engineering slice. Do NOT start paid GPUs, training or costly services without fresh written owner/budget and legal clearance.
7. Update this master memory and docs/continuity/CODEX_HANDOFF.md in the SAME PR/commit as any material decision, gate, link or milestone.

### Copyable context-recovery prompt

~~~text
You are continuing Build 3D AI in https://github.com/kawakaze430/build-3d-ai.
Before doing work, read AGENTS.md, docs/continuity/PROJECT_MEMORY_MASTER.md,
README.md, docs/continuity/CODEX_HANDOFF.md, docs/continuity/IMPLEMENTATION_CHECKLIST.md,
docs/research/LICENSE_MATRIX.md and docs/operations/FIRST_REAL_GPU_RUNBOOK.md, then inspect
the CURRENT main branch, open PRs, workflows and actual source/tests.
Preserve verified first-party infrastructure; do not restart the project.
The 112 open-source study repositories are in
docs/research/OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt. Exactly two primary study
repos were selected in PR #26: 3DAIGC-API and TripoSR; reevaluate only
with source-level and licensing evidence. No production AI checkpoint or
paid GPU inference is approved. Distinguish real tests from fixtures.
Use narrow PRs, run relevant tests, document changes/risks and leave
reviewable work for Codex. Update PROJECT_MEMORY_MASTER.md and
CODEX_HANDOFF.md with material new context before ending.
~~~

## 1. Owner's north-star goal

Build an independently controlled and commercially viable AI-powered 3D creation platform, competitive in measurable workflows with Meshy and Tripo. The owner must control product brand, repository, original website/UI, first-party code, credentials, deployments, customer relationships and business logic. Reuse excellent open-source components lawfully without representing those components or weights as exclusively owned.

### Complete product capabilities requested

- Real text-to-3D, single image-to-3D and multi-image/multi-view-to-3D.
- High-quality geometry, consistent views, textures, PBR materials, UV layouts, controlled triangle budgets, mesh repair, smart topology, retopology, part editing and export.
- Object/prop generation, premium stylized adult human character creation, reusable character identity, skeletons and skin weights, motions and retargeting.
- Actual movable eyeballs, blinking eyelids, expressive eyebrows, smile/frown, working jaw and mouth interior, phoneme/viseme mouth shapes, clean deformation and lip-sync.
- Blender-ready GLB/FBX/OBJ/BLEND outputs where individually validated, production-quality lighting and animation.
- Editable rooms, houses, buildings, streets, landscapes, props, terrain and independently manipulable scenes; optional splat-based worlds as a distinctly labeled representation.
- Browser studio with accounts, project/version history, input upload, prompt editing, model selection, preview, private downloads, credits, payments, API, billing, queue recovery, observability and GPU scheduling.
- Eventually licensed data, training provenance and independently controlled fine-tuned model adaptations with measured quality gains.

**Differentiator:** reusable animation-ready **adult** characters/environments for episodic Blender productions, not just a striking front-view object render. Episode/movie plans are an eventual product acceptance use case, not a replacement for an independent general-purpose 3D creation platform.

## 2. Film/animation conversations and creative requirements

Historical creative discussions (10–11 Nov 2026) informed product acceptance criteria. The owner asked for a planned adult-audience cartoon/animated series of **10 episodes, roughly 30 minutes each**, with reusable stylized characters and places. Reference channels/videos were for studying visual production workflow, but new episodes must have independent original content and respect creators' rights.

### Exact recurring hero-character brief (user's written specification)

> Create a premium-quality stylized 3D animated ADULT WOMAN, age 28–32, with the elegant appearance of a beautiful grown woman, NOT a child. Tall, slim, graceful, natural adult body proportions, long legs, realistic torso, approximately 7.5 heads tall, and a correctly sized head. Soft oval face, refined feminine features, small delicate nose, natural lips, gentle confident smile. Beautiful LARGE expressive brown animated eyes, clear detailed irises, glossy reflections, soft eyelids, natural eyelashes, and elegant eyebrows. Eyes should be big and charming, but not childish or excessively oversized. Shoulder-length chestnut-brown wavy hair with side-swept bangs. Wear a fitted navy blazer, lavender collared shirt, charcoal tailored trousers, brown leather loafers, and a small brown crossbody bag. Full-body front view, symmetrical T-pose, polished 3D animation-film quality, detailed textures. NO childlike face, chibi proportions, giant head, or short legs.

This is a **creative design target**, not a trained model, a delivered 3D asset or permission to copy a real person's likeness. Users reported prior outputs looked childlike or low fidelity. A 10,000-polygon reduction may damage eyes/face detail; neither high poly count nor retopology alone guarantees animation-quality deformation.

### Tools and production route discussed

- Meshy and Tripo/Tripo Studio: optional generation of characters and props; source services and commercial offerings, **not repos we can freely vendor**.
- Adobe Mixamo: body rigs/motion clips; suggested searches were Idle, Walk, Run, Talking, Gesturing, Wave, Nod, Laugh, Sit and hand gestures. Mixamo body motions do NOT automatically produce blinking, eye gaze, brows, mouth shapes or speech visemes.
- World Labs Marble: proposed textured environment assets; prefer true textured polygon GLB for editable Blender sets where available. Gaussian splats and collider models must not be labeled a textured editable polygon mesh.
- Blender (Rigify and custom corrective facial controls): scene assembly, cameras, expressions, lighting and animation. Real geometry, skeletal poses and renders, rather than AI-generated final video.
- Codex/Astra: author scene scripts/asset automation, maintain project software; not a substitute for quality acceptance.
- Google Colab GPU or an authorized cloud GPU: potential render/compute environment only after its current terms and quota are checked.

The user clarified that **“without AI” means avoiding AI-generated final video**, while optionally accepting AI-assisted 3D asset generation and real Blender-based animation. Non-AI licensed/manual models are also acceptable.

Meshy practical constraints discussed: user saw only one image upload OR text mode, a text prompt limit around 1,000 characters, confusion about Remesh vs Smart Topology and when to rig. Preserve the high-detail model before retopology. A past source model was reported around 1.1 million faces; those numbers are historical observations, not platform benchmarks. Retopology changes mesh edge flow, not automatically facial feature quality.

For rigging, prioritize a neutral adult-proportion T-pose, clean neck/face mesh, eye shells, independent eyelid deformation, jaw/mouth cavity and teeth/tongue where appropriate, viseme set, brows and corrective shapes. Rig + walk animation alone does not satisfy character acceptance.

### Rendering and recording decision

- Viewport screen capture can illustrate workflow and enable fast previews; it can skip an offline final render but does not eliminate the cost of actually drawing frames.
- Blender Eevee/render-as-image-sequence, low-resolution playblast/viewport export and later final rendering are reproducible alternatives to screen-recorded production.
- A proposed production baseline to benchmark is 1080p at 24 or 30 fps, short shots and reusable assets. No claim of exact minutes-per-frame without actual GPU/scene benchmark.
- The user asked if one minute taking two hours to render is plausible: it depends on samples/scene/hardware. Test a 10-second representative shot before extrapolating to the whole series.
- Earlier tutorial observations suggested mixtures of viewport recording, Face Puppet capture and image-sequence/iClone renders; retain uncertainty unless an entire uploaded video is available for actual inspection.

### Reference videos supplied by the user

1. https://www.youtube.com/live/b35TsG6BzqY?si=9oCEOXbee1etxTSF
2. https://youtu.be/2C2JKqi3CWc?si=2ydhl0cGef5bcWCZ
3. https://youtu.be/W2E3U3MV-7E?si=eWb9-m7UtwaF78gK
4. https://youtu.be/RA-geft96ss?si=xV1RmebyyFbjxA99
5. https://youtu.be/WD5AKUC3pqU?si=orrRFjm_5EsExGCi

The reference videos are **user-provided study links**; this document does not claim all videos were completely replayed or every production method independently verified.

## 3. Actual Build 3D AI architecture on main (15 Nov baseline)

~~~mermaid
flowchart TD
    U["User in first-party Next.js studio"] --> BFF["Private Next.js BFF session"]
    BFF --> API["FastAPI tenant API + SQLAlchemy"]
    API --> DB["Projects, jobs, identities, artifact records"]
    DB --> W["Durable fenced worker"]
    W --> GW["Private approved-model gateway"]
    GW --> M["Reviewed GPU model service (not running)"]
    M -.->|future real output| GLB["Bounded GLB validation + owner storage"]
    GLB --> API
    API --> V["Existing Three.js GLB viewer/download"]
~~~

### Real source directories to preserve

| Directory/file | Responsibility | Verified boundary |
|---|---|---|
| apps/web/src/features/studio/components/studio.tsx | first-party project/generation/history UI and quota warnings | Synthetic backend/Playwright flow tested; no real model proof |
| apps/web/src/features/assets/components/model-viewer.tsx | Three.js/React Three Fiber GLB orbit/zoom/wireframe | Viewer loads the real product route; test GLB fixture is synthetic |
| apps/web/src/app/api/session/route.ts | private API-key cookie lifecycle | Not public self-signup |
| apps/web/src/app/api/product/[...segments]/route.ts | strict BFF route allowlist | Maintains server-side API key boundary |
| apps/api/src/build3d_api/main.py | owner-scoped projects, jobs, models, downloads and storage usage | Private product API, not public commercial signup/billing |
| apps/api/src/build3d_api/store.py | DB persistence, idempotency, quotas, identity mapping | SQLAlchemy + migration coverage |
| apps/api/src/build3d_api/worker.py | claims/fencing, polling, crash/uncertain submission recovery | No real production GPU exercised |
| apps/api/src/build3d_api/storage.py | filesystem and optional S3-compatible object storage | Synthetic S3-client tests; no real bucket provided |
| apps/api/src/build3d_api/trusted_identity.py | optional trusted issuer/audience-bound JWT/JWKS path | Disabled by default pending full lifecycle |
| apps/gateway/src/build3d_gateway/upstream.py | 3DAIGC-compatible operator API client | HTTP in-memory/contract testing |
| apps/gateway/src/build3d_gateway/model_policy.py | exact model allowlist, fail-closed | Zero production models approved |
| apps/gateway/src/build3d_gateway/glb_validation.py | bounded structural GLB and checksum verification | Structural, not full Blender/deformation/material QA |
| apps/gateway/src/build3d_gateway/textured_glb.py | strict OBJ+PNG -> embedded textured GLB packager | Synthetic fixture tests; no AI texture yet |
| services/generation/triposr_candidate | pinned TripoSR qualification preparation/runtime evidence | No Docker image built, real weights loaded or GPU used |
| .github/workflows | Gateway, Product API, Web Studio and TripoSR CI | Tests CPU/HTTP/browser contracts, not real deployed SaaS |
| docs/ | legal/architecture/roadmap/audit/runbooks | Reference docs; some historical status paragraphs are stale |

### Implemented vs incomplete

**Implemented and CI-tested:** private auth keys, projects/history, durable jobs/worker fences, owner scope, quotas, read-only artifact inventory, copy-only filesystem->S3 migration, short-lived trusted assertion foundations (disabled by default), private model gateway and GLB validator, browser studio and viewer, synthetic GLB packaging, pinned TripoSR source patch.

**Partially implemented:** public identity foundation, optional object storage without real provisioned bucket, code for GPU smoke run with explicit-spend guard, model adapter contracts, quotas without complete retention/deletion policy.

**Not yet verified/deployed:** genuine model loading/inference and textured GLB, GPU cost/VRAM/latency, Blender import of AI-generated result, production billing/credits, public identity lifecycle, real cloud deployment, retopology editor, body/face rig generation, motion/lip sync, scene authoring and model fine-tuning.

**Known documentation staleness:** docs/architecture/ARCHITECTURE.md still contains a 14 Nov snapshot mentioning absent web UI/S3, even though later main commits added them. Treat latest source/CI and later handoff as authoritative; update stale headings in a focused documentation PR when needed.

## 4. Pull request history and validation snapshot

Repository: https://github.com/kawakaze430/build-3d-ai/pulls
Main baseline immediately before this memory document: 477b3bff3fd5449dba1d1dd7a9e4e062f99856a3

| PR | Outcome at snapshot | Main contribution |
|---|---|---|
| #1 | merged | first gateway, ordered checklist, Docker/test baseline |
| #11, #12, #13 | closed, superseded | model policy, GLB checks and durable backend final tree consolidated in #14 |
| #14 | merged | model policy, GLB verification, durable worker/API |
| #15 | merged | Next.js browser studio and GLB viewer |
| #16 | merged | private filesystem and optional S3-compatible storage |
| #17 | merged | baseline docs and public identity architecture decision |
| #18 | merged | exact-revision reuse/commercial license audit |
| #19 | merged | immutable external identity mapping foundation |
| #20 | merged | TripoSR qualification and strict textured GLB packaging |
| #21 | merged | pinned fail-closed TripoSR candidate preparation |
| #22 | merged | artifact quotas and non-destructive storage inventory |
| #23 | merged | verified copy-only filesystem-to-S3 migration |
| #24 | merged | optional trusted external JWT/JWKS authentication foundation |
| #25 | merged | browser quota meter, limits and warnings |
| #26 | **open, mergeable as checked 16 Nov** | source audit, exactly two primary repos, execution plan and TripoSR pip dependency-provenance audit |

Exactly 13 PRs had been merged before #26, with three superseded, and zero older open PRs; #26 is the sole open PR at this memory snapshot. No one should infer its future state from this table.

### PR #26: what the new provenance audit actually proves

PR: https://github.com/kawakaze430/build-3d-ai/pull/26
Head: 712920893d9c9ba139c935605af5a89d2cfccaf0

- Adds CPU-only audit_pip_report.py and nine local unittest fixture tests.
- CI on the final head passed: Gateway https://github.com/kawakaze430/build-3d-ai/actions/runs/43731187656, Product API https://github.com/kawakaze430/build-3d-ai/actions/runs/43731187763, TripoSR Qualification https://github.com/kawakaze430/build-3d-ai/actions/runs/43731187673.
- TripoSR CI recorded **33 resolved dependency artifacts**, of which **one** is a source archive: antlr4-python3-runtime==4.9.3 via OmegaConf. JSON status is BLOCKED_BY_SOURCE_ARCHIVES_NOT_PRODUCTION_APPROVED.
- The CLI's strict --require-wheels mode rejects this source archive; the normal CI report mode records the blocker without falsely claiming release approval.
- TripoSR index-provenance review artifact #14168860683 was uploaded, with short expiry (22 Nov 2026). Prefer reproducing the CI evidence rather than assuming the artifact remains available.
- Even a green provenance-audit CI does NOT mean verified wheel bytes, complete runtime/OS-library license clearance, real model load, or launch approval.
- PR #26 also adds four docs (CURRENT_STATE_AUDIT, TWO_PRIMARY_REPOSITORIES_DECISION, INTEGRATION_DECISIONS, EXECUTION_PLAN). Until merge, read them on its branch, not on main.

## 5. Open-source research (112 URLs) and exactly two primary study repos

Canonical 112-entry catalog on main:
[OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt](../research/OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt)

It includes GitHub URL, purpose, first/next/exploratory priority, GitHub license metadata, maintenance/archival signal and high-risk gates, grouped into application foundations, generation, geometry/PBR, animation, scenes/splats, browser studio, platform, training and security. **Each URL was verified to exist when the catalog was prepared; that is not a comprehensive source/weight/license audit of all 112.**

### Exactly two primary research/engineering choices (PR #26)

1. **FishWoWater/3DAIGC-API** — https://github.com/FishWoWater/3DAIGC-API ; reviewed SHA 9c5643f99cbfd8d47b81922790f0d0a36be57e81 ; Apache-2.0 top-level app shell; submodules carry separate licenses. Primary API contract already integrated by our gateway, not our public identity/studio.
2. **VAST-AI-Research/TripoSR** — https://github.com/VAST-AI-Research/TripoSR ; reviewed SHA 107cefdc244c39106fa830359024f6a2f1c78871 ; first pinned single-image 3D qualification candidate, NOT approved production model. Dependencies, weights/training rights, runtime and data need full clearance.

The 12-candidate scorecard is in PR #26: https://github.com/kawakaze430/build-3d-ai/blob/research/triposr-resolved-dependency-audit/docs/TWO_PRIMARY_REPOSITORIES_DECISION.md

### Additional specialists and alternatives

- **AssetFurnace** — https://github.com/Bingeljell/image-to-3dlab : multi-stage workflow research; source NOTICE separates Hunyuan, Stability, DINO/Qwen and motion/weight licensing.
- **Open3DStudio** — https://github.com/FishWoWater/Open3DStudio : UI ideas, but first-party Next.js is already selected/tested; do not replace blindly.
- **TRELLIS/TRELLIS.2** — https://github.com/microsoft/TRELLIS and https://github.com/microsoft/TRELLIS.2 : high-quality/multiview/PBR R&D; stock renderer license restrictions need resolution, and upstream H100 quality/speed is not our measured benchmark.
- **Step1X-3D** — https://github.com/stepfun-ai/Step1X-3D : stock commercial runtime path rejected due non-commercial nvdiffrast.
- **TripoSG** — https://github.com/VAST-AI-Research/TripoSG : stock worldwide service path rejected due BRIA RMBG-1.4 and derived FlashVDM/Hunyuan restrictions.
- **Hunyuan3D-2.1** — https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 : stock community-license territory restrictions impede intended worldwide SaaS.
- **UniRig / SkinTokens** — https://github.com/VAST-AI-Research/UniRig and https://github.com/VAST-AI-Research/SkinTokens : later auto-rigging/skinning candidates, weight/runtime audit first.
- **xatlas / xatlas-python** — https://github.com/jpcy/xatlas and https://github.com/mworchel/xatlas-python : UV and narrow OBJ binding; not a magic GLB or production-texture exporter.
- **glTF Transform / Three.js / Blender** — https://github.com/donmccurdy/glTF-Transform , https://github.com/mrdoob/three.js , https://github.com/blender/blender : asset validation/viewing, runtime, and final animation pipeline; observe package/GPL boundaries.
- **WorldGen / Infinigen / BlenderProc / OpenUSD** — https://github.com/ZiYang-xie/WorldGen , https://github.com/princeton-vl/infinigen , https://github.com/DLR-RM/BlenderProc , https://github.com/PixarAnimationStudios/OpenUSD : editable scene workflows to research separately from Gaussian splats.

No third-party source should be mass-merged into our monorepo without isolated contracts, exact SHA and code/weights/data/dependency rights.

## 6. Exact first-GPU TripoSR evidence and legal gates

Source commit: 107cefdc244c39106fa830359024f6a2f1c78871
Model repo revision: stabilityai/TripoSR@2ba2f5591f8eb0821784764ab9ab99a12e1abb08
Checkpoint filename: model.ckpt
Checkpoint bytes: 1677246742
Checkpoint SHA256: 429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee
DINO config revision: fdc136b8ef48f5a94159af5dd6323ae7a219697a
Patch evidence: vltmedia/TripoSR-scikit@fa39422b81217687f16efe7bb3afc136feb87ba7
Marching cubes pin: scikit-image==0.25.2
Candidate base image Linux/amd64 manifest digest: sha256:11691e035a3651d25a87116b4f6adc113a27a29d8f5a6a583f8569e0ee5ff897

These are **pinned evidence for an unapproved qualification candidate**. The image has not been built/validated end to end; the model checkpoint was not loaded; no actual 3D artifact has been generated in this project.

### Hard gates in dependency order

1. Capture exact full pip wheelhouse and build provenance, including the antlr4 4.9.3 source archive, independent wheel-byte SHA256 checks, license/NOTICE and all PyTorch/CUDA/base-image/OS transitive libraries.
2. Build/inspect the digest-pinned candidate container under an approved resource envelope; verify local config, deterministic source patch, offline flags and no hidden checkpoint downloads.
3. Test ModernGL/xatlas headless bake, strict model.ckpt bytes/SHA, torch.load(weights_only=True), source output -> embedded textured GLB.
4. Obtain owner/legal clearance for intended worldwide commercial SaaS across source, weights, curated Objaverse data, renderer and all transitives.
5. Obtain written owner approval for cloud account/provider/region, exact GPU model/VRAM, quota, per-hour estimate, maximum total spend, shutdown/cleanup and monitoring. An AWS L4 route was discussed as a possibility, not automatically funded.
6. Only then execute one real image -> 3D -> textured embedded GLB -> authenticated job -> private object -> browser viewer -> Blender import, with input SHA, hardware/driver/model revisions, timings, VRAM, failures and actual cost.

**Never** start paid GPU instances, cloud deployments, large checkpoint downloads, training jobs, domains or billing merely because the owner has mentioned possible AWS/Azure/Colab credits. Those amounts/eligibility/expiry are unverified and are NOT operational authorization.

## 7. Staged roadmap (feature requirements and proof)

| Stage | What actually closes the stage | Present status |
|---|---|---|
| 0: Legal/runtime proof | one reviewed model/weight/runtime, genuine GPU artifact, cost/VRAM, exact license rights | BLOCKED |
| 1: End-to-end core | real image/text -> generation -> validated textured GLB -> secure history/viewer/Blender | Private infrastructure partial; actual model missing |
| 2: Pro mesh and materials | UVs, PBR bake, optimization, editable topology, verified exports | Synthetic packaging only |
| 3: Adult character and animation | actual skeleton/weights, walk/run/talk/gesture, eyes/blink, jaw/visemes | Planned |
| 4: Environments and scenes | editable room/landscape/objects; separate splat viewing | Planned |
| 5: Commercial service | signup/reset/deletion, billing ledger, secure deployment, quotas/monitoring | Private partial; public release incomplete |
| 6: Custom models | licensed dataset/provenance, fine-tuning, held-out gains, versioned rollback | Planned |

Exact task IDs, engineering effort, dependencies, CPU/GPU distinction and acceptance tests are in PR #26 docs/EXECUTION_PLAN.md and main docs/IMPLEMENTATION_CHECKLIST.md.

## 8. Safety, independence and testing rules

- Product remains one owner-controlled monorepo with isolated model adapters/containers.
- No secrets or API keys in repository or prompt archives. Uploaded private images remain private; never publish user/customer likenesses, data or credentials.
- Public repo license != unrestricted model weights/training data. Pin each exact source, weights and transitive dependency, license and notices. Stock restrictions remain blocked unless exact permitted replacement/permission is documented.
- Strong default tenant isolation, image upload bounds, body limits, no cross-project artifacts, no SSRF, untrusted GLB/Blender sandbox, stable idempotency and no blind retry of uncertain non-idempotent upstream POST.
- Mocks, geometry fixtures, placeholder outputs, HTTP contract tests and browser tests are valuable but **not proof of live GPU generation**.
- A model registry policy with zero approved models is intentional; never enable an unreviewed checkpoint for a demo.
- Require reproducible benchmark inputs, seed/config, hardware/VRAM, time/cost, multiple-view inspection, material/UV compatibility and Blender deformation when claiming quality.
- No automatic eternal loops. Each task needs testable scope, rollback, code review and a clear stop condition.

## 9. Source documents and durable link index

### On main (existing project documentation)

- [AGENTS.md](../../AGENTS.md) — coding-agent rules and spend/license controls
- [README.md](../../README.md) — product entry point and existing features
- [PRODUCT_VISION.md](../project/PRODUCT_VISION.md) — owner goals and product scope
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) — architecture design (some status text stale)
- [FEATURE_MATRIX.md](../project/FEATURE_MATRIX.md) — requested acceptance gates
- [ROADMAP.md](../project/ROADMAP.md) — broad phases and estimates
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) — task IDs and progress
- [CODEX_HANDOFF.md](CODEX_HANDOFF.md) — engineer-facing current handoff
- [BACKLOG.md](../project/BACKLOG.md) — engineering tasks
- [DECISIONS.md](../architecture/DECISIONS.md) — architectural decisions
- [OPEN_SOURCE_STRATEGY.md](../research/OPEN_SOURCE_STRATEGY.md) — reuse/license policy
- [OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt](../research/OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt) — 112 actual GitHub URLs
- [REUSE_AUDIT.md](../research/REUSE_AUDIT.md) — upstream exact-source findings
- [LICENSE_MATRIX.md](../research/LICENSE_MATRIX.md) — code, model, weights and transitive restrictions
- [FIRST_REAL_GPU_RUNBOOK.md](../operations/FIRST_REAL_GPU_RUNBOOK.md) — staged TripoSR proof and owner gates
- [MODEL_APPROVAL_GATE.md](../operations/MODEL_APPROVAL_GATE.md) — default-off model policy
- [PRODUCT_BACKBONE.md](../operations/PRODUCT_BACKBONE.md) — API/worker, recovery and persistence
- [OBJECT_STORAGE.md](../operations/OBJECT_STORAGE.md) — local/S3 storage and integrity
- [IDENTITY_AND_ACCOUNT_LIFECYCLE.md](../architecture/IDENTITY_AND_ACCOUNT_LIFECYCLE.md) — account and trusted identity
- [GPU_SMOKE_AND_ARTIFACTS.md](../operations/GPU_SMOKE_AND_ARTIFACTS.md) — offline artifact tests and opted-in smoke CLI
- [BENCHMARKS.md](../project/BENCHMARKS.md) — measurement requirements
- [AI_MODELS_AND_DATA.md](../research/AI_MODELS_AND_DATA.md) — model/training/dataset strategy
- [OPERATIONS_SECURITY.md](../operations/OPERATIONS_SECURITY.md) — deployment and security expectations
- [PHASE0_GATEWAY.md](../development/PHASE0_GATEWAY.md) — upstream integration contracts
- [CPU_DEPENDENCY_INVENTORY.json](../research/CPU_DEPENDENCY_INVENTORY.json) — installed dependency metadata evidence
- [adr/0001-web-studio-foundation.md](../architecture/adr/0001-web-studio-foundation.md) — why original browser UI was built
- [archives/RESEARCH_IMPLEMENTATION_ASSIGNMENT_2026-11-15.txt](../../AnalyseFuture/recovery-notes/RESEARCH_IMPLEMENTATION_ASSIGNMENT_2026-11-15.txt) — original complete 954-line user-assigned implementation prompt, archived verbatim

### Open PR #26 documents (not on main until merged)

- [Current State Audit](https://github.com/kawakaze430/build-3d-ai/blob/research/triposr-resolved-dependency-audit/docs/CURRENT_STATE_AUDIT.md)
- [Exactly Two Primary Repositories Decision](https://github.com/kawakaze430/build-3d-ai/blob/research/triposr-resolved-dependency-audit/docs/TWO_PRIMARY_REPOSITORIES_DECISION.md)
- [Integration Decisions](https://github.com/kawakaze430/build-3d-ai/blob/research/triposr-resolved-dependency-audit/docs/INTEGRATION_DECISIONS.md)
- [Execution Plan](https://github.com/kawakaze430/build-3d-ai/blob/research/triposr-resolved-dependency-audit/docs/EXECUTION_PLAN.md)

### Historical owner-supplied technical and tool links

- https://www.tripo3d.ai/ (commercial 3D asset generation)
- https://www.blender.org/ (Blender scene/rig/render pipeline)
- https://www.mixamo.com/ (animation/motion reference service)
- https://www.meshy.ai/ (asset generation comparison)
- https://colab.research.google.com/ (possible GPU compute environment)
- Five owner-supplied YouTube videos are listed verbatim in Section 2.
- All 112 study repository URLs and their preliminary license/activity labels are in OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt; do not duplicate the entire list here.

### Historical scope separation

The owner also has independent discussions/projects concerning a reusable 2D animation engine (kawakaze430/2d-animation-ep-3), VPN, domain reseller, browser and downloader repositories. Those are distinct products. Do **not** transfer their code/PR status, licensing or specifications into build-3d-ai without an explicit product decision.

## 10. Historical conversation timeline (summaries, not transcript)

| Date | Available historical project information and outcome |
|---|---|
| 10 Nov 2026 | Owner explored Marble + Meshy/Tripo + Mixamo + Blender, Codex/Astra automation and Colab GPU for stylized animated episodes; questions on real meshes versus AI video, fast rendering/recording, textures, facial rigs. |
| 10–11 Nov | Adult woman character reference, large expressive eyes with adult body proportions, T-pose, Meshy text/image limits, remesh/retopology, downloaded assets, Mixamo movements and post-rig workflow discussed. |
| 12–13 Nov | Independent Build 3D AI SaaS concept expanded from filmmaking tooling to Meshy/Tripo competitor; reuse-first selection, source/license audit and original product monorepo plan. |
| 13 Nov | Open3DStudio, 3DAIGC-API, Step1X, TRELLIS.2, UniRig, SkinTokens, AssetFurnace, xatlas, glTF-Transform, world generation repos recommended for study; commercial usage warnings recorded. |
| 14 Nov | User requested genuine implementation rather than prototype. Private project backend and gateway PR stack, tests, recoverable jobs and fail-closed model policy progressed; no paid GPU used. |
| 15 Nov | PRs #1 and #14–#25 consolidated/merged, browser studio, S3-compatible storage, identity foundations, quotas and TripoSR candidate added. Most recent main CPU/web CI green, but no actual AI model run. |
| 15 Nov | Owner asked to inspect/merge PRs and push a broad repository study list; 112 verified GitHub repository candidates cataloged in docs/research/OPEN_SOURCE_REPOSITORIES_TO_STUDY.txt directly on main. |
| 15 Nov | Owner supplied a detailed 954-line research/implementation assignment. PR #26 introduced four source-level research/plan docs, exactly two primary repos, a 9-test pip-report audit and a discovered antlr4 sdist release blocker. Three PR CI workflows passed. |
| 16 Nov | Owner requested this permanent master context archive because long ChatGPT threads lose earlier context. Original assignment archived and this master memory created. |

### Important historical uncertainties

- Not all older chats or their precise original wording are accessible. This document records what was visible and verifiable, not invented verbatim transcripts.
- Historical Meshy menu/version UI details, cloud price/credit statements and third-party license/product behavior may have changed; re-verify before current action.
- Uploaded screenshots, personal likeness photographs, reference-video files and unrelated project chats were not copied to this public repository. Only project-relevant textual specifications, provided public links and the owner-supplied technical assignment were included.

## 11. Next precise developer assignment and approval blockers

**Next recommended Codex action:**

1. Use the current feature map and test report. The PR #26 auditor and tests are already recovered; investigate only genuinely unique remaining branch work, retaining the source-archive release gate and newer product behavior.
2. For antlr4-python3-runtime==4.9.3, explicitly inspect its source distribution, build requirements and notices; produce a reproducible independently byte-hashed wheel, or safely substitute a license-appropriate package/runtime. Preserve strict wheel-only release gate.
3. Produce an exact wheelhouse with independent SHA256 validation and a dependency/notice SBOM, including torch/CUDA/OS libraries from the pinned base image. No large hidden downloads or unbudgeted builds.
4. After the dependency/license audit, under approved resource constraints, build/inspect candidate container, headlessly test xatlas/ModernGL and local checkpoint loading. Do not start live paid inference yet.
5. Obtain written owner/legal model/data/SaaS decision and written capped GPU budget/provider/region/shutdown authorization. Only then execute the first real image-to-textured-GLB end-to-end acceptance slice.
6. Update docs/project/FEATURE_MAP.md, AnalyseFuture/TECHNICAL_DEBT.txt, docs/continuity/CODEX_HANDOFF.md and THIS master memory with actual results and a recovery checkpoint. Historical branch-only audit/execution documents remain under AnalyseFuture/historical-implementations/triposr-provenance-research/docs/.

**Before first GPU run, request from owner:** chosen provider/account + region + GPU type, available quota, estimated per-hour rate, allowed maximum total spend, shutdown/cleanup policy and explicit legal approval of exact model/weights/runtime/training-data chain. Credits discussed in old chats are not permission.

## 12. Maintenance contract for this memory document

- Treat this file as a concise-but-rich **project context index**, not an exhaustive log that duplicates every source document and test output.
- Preserve old decisions and dates when superseded; add a dated change note or link to the new PR/ADR instead of silently rewriting history.
- Never paste secrets, raw private image assets, tokens, customer content or sensitive personal chat details into this **public** repository.
- Keep the “current status” table refreshed after meaningful merges/approvals and revalidate CI/PR states live.
- Add new references, external repos, links, benchmark charts/screenshots (only if real and redistributable), measured results and asset paths to the correct canonical docs, then link them here.
- When a new chat begins, paste only the Section 0 recovery prompt and this document URL. An agent should be able to resume by following the actual GitHub code and links.

**End of master project-memory snapshot.**


## 13. Archive organization — 17 November 2026

Historical paths in this section were subsequently relocated under `AnalyseFuture/`; see [the current structure](../../PROJECT_STRUCTURE.md).

The owner requested extraction of all three supplied ZIP archives, removal of the ZIP files after verification, and a direct update to `main` without a PR or additional branch. The imported source snapshots live at `third_party/3daigc-api/` and `third_party/triposr/`; the example bundle keeps its original internal hierarchy under `assets/reference/autorig/`. Existing first-party application and service paths are retained.

Upstream source contents are preserved byte-for-byte with only the outer ZIP directory removed. Original licenses remain with their source. The example bundle contains no license, and the 3DAIGC-API ZIP omits the source of its declared submodules. All imported content is **RESEARCH_ONLY**; extraction is not product integration, model approval or inference evidence.

References: [repository layout](../../README.md#repository-layout), [source snapshot notes](../../AnalyseFuture/third_party/README.md), [reference assets](../../AnalyseFuture/assets/reference/README.md), and [archive inventory and hashes](../../AnalyseFuture/repository-inventory/ARCHIVE_IMPORTS.json). Earlier project and license decisions remain in force.


## 14. Session preservation — 17 November 2026

The owner authorized saving useful session work directly to `main` before losing the workspace and deferred other development. Archive organization was already pushed as `b32f88a`. Preserve this dated event without interpreting it as approval for future paid resources or broad implementation.

The [detailed project idea](../project/BUILD_3D_AI_PROJECT_IDEA.txt) records the existing foundation, ambitious product direction, proposed priorities, limits, conditional future horizons and who would attempt the work. It is a planning proposal, not a claim that proposed features exist or a budget authorization. The [cloud development guide](../development/CLOUD_DEVELOPMENT_ENVIRONMENT.md) and helpers in [scripts/cloud](../../scripts/cloud) preserve reusable installation, startup and browser-test instructions (`install.sh`, `run_web.py`, `playwright.config.cjs`).

Committed files can be recovered from Git. Live processes, installed dependencies, caches, private smoke-test credentials and private application state are not preserved by that Git commit. Recreate or privately restore them as appropriate; never copy credentials into public project memory.

The next technical priority remains one real generation qualification and verified textured GLB/browser/Blender path, subject to existing rights, runtime verification and explicitly bounded spending approvals. Recheck live repository state and follow the [developer handoff](CODEX_HANDOFF.md) before resuming.

## 15. Main project goal adopted — 17 November 2026

The owner explicitly adopted [BUILD_3D_AI_PROJECT_IDEA.txt](../project/BUILD_3D_AI_PROJECT_IDEA.txt) as the main goal for the GitHub repository and requested a direct update to `main`. It is now the primary detailed product direction, linked prominently in the README and referenced by agent instructions and [PRODUCT_VISION.md](../project/PRODUCT_VISION.md). Earlier notes describing the document as an unadopted proposal are historical. Its proposed features and one-/two-/later-year horizons remain conditional; adoption is not evidence of implementation or permission for paid resources. Preserve the existing foundation and follow the document's focused-first-release priorities and acceptance gates.

## 16. Preservation-first structure review — 17 November 2026

The owner reported compromised access and disrupted files, and requested a direct `main` restructure preserving uncertain material in `AnalyseFuture/`. The inspected local and remote main matched previously verified `e4b05f4`; no later main-branch changes were observed. This is not a conclusion about GitHub account access or an independent compromise clearance.

All 242 tracked reference files from `third_party/` and `assets/reference/` were preserved under the corresponding paths in `AnalyseFuture/`. All 240 source/asset files retain their hashes; original copies of the two navigation notes are also retained under `AnalyseFuture/history/`. Active app, qualification service, script, Compose and dependency paths remain compatible. The file index, archive relocation records, [structure guide](../../PROJECT_STRUCTURE.md) and [dated audit](../../AnalyseFuture/recovery-notes/REPOSITORY_AUDIT_2026-11-17.md) document the move and its limits. Default pytest discovery and root Docker context exclude the inactive review area.

The [main project goal TXT](../project/BUILD_3D_AI_PROJECT_IDEA.txt) now includes a structure-review addendum while preserving the detailed vision, existing work, limitations, one-/two-/longer-year horizons and roles. The first real qualified generation/browser/Blender workflow remains the next gated priority; reference relocation does not grant model or spending approval.

Structure-review validation: 136 default first-party Python tests, three preparation-helper tests, four web unit tests, six browser contracts, TypeScript checks, the production web build and both Compose configuration checks passed. File-hash checks retained all 242 original tracked references and all 241 extracted local files (one ignored metadata file); reference scripts/weights were not executed. See the dated audit for boundaries.
