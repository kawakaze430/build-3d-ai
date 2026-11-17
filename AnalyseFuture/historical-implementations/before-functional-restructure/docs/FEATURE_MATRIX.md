# Master Feature Matrix

Current implementation reconciliation: 17 November 2026. The [pre-review version](../AnalyseFuture/historical-implementations/documentation-before-universal/docs/FEATURE_MATRIX.md) preserves the exact document from baseline `56f412f`; historical results remain scoped to their recorded runs.

**Status convention:** Rows below describe broad release requirements, not claims that every subfeature is absent or complete. Implemented private slices are listed separately; use the [granular feature inventory](../AnalyseFuture/FEATURE_INVENTORY.txt) and [ownership map](FEATURE_MAP.md) for current code/evidence. P0=initial deployable product, P1=commercial expansion, P2=advanced development.

**Verified private product slices, 15 Nov 2026:** APP01/APP02 now include operator-provisioned user keys, private projects/history, durable queue admission, worker recovery, browser studio workflows and verified private downloads. The browser viewer loads the real product download route and is contract-tested with a clearly synthetic GLB fixture. Artifact storage has filesystem and S3-compatible implementations behind configuration. Persistent per-user byte quotas, read-only scanning, copy-only storage migration, immutable identity mapping and optional API JWT/JWKS validation are implemented. These are **not complete commercial features**: public browser identity/account lifecycle, retention/deletion, real cloud-storage qualification, upstream cancellation, deployment and real GPU/model validation remain open. GEO01/EXP01 still require proof using a genuinely generated artifact and Blender/viewer import. [Backend evidence](PRODUCT_BACKBONE.md), [storage design](OBJECT_STORAGE.md), [identity decision](IDENTITY_AND_ACCOUNT_LIFECYCLE.md).

| ID | Feature | Priority | Release acceptance |
|---|---|---|---|
| GEN01 | Single image → 3D geometry | P0 | Real checkpoint generates importable mesh; logs time/VRAM |
| GEN02 | Text → 3D | P0 | Real, labeled pipeline; prompt lineage recorded |
| GEN03 | Textured GLB/PBR preview | P0 | Actual material/texture maps verified |
| GEN04 | Multiple reference images/views | P1 | True multiview conditioning and test evidence |
| GEN05 | Alternate model-quality/speed modes | P1 | Reproducible benchmarks and costs |
| GEN06 | Consistent stylized characters | P2 | Measured identity/proportion gains across views |
| GEO01 | Mesh validation/cleanup | P0 | Geometry finite and file importable, errors reported |
| GEO02 | UV unwrap and compression | P1 | Reuse tested tools; UV coverage and GLB size measured |
| GEO03 | Smart retopology and poly budget | P1 | Deformation/boundary quality checked, limits stated |
| GEO04 | Semantic part segmentation and local edit | P2 | Editable semantic parts verified |
| MAT01 | PBR materials, texture bake and inspection | P1 | Maps, UV seams and render test |
| MAT02 | Prompt/image-driven texture repaint | P2 | Region control and version history |
| RIG01 | Body auto-rigging and skin weights | P1 | Skeleton + deformation smoke test |
| RIG02 | Motion library and animation retargeting | P1 | Walk/run/gesture/talk test in Blender |
| RIG03 | Eyes, blinking, brows, jaw and mouth | P2 | Facial controls tested on target characters |
| RIG04 | Visemes/lip sync and expression controls | P2 | Mouth shapes + audio timing demo verified |
| ENV01 | Editable scene graph, terrain, object placement | P2 | Objects stay individually editable |
| ENV02 | Gaussian splat / world generation mode | P2 | Format and editing limitations explicit |
| EXP01 | GLB output and Three.js viewer | P0 | File validates and opens |
| EXP02 | OBJ, FBX and Blender export | P1 | Each export actual import-tested |
| APP01 | Secure user account, projects, asset history | P0 | Authorization tests pass |
| APP02 | Jobs, cancellation/retry and download | P0 | Durable state and failure recovery |
| APP03 | Credits/subscriptions and payment ledger | P1 | Webhook idempotency and refund behavior proven |
| APP04 | Public developer API and plugins | P2 | Auth, quotas, docs and webhook tests |
| OPS01 | Production packaging, CI, AWS GPU service | P0 | Repeatable builds and approved deployment |
| OPS02 | Cost and usage telemetry, monitoring | P0 | Per-job GPU/cost report |
| ML01 | Benchmark datasets/evaluator | P0 | Fixed permitted test set and scoring protocol |
| ML02 | Fine-tuning dataset/provenance | P1 | Per-asset usage rights and split checks |
| ML03 | Specialized fine-tuned model | P1 | Repeatable measurable gain vs base |

## Implemented slice boundaries

APP01 includes private API-key identity, product ownership, projects and persisted history; full public account lifecycle and asset versions remain open. APP02 includes durable admission, idempotency, fenced recovery, bounded polling, queued-only cancellation and verified downloads; it does not implement remote cancellation or automatic generation retries. GEO01/EXP01 include structural GLB checks, synthetic OBJ+PNG packaging and the product viewer path, while real generated asset/Blender proof remains unverified. OPS01 includes development/CI/Compose packaging, not deployed GPU hosting.

The BFF now shares bounded streamed-body reading (12 MiB product requests; 8 KiB login). The studio uses its existing download URL helper. First-100 project/job display and a slow-poll response race remain technical debt; persisted backend history must not be described as fully browsable UI history.

## User experience

A user must be able to: sign in → upload or prompt → choose quality/model (where supported) → monitor a genuine job → inspect the rotating mesh → view materials/geometry limits → download an asset → reopen project later.

No fake “working” generation using sample meshes. Expose errors, queue delays and unsupported formats honestly. For training or 3D generation jobs, retain reproducible model/weight hashes and configurations.

## Definition of done

Tested implementation + legal approval + observable metrics + secure data handling + documented limit/rollback. Any row without evidence remains planned.
