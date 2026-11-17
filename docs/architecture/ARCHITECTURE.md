# Current Architecture and Expansion Boundaries

Current implementation reconciliation: 17 November 2026. The [pre-review target architecture](../../AnalyseFuture/historical-implementations/documentation-before-universal/docs/ARCHITECTURE.md) preserves the exact `56f412f` document, including its dated 14 November snapshot and proposed skeleton.

## Implemented runtime

```text
Browser studio (apps/web)
  -> private Next.js session and allowlisted BFF routes
  -> tenant product API (apps/api, port 8081)
       -> SQLAlchemy database: users, keys, projects, durable jobs, artifacts
       -> owner-scoped, revalidated downloads
            -> filesystem storage (default) / optional S3-compatible backend

Bounded operator worker (build3d-worker)
  -> same database, storage settings and approval policy as the product API
  -> reused build3d_gateway upstream client
  -> separately deployed private model server (not provided/running by default)

Separate operator gateway (apps/gateway, port 8080)
  -> control-key protected upstream catalog/status/generation/download contract
  -> fail-closed reviewed model policy; bounded GLB preflight
```

The studio and storage abstraction are implemented; they are not merely future diagram boxes. SQLite is the local development default. PostgreSQL has a dedicated integration-test path and Compose packaging. Neither the presence of packaging nor previous database tests proves a deployed production service.

The durable queue is implemented in the relational database with conditional claims and fencing. AWS SQS, global GPU scheduling and autoscaling are future choices, not current runtime dependencies. Do not introduce a second queue or duplicate worker merely to match the old target diagram.

## Responsibility and dependency map

| Component | Responsibility | Important boundary |
|---|---|---|
| `apps/web` | Studio, private API-key cookie, allowlisted tenant BFF, GLB inspection | Browser does not receive operator/upstream credentials or arbitrary proxy destinations |
| `apps/api` | Product ownership, migrations, projects/jobs, admission limits, recovery, artifact lifecycle | All tenant work resolves to the same product owner model |
| `apps/gateway` | Reusable upstream client, model policy, GLB validation/packaging and operator app | Administrative routes are separate from the tenant API |
| `services/generation/triposr_candidate` | Guarded qualification preparation and dependency-report auditing | Qualification-only; no automatic weights download or approved inference |
| `config` | Static example configuration, including reviewed identity provider shape | Never derive a provider/JWKS destination from untrusted token claims |
| `scripts/cloud` | Recreate CPU development and isolated browser-contract workflow | No worker, paid resources or model loading during setup |
| `AnalyseFuture` | Inactive source/reference preservation and audit evidence | Excluded from default test discovery and root Docker build context; not an execution sandbox |

The Python API package depends on the local gateway package and reuses its client, policy and verifier. It does not copy upstream AI modules into the product process. The Next.js BFF talks only to the tenant API. Each future GPU engine needs an independently reviewed environment because its CUDA/PyTorch and licensing dependencies can differ.

## Implemented contracts and known limits

- Operator-provisioned API keys are the default identity mechanism. Immutable external issuer/subject mapping and asymmetric JWT/JWKS validation exist behind a disabled-by-default flag. Public browser signup/session lifecycle and BFF assertion issuance remain open.
- New jobs retain input/provenance, idempotency keys and exact model approval metadata. Worker leases/fences guard local state. Bounded read/poll retries are distinct from non-idempotent generation POSTs; uncertain submissions require reconciliation rather than blind resubmission.
- Filesystem and optional S3-compatible storage implement private deterministic keys, checksums and verified downloads. Persistent byte quotas, bounded read-only scanning and copy-only filesystem-to-S3 migration exist. No automatic retention or customer deletion is enabled.
- Downloads use the product integrity boundary rather than public/presigned redirects. The GLB validator proves bounded structure and embedded resources; it does not establish artistic quality, clean topology or Blender deformation.
- The studio provides the real viewer/download route but currently fetches only the first 100 projects/jobs. A slow polling response can still race project navigation. These are open UI correctness/completeness tasks.
- Shared streamed-body reading bounds product BFF requests to 12 MiB and login JSON to 8 KiB. It does not replace API image decoding, transport ingress controls or execution sandboxing.
- The recovered pip-report auditor records resolver/index metadata, exact direct pins and source-archive blockers. It does not independently download/hash a wheelhouse or approve the model runtime.

See the [feature ownership map](../project/FEATURE_MAP.md), [product contracts](../operations/PRODUCT_BACKBONE.md), [storage lifecycle](../operations/OBJECT_STORAGE.md) and [identity boundary](IDENTITY_AND_ACCOUNT_LIFECYCLE.md).

## Expansion targets

The [main project goal](../project/BUILD_3D_AI_PROJECT_IDEA.txt) defines the long-term direction. Start by qualifying one actual image-to-textured-GLB path through the existing product and Blender import. The default policy has zero approved models, and no real inference is established by the current fixture tests.

Later work can add asset versions, tested processing utilities, body and face preparation, editable scenes and model-specific adaptation. Each capability needs its own downstream acceptance and rights review. Billing ledgers, public accounts, email delivery, GPU budgets, production observability, backups/restore and deletion policy are separate release requirements.

Retain framework/package conventions and root packaging paths. Create shared modules only for compatible responsibilities actually reused; do not force Python packages and Next.js routes into a generic feature directory. The [structure guide](../../PROJECT_STRUCTURE.md) records present locations; the [future-roadmap supplement](../../AnalyseFuture/PROJECT_VISION_AND_FUTURE_ROADMAP.txt) describes conditional research rather than implemented service boundaries.

## Expanded creation, world, agent and training boundaries —17November2026

The owner expanded the target to image/text/genuine multi-image inputs for both
3Dassets and environments,geometry/material editing,rigs/motions,an AIworkflow
agent and future fine-tuned models. These are proposed extensions,not additional
running services. Read [the detailed task handoff](../../PROJECT_STATUS_AND_TASKS.md)
and [future fine-tuning research](../../research.md). Existing private product
components and their ownership/transaction/fencing/integrity contracts remain
canonical. Latest delivery policy is verified milestones pushed directly to main.

| Proposed extension | Integration boundary and first useful slice | What is not implemented/assumed |
|---|---|---|
| Capability-aware generation/processing | GEN/ART/ANIM adapters declare exact supported modalities,formats,model/runtime provenance and resource limits; reuse tenant admission,SQLqueue and approval policy. Start with one accepted adapter/profile. | A commercial Tripo SDK is distinct from open TripoSR; the current3DAIGC-style client is not automatically a Tripo/Meshy/Marble integration. |
| Asset versions and processing stages | ART-01 supplies one immutable asset-version/lineage authority; edits/UV/material/rig/export stages retain owner and byte accounting. | No alternate asset database or silent overwrite; skeleton/material filename alone is not downstream acceptance. |
| Worlds and environments | ENV-01 declares a bounded owned scene manifest; ENV-02 adds a modular editable scene. Separate polygon,splat/neural,panorama and collision layers need their own validators,quota and delivery contracts. | Do not rename PLY/splat/sceneZIP as GLB or infer semantic objects/collision from a render; worlds are not shipped. |
| Product AIagent | AGENT read tools/plans/typed adapters enforce server-side owner/version/capability/resource scope and reuse existing operations. Reads and reversible edits can proceed within approved scope; extra external/destructive/spend actions need their actual authorization. | No second job dispatcher,no arbitrary shell/SQL/proxy tool,no prompt-derived permission or self-approved budget. Agent not implemented. |
| Fine-tuning research/runtime | RES tasks select one suitable task/base,licensed dataset,safe preprocessing,held-out evaluator and approved bounded experiment. A justified services/training/<selected-task>/ harness is proposed,isolated from CPU product and GPU inference environments. | No universal LoRA recipe,training dataset,trained checkpoint or approved run; don't merge incompatible CUDA environments. |
| Model release | Reviewed base/adaptation/runtime/data provenance flows into one release/model registry and the existing approval boundary; pilot/rollback preserves known-good versions. | Fine-tuning does not automatically clear base rights,improve held-out quality or enable a production model. |

Schema/module names proposed in task cards become real only in a verified
implementation milestone. Coordinate shared Studio/store edits and preserve
history rather than introduce a duplicate active implementation. Structure and
QA cards list actual documentation drift/maintenance gaps and required tests;
conventional Next.js/Python package boundaries and inactive upstream snapshots
are intentional. No application tests,model execution or training ran for this
architecture documentation update;prior253executions retain their dated scope.
