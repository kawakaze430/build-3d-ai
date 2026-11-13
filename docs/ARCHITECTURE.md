# Target Architecture

**Proposed, not deployed.**

```text
Browser / Developer API
   |
Next.js Studio + Three.js/React Three Fiber Viewer
   |
FastAPI Backend ---- Authentication & Policy ---- PostgreSQL
   |                                  |
Durable Job Queue (SQS) ---- GPU Dispatcher / Model Registry
   |                  |                |                 |
Image/Text → 3D    Texture/UV      Rig/Animation      Scene Generation
isolated worker    worker          worker             worker
   |                  |                |                 |
   +------------------+----------------+-----------------+
                         |
                 Blender / mesh validation
                         |
           Private S3 assets, verified GLB/exports
                         |
                 Signed customer downloads
```

## Monorepo skeleton (planned)

```text
apps/web                 UI, 3D viewer, customer project library
apps/api                 Auth, billing ledger, admin, job API
services/orchestrator    Model routing, queue, retries, cancellation
services/generation      Model adapters (GPU containers pinned separately)
services/processing      UV, textures, mesh repair, exporters
services/rigging         Body, face and animation workers
services/scenes          Editable environment/scene graph
packages/contracts       Typed API, job/artifact schemas
training                 Data prep, configs, evaluation, weights metadata
infra                    Docker, Terraform, CI, observability
tests                    Unit, contract, E2E, GPU and Blender-import tests
docs                     Specs, runbooks, architecture decisions
```

## Engineering choices

- **Reuse code, not chaos:** evaluate Open3DStudio/3DAIGC-API as base candidates. Prefer adapters and version-pinned modules over huge vendor dumps. Each GPU engine gets its own tested environment to avoid CUDA conflicts.
- **Backend:** authenticated FastAPI, PostgreSQL, durable queue, idempotent jobs, limited retries, dead-letter queue, cancellation and credit refund.
- **Assets:** immutable object IDs, content hashes, provenance, private buckets, time-limited download signatures and configurable retention.
- **Model routing:** registry includes source, license decision, exact weights hash, VRAM, cost, supported outputs, quality profile and rollback version.
- **Validation:** generated mesh must have sane bounds and nonzero geometry, material and texture checks, viewer import and canonical GLB; optional FBX/OBJ/BLEND require actual compatibility tests.
- **Ops:** separate web/API from GPU inference; cost/latency/queue telemetry and automatic idle shutdown; development/staging/production isolated.

## Core data contracts

**Job:** owner_id, type, status, input ids, model version, input options, timestamps, cancellation, error reason, credit authorization, idempotency key.

**Artifact:** owner_id, project_id, source job, format/MIME, storage path, checksum, materials, mesh metrics, provenance, permission policy, generation parameters.

**Model:** id/version, source repository and commit, weights hash, dependency image, license-review reference, GPU requirements, outputs, validated status.

## Security and reliability gates

Untrusted uploads can contain executable behavior and malicious binary content. Validate types and sizes; sandbox Blender and converters; restrict networking and credentials; prevent SSRF, cross-account asset access, injection through tool-calling paths and secrets leakage. Use least-privilege IAM, HTTPS, backups and recovery tests.

## Decisions pending proof

Which baseline model is commercially cleared and actually fits available GPUs; whether to adapt or replace Open3DStudio frontend; payment provider and regional compliance; per-job target cost; exact multi-view, animation and environment pipelines.
