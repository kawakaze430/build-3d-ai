# Feature ownership and dependency map

Prepared: 17 November 2026, from the universal review starting at `56f412f`.

This map groups the existing system by vertical responsibility without moving framework entry points or duplicating business logic. The [complete feature inventory](../../AnalyseFuture/FEATURE_INVENTORY.txt) records granular status, dependencies, missing work and evidence; the [requirements matrix](FEATURE_MATRIX.md) retains product acceptance IDs. The [owner-adopted main goal](BUILD_3D_AI_PROJECT_IDEA.txt) remains product direction.

Paths below are relative to the repository root. A listed test is evidence of coverage ownership, not a claim that it validates every production property. The [current validation report](../../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt) separates executed checks from unrun operations.

## Product verticals

| Responsibility | Web ownership | API / shared logic ownership | Verification ownership | Configuration / topical documentation |
|---|---|---|---|---|
| Private login and server-side session | `apps/web/src/app/api/session/route.ts`; `lib/server-product-api.ts`; login UI in `components/studio.tsx` | `apps/api/src/build3d_api/main.py` bearer dependency; `store.py` API-key authentication; `cli.py` create/issue/revoke | API `test_product_api.py`; web `tests/e2e/studio.spec.ts` | `BUILD3D_API_URL`; [identity](../architecture/IDENTITY_AND_ACCOUNT_LIFECYCLE.md), [ADR 0001](../architecture/adr/0001-web-studio-foundation.md) |
| Optional external identity | Public browser integration is not implemented | API `trusted_identity.py`, immutable mapping in `store.py`, migrations `0002`/`0004`, operator identity CLI | API `test_trusted_identity.py`; mapping tests in `test_product_api.py` | `config/identity/providers.example.json`; `EXTERNAL_JWT_AUTH_ENABLED`; [identity](../architecture/IDENTITY_AND_ACCOUNT_LIFECYCLE.md) |
| Bounded web request ingestion | Shared `apps/web/src/lib/server/request-body.ts` used by both session and product routes | Tenant API separately enforces request/image bounds through `body_limit.py` and `images.py` | Web `lib/request-body.test.ts` (ten new cases); API image/body tests | Product BFF 12 MiB; login 8 KiB; [product contracts](../operations/PRODUCT_BACKBONE.md) |
| Tenant project ownership | `lib/api.ts` parsing and calls; `components/studio.tsx` create/select/list | API routes in `main.py`; `store.py` scoped queries/foreign keys | API `test_product_api.py`; browser project/isolation contracts | `DATABASE_URL`; [backbone](../operations/PRODUCT_BACKBONE.md) |
| Persisted job history and status | `lib/contracts.ts`, `lib/status.ts`, `lib/api.ts`, studio state | API `store.py` public-job projection, job lists and owner lookup | Web `status.test.ts`/`api.test.ts`; API persistence tests | API supports bounded pagination; UI currently requests only first 100 rows; [inventory](../../AnalyseFuture/FEATURE_INVENTORY.txt) |
| Text/image job admission | Studio forms -> allowlisted product BFF -> `lib/api.ts` | API `main.py`, `store.py`, `images.py`, `body_limit.py`; shared gateway model policy | API admission/idempotency/concurrency/upload tests in `test_product_api.py` | `MAX_ACTIVE_JOBS_PER_USER`, `API_REQUESTS_PER_MINUTE`, approval policy; [backbone](../operations/PRODUCT_BACKBONE.md) |
| Durable execution and reconciliation | Status/error guidance; no browser worker execution | API `worker.py`, fenced `store.py` claims/transitions, `cli.py` reconciliation; reused gateway `upstream.py` | API `test_durable_worker.py`; gateway contract tests | Shared DB/storage/policy; explicit spend acknowledgement; [recovery rules](../operations/PRODUCT_BACKBONE.md) |
| Model permission and lineage | Approved-model selector; honest empty state | Gateway `model_policy.py` and packaged `model-approvals.json`; API snapshots/rechecks approval | Gateway `test_gateway.py`; API policy-change tests | `MODEL_APPROVAL_FILE`; [approval gate](../operations/MODEL_APPROVAL_GATE.md), [license evidence](../research/LICENSE_MATRIX.md) |
| Private artifact delivery | Shared `artifactDownloadUrl()` in `lib/api.ts`; BFF download route | API owner lookup, storage materialization and checksum/GLB revalidation; gateway `glb_validation.py` | API `test_storage.py`/`test_product_api.py`; browser download/isolation contracts | `ARTIFACT_STORAGE_BACKEND`, private storage settings; [storage](../operations/OBJECT_STORAGE.md) |
| Filesystem / S3-compatible storage | Storage internals stay server-side | API `storage.py`; `FileSystemArtifactStorage` / `S3ArtifactStorage`; worker publication and DB completion | API `test_storage.py` uses filesystem and synthetic S3 client | Optional `build3d-api[s3]`, SDK credential chain, bucket/endpoint/prefix; [storage](../operations/OBJECT_STORAGE.md) |
| Persistent artifact-byte quotas | Studio usage meter and warnings; `getStorageUsage()` parsing | API `/v1/storage`, `store.py` completion-time enforcement and operator quota CLI; migration `0003` | API quota/concurrency tests; web parsing/browser usage contracts | `DEFAULT_STORAGE_LIMIT_BYTES` for new users; [quotas](../operations/OBJECT_STORAGE.md) |
| Read-only storage inventory / copy migration | No tenant maintenance endpoint | API `maintenance.py`, `migration.py`, `cli.py`; shared storage/validator contracts | API storage/migration fixture tests | Bounded `scan-artifacts` and dry-run/default copy command; [migration runbook](../operations/OBJECT_STORAGE.md) |
| Browser GLB inspection | `src/features/assets/components/model-viewer.tsx`; Three.js/R3F/Drei | Reuses the verified owner-scoped download; no sample asset in production UI | Browser synthetic-GLB viewer contract; TypeScript/build | `apps/web/package.json`; [web studio](../../apps/web/README.md) |

All API test paths above are beneath `apps/api/tests/`; gateway tests are beneath `apps/gateway/tests/`; web source paths are beneath `apps/web/src/` unless fully specified.

Known UI debts remain explicit: `listProjects()` and `listJobs()` use `limit=100&offset=0`, so persisted history is not fully browsable. Slow polling responses can race navigation; the current request-body and download-helper consolidation does not fix that race. These need focused behavior tests and a bounded correction rather than a claim that all history/polling is complete.

## Operator and qualification verticals

| Responsibility | Implementation owner | Verification owner | Dependencies and boundaries |
|---|---|---|---|
| Administrative model-server gateway | `apps/gateway/src/build3d_gateway/main.py`, `upstream.py` | `test_gateway.py` | Control key and private upstream token; distinct from product users; [phase-0 guide](../development/PHASE0_GATEWAY.md) |
| Bounded upstream GLB preflight | Gateway `download.py` and `glb_validation.py` | `test_glb_validation.py`, gateway invalid-download tests | Rejects invalid bounded structure/external resources before response; does not prove mesh quality |
| Explicit live smoke command | Gateway `smoke.py` | `test_gpu_smoke.py` uses synthetic HTTP/GLB fixtures | Explicit approved model/runtime and budget required; [smoke guide](../operations/GPU_SMOKE_AND_ARTIFACTS.md) |
| OBJ + PNG to self-contained GLB | Gateway `textured_glb.py`, existing GLB validator | `test_textured_glb.py` | Narrow xatlas-compatible OBJ dialect; synthetic packaging proof, not UV/artistic acceptance |
| Guarded TripoSR preparation | `services/generation/triposr_candidate/prepare_runtime.py`, manifest and local configs | `test_prepare_runtime.py` and `test_marching_cubes_contract.py` | Exact separate Git checkout, reviewed blobs/config/checkpoint requirements; no model execution during preparation |
| Resolver-metadata audit recovered from earlier branch | Same candidate directory: `audit_pip_report.py` | `test_audit_pip_report.py` (nine recovered fixture tests) | Recovered from `7129208`; validates direct pins/trusted URLs/index hashes/source-archive status, not independently downloaded artifact bytes |
| CPU package and image delivery | `apps/api/pyproject.toml`, `apps/gateway/pyproject.toml`, root `requirements.lock`, both Dockerfiles/Compose files | `scripts/packaging/check_api_wheel.py`, local image/config/startup checks where recorded | Gateway Docker context now uses root constraints rather than a second unconstrained install definition |

The guarded candidate source patch and metadata auditor are useful first-party tooling. The complete GPU candidate image, exact wheelhouse/binary notices, model loading, real inference, real S3 operation and Blender import remain unverified. Source-archive blockers must remain visible even when an inventory command itself succeeds.

## Shared development and validation ownership

- `scripts/cloud/install.sh` recreates the constrained CPU packages and web dependencies. There is no checked npm lockfile yet; exact transitive frontend reproducibility remains release debt.
- `scripts/cloud/run_web.py` runs in `apps/web` and restores files Next.js generates/rewrites. Use it as documented, preserving concurrent user changes.
- `apps/web/playwright.config.ts` is the canonical browser-contract definition. `scripts/cloud/playwright.config.cjs` is a thin managed-Chromium selector rather than a second test-server configuration.
- Root `pytest.ini` selects first-party CPU suites; explicit candidate suites add preparation/audit/marching-cubes coverage. `AnalyseFuture/` remains excluded from default discovery.
- All four root workflow definitions were inspected: Gateway CI, Product API CI, Web Studio CI and TripoSR Qualification CI. Their contents are not proof that a new hosted Actions run completed. The current run's executed local checks are listed in the validation report.

The current audit records 136 SQLite/gateway tests, 83 PostgreSQL API tests, 12 preparation/auditor tests, two marching-cubes tests, 14 web unit tests, six browser contracts, TypeScript checking and the production web build. Two CPU images were built using the managed CA trust path after an ordinary build encountered TLS trust failure. These outcomes do not validate the GPU candidate or justify disabling package/TLS verification. Consult the [validation report](../../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt) for commands, outcomes and limitations.

## Dependency flow and why paths stay coherent

```text
Studio UI
  -> typed web API helpers
  -> session/product Next.js routes
       -> shared bounded-body reader + fixed-origin product fetch
       -> tenant FastAPI API
            -> same product owner for API keys or optional trusted assertions
            -> SQLAlchemy migrations/store: projects, durable jobs, quotas
            -> private storage and shared GLB validation for downloads

Explicit bounded worker
  -> same database and policy
  -> reused gateway upstream client
  -> separately approved private inference runtime
  -> verified storage publication + fenced artifact completion
```

Next.js requires filesystem routes, and Python packaging/migrations rely on stable module ownership. These boundaries separate browser sessions, tenant authorization, operator credentials and GPU environments. A feature can span them without belonging in one physical folder. Moving everything into a generic `features/` directory would break useful conventions while adding no shared behavior.

Consolidation therefore joins compatible responsibilities: one streamed-body reader, one download-URL helper, one canonical browser-test configuration, reused gateway policy/client/GLB verification, one CPU constraint source, and one candidate dependency-report auditor. It does not combine incompatible model environments or promote raw upstream source into the product process. Larger `store.py`/studio components may be split when a specific change justifies it, while retaining ownership, admission and fencing invariants.

## History and future work

The [consolidation report](../../AnalyseFuture/CONSOLIDATION_REPORT.txt), [path mapping](../../AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt), [archived manifest](../../AnalyseFuture/ARCHIVED_FILES_MANIFEST.txt) and [technical debt](../../AnalyseFuture/TECHNICAL_DEBT.txt) record recovered work and retained alternatives. Exact pre-review live-document bytes remain in [documentation-before-universal](../../AnalyseFuture/historical-implementations/documentation-before-universal); historical upstream snapshots remain under `AnalyseFuture/third_party/` with their license and provenance boundaries.

Public accounts, payments/credit ledger, retention/deletion, GPU scheduling, actual generation quality, professional mesh/material editing, rigs, facial performance, scenes and training require separate implementation and acceptance. Use the [derived future roadmap](../../AnalyseFuture/PROJECT_VISION_AND_FUTURE_ROADMAP.txt) to investigate them without treating research dates or adopted ambition as shipping/spending authorization.
