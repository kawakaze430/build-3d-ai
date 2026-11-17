# Actionable Engineering Backlog

Current implementation reconciliation: 17 November 2026. The [pre-review version](../AnalyseFuture/historical-implementations/documentation-before-universal/docs/BACKLOG.md) preserves the exact document from baseline `56f412f`; historical results remain scoped to their recorded runs.

This file preserves the original backlog and adds current sequencing. It is **not a claim that broad product tasks are complete**. Reuse existing implemented slices before opening work. See the [feature ownership map](FEATURE_MAP.md), [granular inventory](../AnalyseFuture/FEATURE_INVENTORY.txt) and [execution checklist](IMPLEMENTATION_CHECKLIST.md). Normal review conventions remain subject to the current user-authorized delivery workflow.

| Order | Task | Definition of done |
|---|---|---|
| 0 | Audit current GitHub state | Existing content and branch baseline recorded |
| 1 | Inventory public repos and licenses | Source/model/weight/dependency matrix, candidates approved or blocked |
| 2 | Cost and GPU viability | Explicit approved budget, region/quotas, estimated per-job baseline |
| 3 | App foundation decision | Open3DStudio/3DAIGC-API tested; build-vs-reuse ADR |
| 4 | CI, container and local test skeleton | Repeatable non-GPU checks and test commands |
| 5 | First **real GPU** image-to-3D | Valid GLB, actual inference, time/VRAM/logs, source lineage |
| 6 | User auth, data model and private uploads | Cross-tenant access tests and signed URLs |
| 7 | Job queue, dispatcher and cancellation | Bounded retries, idempotency, DLQ, cost instrumentation |
| 8 | Website, model preview and project library | Complete user upload/generate/download journey |
| 9 | Text→image→3D integration | Real model output, correct labeling and prompt provenance |
| 10 | UV, PBR and mesh optimization | Reused verified libraries, GLB and Blender import checks |
| 11 | Evaluation platform | Frozen inputs, multi-view quality, failure and cost scorecard |
| 12 | Metering, subscription and credits | Auditable ledger, failed-job credits return, webhooks tested |
| 13 | Body auto-rigging and motion library | Deformation tests, retarget, export |
| 14 | License-curated dataset + fine-tune | Reproducible LoRA experiment and performance gain |
| 15 | Multi-reference and targeted asset edits | Repeatable, editable output with real test evidence |
| 16 | Facial rig and lip-sync research | Eye/jaw/brows/blinks/visemes in Blender |
| 17 | Editable environments and scene graph | Terrain, props, export; splats separate |
| 18 | Developer API and plugin integration | Auth, quotas, versioning, docs |
| 19 | Production hardening | Load, backup restore, observability and security testing |

## Each task/PR must include

Problem; user outcome; current code inventory; existing open-source alternative; licenses; expected inputs and outputs; measurable acceptance; test commands and actual results; security review; GPU cost impact and cap; rollback; documentation updates.

## Current next work — 17 November 2026

1. Use the current repository audit and feature inventory to avoid rebuilding the working API, worker, storage, studio, JWT boundary and CI. The table above records the initial work sequence; completed private slices are credited in the checklist.
2. Finish the exact candidate runtime/dependency review. The recovered pip-report auditor inventories index metadata and source-archive blockers; it is not a verified wheelhouse or production approval.
3. Under the separate model/license and bounded GPU budget approvals, prove one real generation→textured GLB→product viewer→Blender workflow.
4. Repair the bounded UI debts: project/job pagination beyond the current first 100 and stale slow-poll results during navigation. Preserve current ownership and quota behavior.
5. Complete public browser lifecycle, retention/deletion, backup restore, metering and operational readiness only as justified by the supported pilot.

Do not initiate paid cloud resources, download massive weights or commit secrets merely to execute this backlog. Keep each implementation change bounded and verified; use direct-main or PR delivery as explicitly authorized for that task.
