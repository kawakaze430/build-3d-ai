# Actionable Engineering Backlog

This is an implementation-ready task list **not a claim that tasks have been completed**. Create GitHub issues as execution begins; link PRs and test evidence.

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

## Immediate Codex instruction

**Start with tasks 0–5, in order.** Do not initiate paid cloud resources, download massive weights or commit secrets. Produce verified audit files and an inexpensive reproducible smoke test plan if GPU access is not yet approved. At most one tested end-to-end vertical slice per implementation PR.
