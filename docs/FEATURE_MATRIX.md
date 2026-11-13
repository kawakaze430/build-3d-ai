# Master Feature Matrix

**Status convention:** Every row here is **PLANNED** until linked to a tested implementation PR and evidence. P0=initial deployable product, P1=commercial expansion, P2=advanced development.

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

## User experience

A user must be able to: sign in → upload or prompt → choose quality/model (where supported) → monitor a genuine job → inspect the rotating mesh → view materials/geometry limits → download an asset → reopen project later.

No fake “working” generation using sample meshes. Expose errors, queue delays and unsupported formats honestly. For training or 3D generation jobs, retain reproducible model/weight hashes and configurations.

## Definition of done

Tested implementation + legal approval + observable metrics + secure data handling + documented limit/rollback. Any row without evidence remains planned.
