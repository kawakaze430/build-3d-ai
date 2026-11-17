# Ordered Execution Plan — Build 3D AI
Updated: 2026-11-15
Scope: extend the merged private product baseline. Dates and effort are rough engineering ranges, not delivery promises. See CURRENT_STATE_AUDIT.md and TWO_PRIMARY_REPOSITORIES_DECISION.md.

## Immediate critical path

Actual current flow: browser/Next.js BFF -> authenticated tenant API -> durable DB worker -> private 3DAIGC-compatible gateway -> approved model service -> structurally checked GLB -> private filesystem/S3-compatible artifact -> browser download/viewer. Everything through the model service is blocked until an exact model is approved. No production GPU service is deployed.

Priorities: P0 = first authentic image-to-GLB vertical slice, P1 = commercial/better assets, P2 = specialized professional creation. Resources: CPU = local/CI; GPU = later approved compute; LEGAL = explicit source/weight/data/territory approval; OWNER = budget/accounts/operational authorization. Every GPU task remains stopped until both LEGAL and OWNER gates clear.

## Stage 1 — genuine first AI generation (dependency-ordered)

| Task | Current status | Modules/files | Depends on | Resources/effort | Acceptance, tests and blocker |
|---|---|---|---|---|---|
| G01: source+weight pins | Done for candidate only | services/generation/triposr_candidate/runtime_manifest.json; prepare_runtime.py | none | CPU, ~0.5d maintenance | Exact source Git blobs/checkpoint metadata and offline flags verified in tests; no production model approval |
| G02: resolved dependency index evidence | In progress in research PR | audit_pip_report.py; test_audit_pip_report.py; triposr-qualification-ci.yml | G01 | CPU/CI, ~0.5–1d | All direct pins present, package metadata SHA and trusted wheel index provenance recorded; dry-run evidence is not verified wheel bytes |
| G03: complete offline wheelhouse/OS inventory | OPEN | Dockerfile.candidate; requirements-build3d.txt; new build inventory | G02 | CPU build runner, ~2–5d | Audit every resolved wheel byte/hash, sdist build origin, torch/CUDA/system libraries and SPDX notices; reject any unpinned/unknown path |
| G04: digest-pinned candidate image build | OPEN | services/generation/triposr_candidate/ | G03 | CPU builder; several GB image/disk; owner must review resource constraints | Immutable built image SHA/digest, Python/CUDA list, safe offline import; no inference or weight fetch |
| G05: headless bake + exact checkpoint dry load | OPEN | candidate run.py, xatlas, moderngl, textured_glb.py | G04 | GPU may be required for model load; LEGAL/OWNER gate before GPU | Headless ModernGL/xatlas bake, weights_only local checkpoint, no runtime network, content hash and cleanup |
| G06: written legal and budget approvals | BLOCKED | docs/LICENSE_MATRIX.md; FIRST_REAL_GPU_RUNBOOK.md; model-approvals.json | G03–G05 evidence | LEGAL+OWNER, variable | Exact worldwide SaaS source/weight/data/graphics approval plus cloud account/region/quota/hourly+total cap and shutdown procedure |
| G07: one genuine image->textured GLB | BLOCKED | private model worker, gateway/main.py, textual_glb/validation modules | G05+G06 | Approved GPU, ~1–3d qualification | Record input/seed/config/driver/GPU/VRAM/time/cost, actual mesh, PBR/UV/embedded texture validity, reproducible failures |
| G08: private model service integration | OPEN | apps/gateway/upstream.py; apps/api/worker.py; model registry | G07 | CPU integration with controlled GPU test, ~2–5d | Attested allowed exact revision, bounded job submit/poll/download, idempotency/recovery/security/tenant tests |
| G09: viewer+Blender proof | OPEN | apps/web/model-viewer.tsx; Blender headless QA script | G07–G08 | CPU + actual GLB, ~1–2d | Browser screenshot and Blender import/mesh/material/UV measurement of SAME generated file SHA |

Note: the existing textured GLB packager module is apps/gateway/src/build3d_gateway/textured_glb.py; its tests use synthetic OBJ/PNG. G07 must not count those as real generation.

## Stage 2 — generation breadth

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| GEN-TXT: real text-to-3D | OPEN | isolated text-to-image/image-to-3D adapter; apps/api | G09 + legal model approval | GPU/LEGAL/OWNER, 1–3w | Genuine labeled text route, prompt/model lineage and coherent GLB outputs |
| GEN-MV: multiple-view conditioning | OPEN | services/generation/ adapters, web upload | G09 | GPU/LEGAL, 2–5w | Uses >=2 reference images and outperforms single-image held-out consistency baseline |
| GEN-MODE: quality/cost tiers | OPEN | registry, jobs, web selector | G09 + benchmarks | CPU/GPU/OWNER, 1–3w | Measured job cost, quality and VRAM rather than labels without proof |
| GEN-HISTORY: reproducible variations | Partial | store.py, studio.tsx, runtime manifest | G07 | CPU, 3–6d | Per-job seed/config/model hash captured and reproducible on same release |

## Stage 3 — professional meshes and materials

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| GEO-QA: deep mesh/material validator | Structural GLB only | glb_validation.py; Blender/glTF Validator adapters | G09 | CPU, 1–2w | Vertex/index bounds, material maps, UV island checks, external URI policy, import smoke test |
| GEO-UV: UV/PBR cleanup | Partially synthetic packager | textured_glb.py; xatlas, glTF-Transform | G09 | CPU, 1–3w | Valid baked UVs, occlusion/normal/roughness expectations and seams against reference |
| GEO-RETOPO: editable quad/animation mesh | OPEN | isolated Blender/mesh processing service | GEO-QA | CPU, 3–8w | Controlled poly budgets with deformation/face topology and projection metrics |
| GEO-EXPORT: FBX/OBJ/BLEND | OPEN | converters, Blender batch jobs | GEO-QA | CPU, 1–3w | Import/export compatibility tests for every advertised format; no fake suffix conversions |

## Stage 4 — reusable stylized adult characters and motion

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| CHAR-BASE: consistent adult bodies/faces | OPEN | character generation profiles / model R&D | G09+GEN-MV | GPU+licensed data, 4–10w | Held-out adult proportions, multi-angle eye/facial identity and garment consistency |
| CHAR-RIG: skeleton + skin weights | OPEN | UniRig/SkinTokens adapters; Blender | GEO-RETOPO | CPU/GPU, 3–8w | Clean walk/run/arms tests and standard Blender bones, no major deformation tears |
| CHAR-FACE: eyes/brows/jaw/visemes | OPEN | Blender shape keys, corrective rig, facial tests | CHAR-RIG | CPU/artist QA, 4–10w | Look-around, blink, brow, smile/frown, working jaw/mouth interior and speech visemes |
| CHAR-MOTION: motion retarget/lip-sync | OPEN | Blender animation and audio services | CHAR-RIG+CHAR-FACE | CPU/GPU optional, 2–6w | Talking with gestures and synchronized phoneme shapes, Blender render/playback proof |

## Stage 5 — environments

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| ENV-GRAPH: editable scene graph | OPEN | services/scenes; OpenUSD/Blender interfaces | G09 | CPU, 4–8w | Room/house/street with independently selectable objects and transforms |
| ENV-WORLD: procedural rooms/terrain | OPEN | BlenderProc/Infinigen-inspired worker | ENV-GRAPH | CPU/GPU, 4–10w | Reproducible scene graph, materials and Blender export |
| ENV-SPLAT: optional neural/splat world | OPEN | isolated nerfstudio/gsplat research adapter | ENV-GRAPH | GPU+LEGAL, 4–8w | Explicit splat vs polygon mode, no false claim of editable mesh |

## Stage 6 — safe commercial service

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| SAAS-ID: Better Auth browser lifecycle | JWT foundation only; disabled | apps/web; trusted_identity.py; migrations | CPU security design | CPU, 3–6w | Signup/email verification/session/CSRF/rotation/reset/deletion tests and no auth bypass |
| SAAS-BILL: credit ledger/payments | OPEN | apps/api; webhook handler | G07 cost telemetry+identity | CPU + owner provider approval, 3–6w | Idempotent credit reserve/settle/refund and webhook replay tests |
| SAAS-OPS: deployment/queue/telemetry | Partial local compose | infra; worker.py, metrics | G07+G08 | CPU/cloud approval, 3–8w | Staging with private networking, backups, audit logs, observed cost and canary rollback |
| SAAS-RETENTION: customer deletion+backup | Byte quota/migration implemented | storage.py; maintenance.py; DB | ID+owner policy | CPU, 2–4w | Audited reversible deletion/retention, no orphan leaks, backups and restore tests |
| SAAS-API: public developer API | Private tenant API only | apps/api, docs/contract | SAAS-ID+BILL | CPU, 2–5w | OAuth/API keys, quotas, docs, webhooks, abuse limits and idempotency |

## Stage 7 — custom models

| Task | Status | Modules | Depends | Resources/effort | Acceptance |
|---|---|---|---|---|---|
| ML-DATA: licensed provenance set | OPEN | training/data manifests | G09 benchmark protocol | LEGAL, 3–8w | Per-asset rights, dedupe, splits, provenance, removal requests |
| ML-FINETUNE: specialize adult characters | OPEN | isolated training service and checkpoints | ML-DATA+approved baseline | GPU+OWNER+LEGAL, 6–16w | Reproducible training and held-out improvement over pinned baseline |
| ML-RELEASE: safe rollback/model registry | Approval policy foundation only | model registry; deployment | ML-FINETUNE | CPU/GPU, 2–5w | Exact weight hash, model card, cost, staged rollout and rollback test |

## Resource policy / priorities

CPU-only now: G02, much of G03, web/auth security design, backup and test spec work.
Build resources needing review: G04 image several GB and underlying package downloads; no automatic massive downloads in CI.
GPU+owner/legal blocked: G05 if CUDA model load, G06/G07 and all dependent GPU tasks.
Provider/account: AWS L4 is only a candidate. Confirm credits, quota, region, expected hourly price and maximum authorized spend freshly; do not assume old credit balance is usable. No infrastructure was provisioned in this assignment.

## Validation and next engineer handoff

Immediate next task: collect/validate a complete dependency-wheel and base-container inventory for TripoSR at the pinned platform. The new audit_pip_report.py records pip's index-reported SHA256 values in CI but explicitly does not hash downloaded wheel bytes. Do NOT mark G03/G04/G05 complete because it runs.

Suggested commands after this PR:
- python -m unittest discover -s services/generation/triposr_candidate -p test_audit_pip_report.py -v
- python -m pytest -q services/generation/triposr_candidate/test_prepare_runtime.py services/generation/triposr_candidate/test_audit_pip_report.py
- git review of upload artifact triposr-candidate-index-provenance from TripoSR Qualification CI
- per runbook: build and inspect exact base and dependency images only after resource approval; never run build3d-gpu-smoke --confirm-gpu-spend until owner and legal approvals

Use one reviewed, narrowly scoped PR per acceptance group. Protect existing monorepo code and the zero-approved-model policy.
