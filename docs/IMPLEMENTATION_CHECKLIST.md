# Complete Ordered Implementation Checklist

**Status:** PLANNED unless explicitly checked below and linked to verified proof. This checklist is the canonical execution order for Codex and developers, not a claim that the product is complete.

**Objective:** An independently owned, commercially operable Meshy/Tripo-class AI 3D creation studio: text/image/multiview to 3D, PBR, editable geometry, UV/retopology, rigs, animation, environments, APIs, customer accounts and fine-tuned models.

**Execution rules:** never spend paid GPU/credit without approval; reuse before custom-building; every source/weight/dependency requires commercial-license clearance; a stub/mock is never “implemented”; first create a working vertical slice, then broaden scope. Mark status as: [ ] planned, [x] completed and verified. Blocked means OPEN, not DONE.

## Phase 0 — Repo, legality, testable core (critical path)

- [x] **00.01** Establish owner-controlled GitHub repository and complete high-level engineering docs. Proof: README and docs already on main.
- [x] **00.02** Verify actual upstream 3DAIGC-API endpoints and Open3DStudio project existence. Proof: published upstream README/routes and repository metadata examined 2026-11-13.
- [ ] **00.03** Inventory actual code in upstream Open3DStudio, 3DAIGC-API and AssetFurnace at pinned commit SHAs; audit tests, maintenance and API compatibility.
- [ ] **00.04** Create source/model/weight/dataset/transitive-dependency commercial license matrix; block noncommercial/restricted integrations.
- [ ] **00.05** Decide frontend foundation: adapt Open3DStudio vs. clean-room product UI based on actual fit/maintainability.
- [ ] **00.06** Decide one commercially cleared baseline 3D checkpoint and GPU runtime; pin full dependency graph.
- [x] **00.07** Add working, authenticated upstream integration gateway, tests and CI. Proof: apps/gateway and passing GitHub Actions on Python 3.11/3.12; **unit/contract tests only, no GPU validation**.
- [ ] **00.08** Obtain owner-approved GPU account, instance quota, allowed region, max hourly spend and stop conditions.
- [ ] **00.09** Start license-cleared upstream GPU backend privately; prove real image→textured mesh→downloaded, validated GLB.
- [ ] **00.10** Benchmark 20 sample inputs: geometry, textures, VRAM, time, error rate, and full cost/job.
- [ ] **00.11** Decide Go/No-Go and record actual blockers; no large spend before this gate.
- [x] **00.12** Add repository CI for both Python 3.11/3.12; tests compile the gateway and verify upstream HTTP contract via isolated in-memory transport. Proof: GitHub Actions run 43470562375 (passed).
- [x] **00.13** Add structural validation of self-contained GLB 2.0 exports, bounding 250 MiB downloads and reporting SHA256/mesh count; offline test coverage only. Proof: apps/gateway/src/build3d_gateway/glb_validation.py and tests/test_glb_validation.py.
- [x] **00.14** Add gated real-job GPU smoke runner for explicit model choice, owner spend acknowledgement, job polling, validated GLB download, checksum and timing report. Proof: build3d-gpu-smoke CLI + synthetic HTTP tests; **no paid GPU run has occurred**.

## Phase 1 — Durable owner-controlled product backbone

- [ ] **01.01** Monorepo contracts: versioned API schemas, worker registry, model IDs, job and artifact types.
- [ ] **01.02** PostgreSQL migrations for users, projects, jobs, artifacts, provenance, permissions and ledger.
- [ ] **01.03** User signup/login, secure sessions, password reset and account deletion; do not expose upstream admin token.
- [ ] **01.04** Tenant-level authorization tests for jobs/files/downloads and signed asset URLs.
- [ ] **01.05** Private object storage with checksums, image upload validation, retention and cleanup.
- [ ] **01.06** Durable queue, idempotency, retriable workers, cancellation, timeouts and dead-letter queue.
- [ ] **01.07** GPU scheduler with model registry, per-model VRAM limits, concurrency, cold-start and eviction.
- [ ] **01.08** Real text-to-3D (or explicitly labeled text→image→3D), image-to-3D, user selectable quality.
- [ ] **01.09** Browser studio with prompt/upload, jobs, failure details, history and model/version selector.
- [ ] **01.10** Three.js viewer with turntable, camera reset, material/wireframe views and secure real-model downloads.
- [ ] **01.11** Automatic mesh validation and GLB export with Blender/glTF import smoke tests.
- [ ] **01.12** First end-to-end production-like deployment in isolated staging; load, access-control and recovery tests.

## Phase 2 — Professional asset creation

- [ ] **02.01** Selective texture generation and true PBR: albedo, normal, roughness, metalness.
- [ ] **02.02** UV unwrap (prefer tested xatlas), packing, inspection and seam quality metrics.
- [ ] **02.03** Geometry cleanup, decimation, mesh integrity and polygon budget controls.
- [ ] **02.04** Smart retopology research/benchmark, not just decimation; deformation-aware quality evaluation.
- [ ] **02.05** Mesh part segmentation and part-aware editing under commercially usable dependencies.
- [ ] **02.06** Multiple reference views with genuine multi-view conditioning, not a single-image trick.
- [ ] **02.07** Texture repaint and regional edits, versioning/undo and repeatable parameters.
- [ ] **02.08** Verified GLB, OBJ, FBX and BLEND exports; scale/orientation/texture import tests.
- [ ] **02.09** Batch assets, processing presets, model/seed/config provenance and project revisions.

## Phase 3 — Animation-ready character platform

- [ ] **03.01** Benchmark adult stylized characters, faces, hands, hair and clothing from all directions.
- [ ] **03.02** Evaluate UniRig, SkinTokens and other body skeleton + skinning approaches; license-check weights.
- [ ] **03.03** Body rigs with clean deformation tests for walk, run, sit, arm gestures.
- [ ] **03.04** Retarget/licensed motion library, controllable character proportions, export to Blender.
- [ ] **03.05** Eyes rotation, eyelid blinking and eye contact/gaze controls.
- [ ] **03.06** Brows, smile/frown, jaw articulation, mouth interior and deformation-ready face topology.
- [ ] **03.07** Visemes/phonemes, lip sync, expression mixing and speech animation validation.
- [ ] **03.08** Consistent characters across poses, outfits, versions and scenes; measured identity preservation.

## Phase 4 — Custom models and competitive quality

- [ ] **04.01** Build approved training dataset with per-asset commercial rights, original meshes, multi-view renders and camera metadata.
- [ ] **04.02** Reproducible preprocessing, filtering, deduplication and asset-disjoint train/val/test splits.
- [ ] **04.03** Freeze a 100+ item quality benchmark including faces, complex geometry and difficult material cases.
- [ ] **04.04** Run Step1X-3D LoRA / supported 3D fine-tune in bounded, owner-approved GPU experiment.
- [ ] **04.05** Compare model to base and selected commercial baselines with blind multi-view reviews and actual costs.
- [ ] **04.06** Version/checkpoint registry with rollout, regression evaluation, canary and rollback.
- [ ] **04.07** Repeat only if measurable gains; expand models, architecture or dataset when data justify it.

## Phase 5 — Environments and complete studio

- [ ] **05.01** Editable scene graph with terrain, buildings, props, lights, cameras and collections.
- [ ] **05.02** Scene composition/layout from text and images with editable per-object geometry.
- [ ] **05.03** Splat/world-generation R&D separately from mesh scene editing; mark export limitations clearly.
- [ ] **05.04** Scene-to-Blender/engine export with correct transforms, materials, object IDs and dependencies.
- [ ] **05.05** Project collaboration, asset library, sharing permissions, version history and review tools.
- [ ] **05.06** Unity, Unreal and Blender integrations; public developer API, SDKs and webhooks.

## Phase 6 — Commercial-scale product and launch

- [ ] **06.01** Brand, marketing site, product UX and accessibility; do not copy competitor assets.
- [ ] **06.02** Subscription tiers, prepaid credits, durable ledger, usage invoices and failed-job reversals.
- [ ] **06.03** Payment webhook security, tax/regional compliance and customer service operations.
- [ ] **06.04** GPU spend limits, per-customer quotas, abuse protection, uploads sandbox and malware processing.
- [ ] **06.05** Audit logs, secrets vault, least-privilege IAM, encrypted storage, backups and restore drills.
- [ ] **06.06** Metrics/logs/traces, SLA/SLO monitoring, retry and queue observability, status page.
- [ ] **06.07** Load tests at projected traffic, cost-per-asset economics and cloud autoscaling.
- [ ] **06.08** Full legal clearance, customer terms/privacy policy, rights and training-data opt-in controls.
- [ ] **06.09** Closed beta with real creators, bug prioritization and human benchmark comparisons.
- [ ] **06.10** General availability decision based on security, reliability, cost and quality gates.

## Priority blockers — assign Codex or owner

| ID | Blocker | Owner | Exit condition |
|---|---|---|---|
| B01 | Production GPU compute and credits availability | Owner | Approved quota, budget, limits and provider account |
| B02 | Full code+model+weight+dependency commercial license clearance | Legal/engineering | Written verdict for selected engine and complete chain |
| B03 | Upstream backend private deployment with valid model | Codex + Owner | Live health/models and real inference smoke test |
| B04 | UI foundation suitability and upstream version drift | Codex | Pinned commit/build and integration regression tests |
| B05 | Real identity, data isolation and billing | Codex + security review | Production tests, tenant security and ledger invariants |
| B06 | High-quality facial rigs and editable full environments | R&D | Measured prototype-independent production benchmarks |

## How to hand this to Codex

1. Read AGENTS.md and all existing docs. Compare current code to this checklist.
2. Begin with 00.03/00.04 license/code inspection and 00.07 integration CI; **do not spend GPU credits**.
3. For each item create a scoped issue/PR with actual results; only check an item when evidence exists.
4. Never substitute an AI mock for real inference. Keep research/test fixtures separate from production.
5. Move to the next blocked item only after obtaining the required owner approval.

**Important:** This initial checklist is comprehensive but must evolve with real research and changing model/software releases.