# Persistent projects and generation jobs

Current implementation reconciliation: 17 November 2026. The [pre-review version](../AnalyseFuture/historical-implementations/documentation-before-universal/docs/PRODUCT_BACKBONE.md) preserves the exact document from baseline `56f412f`; historical results remain scoped to their recorded runs.

Initial backend implementation dated **14 November 2026**; consolidated and extended on `main` through PR #16 on **15 November 2026**. This is a real private product backend, with database-backed accounts, projects and jobs. Tests use real database transactions and **synthetic HTTP/model fixtures**; they do not prove AI inference, quality, GPU cost, commercial clearance, or production deployment.

## Scope and acceptance criteria

| Capability | Implemented behavior | Verification |
|---|---|---|
| Database | Frozen Alembic migration for users, API keys, projects, jobs and artifacts; SQLite for local development, PostgreSQL target | Migration upgrade/downgrade/re-upgrade and metadata agreement |
| Authentication | Operator issues high-entropy API keys; only SHA-256 digests persist; revocation and additional keys | Anonymous, wrong-key, revoked-key and disabled-user tests |
| Ownership | Every project/job/artifact read, submit, cancel and download is owner-scoped; composite database foreign keys | Two-user HTTP and database tests |
| Persistence | Projects and job history survive application/connection-pool replacement | Restart test with a new engine and app |
| Job admission | Required per-owner idempotency key; changed payload conflicts; atomic active-job quota | Concurrent same-key and different-key tests |
| Uploads | 10 MiB encoded limit, 16 million pixels, actual PNG/JPEG/WEBP decode, orientation normalization, metadata removal | Truncated/signature-only images, malformed EXIF, pixel and request-size tests |
| Worker | Persistent claims and fencing tokens; safe polling retries; uncertain POSTs require reconciliation | Two-worker, crash, expired-lease, timeout and transport-failure tests |
| Model lineage | Snapshot full approval entry at queue time and compare again before submission | Changed/revoked approval cannot reach the upstream |
| Artifacts | Bounded GLB verification, checksum, atomic DB completion, owner-only download through a storage abstraction; filesystem default + optional S3-compatible backend | Invalid output, disk/object failure, missing/corrupted files, synthetic S3 round trip and cross-owner tests |

The phase-0 operator gateway remains a separate application on port 8080. The product API is on port 8081 and does **not** mount those operator routes. A customer API key cannot query arbitrary upstream jobs, select unauthorized checkpoints, or provision users. The GPU server is reachable only by the worker, using a server-side token.

## Local setup without a GPU

From the repository root, on Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e "./apps/gateway[test]" -e "./apps/api[test]"
build3d-admin migrate
build3d-admin create-user --name "Owner"
uvicorn build3d_api.main:create_app --factory --host 127.0.0.1 --port 8081
```

On Windows use `.venv\Scripts\Activate.ps1` and PowerShell environment variables. The lockfile is tested on Linux; Windows-specific dependency resolution is not verified.

`create-user` returns `user_id`, `key_id` and `api_key` **once**. Store the token privately. Do not commit it, share command output, put it in URLs, or send the operator/upstream token to browsers. No default user or password exists. Issue replacement keys with `build3d-admin issue-key --user-id USER_ID`; revoke an old key with `build3d-admin revoke-key --key-id KEY_ID`.

Open `http://127.0.0.1:8081/docs` for the interactive API. Enter the user API key in **Authorize**, create a project, and use the returned project ID. `/health` verifies process/database availability; `gpu_verified: false` is intentional. No inference is run at startup or during project creation.

Configuration is read from the process environment; the Python commands do not automatically load `.env`. Compose reads `.env`. Defaults use `./data/build3d.db`, filesystem artifact storage and `./data/artifacts`; these local data paths are excluded from Git. An optional S3-compatible artifact backend is available behind `ARTIFACT_STORAGE_BACKEND=s3`; no bucket is created automatically. See [OBJECT_STORAGE.md](OBJECT_STORAGE.md). SQLite is a local development option; use PostgreSQL for concurrent private staging.

## HTTP contract

Every `/v1` route requires a bearer credential. Operator-provisioned `USER_API_KEY` values are the default. A reviewed provider configuration plus `EXTERNAL_JWT_AUTH_ENABLED=true` enables the implemented asymmetric JWT/JWKS path; immutable issuer/subject mapping resolves the same product owner. This does not enable public browser accounts. API-key requests are rate limited per key in the database (120/minute by default, shared across API processes); external credentials use their own durable rate window. See [identity details](IDENTITY_AND_ACCOUNT_LIFECYCLE.md). Responses have `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. Limits return HTTP 429; missing/inaccessible objects return HTTP 404 without exposing another user's resources. Timestamps are UTC Unix seconds.

| Method and path | Input / outcome |
|---|---|
| `GET /v1/me` | Current user ID |
| `GET /v1/models` | Only approved model IDs; empty by default |
| `GET /v1/storage` | Owner-scoped persistent artifact usage, limit and remaining bytes |
| `POST /v1/projects` | JSON `{"name":"Film assets"}` → 201 with project ID |
| `GET /v1/projects` | Paginated projects, `limit` 1–100 and bounded `offset` |
| `GET /v1/projects/{id}` | Owned project |
| `POST /v1/projects/{id}/jobs/text` | JSON `{"prompt":"A wooden chair","model_id":"APPROVED_ID"}` plus `Idempotency-Key` |
| `POST /v1/projects/{id}/jobs/image` | Multipart `file`, `model_id`, plus `Idempotency-Key`; no file URL inputs |
| `GET /v1/projects/{id}/jobs` | Paginated job history |
| `GET /v1/jobs/{id}` | Persistent status, error code, prompt/input hash, model approval provenance |
| `POST /v1/jobs/{id}/cancel` | Only queued jobs; repeat cancellation is safe |
| `GET /v1/jobs/{id}/artifact` | Verified artifact metadata; 409 until available |
| `GET /v1/jobs/{id}/download` | Revalidated private GLB with `X-Artifact-SHA256` |

New job submission returns **202 queued** and a `Location` header. Repeating the same key and input returns **200 with the same job ID**; changing project/type/prompt/model/original image bytes under that key returns **409**. Keys are scoped to an owner, retained with history, and not automatically expired. Admission still requires a currently approved model even for replays. Each owner has three active jobs by default; this is a concurrency guard, **not a dollar spend limit**. Artifact completion is separately constrained by the persistent per-user byte quota from migration `0003`; quota rejection becomes a known failed job and creates no artifact row. There is no automatic regeneration or retry endpoint.

Image bytes are decoded and normalized to PNG before persistence. `input_sha256` identifies the original upload, and the normalized input is stored transactionally in the database until completion/failure/cancellation. Thus queued input survives restart without relying on a temporary upload URL. Image inputs still live transactionally in the database in this slice; the S3-compatible backend currently stores generated GLB artifacts only. Persistent artifact quotas, read-only orphan/missing scanning and verified copy-only filesystem-to-S3 migration are implemented. Retention, customer/operator deletion, real remote-storage qualification and audited destructive cleanup remain open.

## Worker and GPU requirements

Before running a worker against a real backend, resolve the existing model/license and GPU budget gates. Set `MODEL_APPROVAL_FILE`, `UPSTREAM_BASE_URL`, `UPSTREAM_BEARER_TOKEN`, `DATABASE_URL` and the same artifact-storage configuration for API/worker. Filesystem deployments use `ARTIFACT_DIR`; S3-compatible deployments additionally require `S3_ARTIFACT_BUCKET` and optional endpoint/region settings. The worker and API must share the same database, artifact storage and policy. Inside containers, `localhost` refers to the container; set a private reachable backend hostname explicitly.

The worker reuses the real `UpstreamGateway` text/image APIs and GLB verifier. It stores exact model approval metadata but cannot attest that the remote server actually loaded those checkpoint bytes. Runtime attestation is still required before production.

Only after the owner has approved the actual model, backend and bounded GPU budget:

```bash
build3d-worker --confirm-gpu-spend --max-steps 240 --interval-seconds 5
```

This runs at most 240 work cycles, defaulting to one cycle when `--max-steps` is omitted. One cycle claims one queued/running job. The worker does not create infrastructure. Starting a cycle can submit real billable work to an existing server; the flag acknowledges this but cannot cap cloud charges or stop remote computation. No worker is run during installation, migration, API startup, or tests.

## Recovery rules

| State | Meaning | Automatic action / operator action |
|---|---|---|
| `queued` | Durable input accepted, no upstream request yet | Worker may claim; owner can cancel |
| `dispatching` | Claim committed before non-idempotent upstream POST | Never submit again after a crash; lease expiry moves to `submission_unknown` |
| `running` | Upstream job ID is persisted | GET polling resumes after restart/lease expiry |
| `completed` | GLB verified and private artifact record committed | Download available |
| `failed` | Known upstream failure, policy change, invalid size, or operator resolution | Slot released; no automatic regeneration |
| `canceled` | Canceled while still queued | Slot released; no upstream cancel claim |
| `submission_unknown` | Submission response was lost/invalid or worker crashed | Quota slot retained; investigate backend |
| `polling_paused` | Bounded reads/downloads failed repeatedly | Quota slot retained; repair access/storage/output and reconcile |
| `timed_out` | Upstream completion was not observed within one hour | Quota slot retained; remote compute may still be running |

The upstream contract does not offer proven idempotent POSTs or cancellation. Accordingly, the worker does **not** promise exactly-once remote execution and never automatically repeats generation POSTs. Even an explicit upstream HTTP error during submission is conservatively treated as uncertain. GET failures back off exponentially (up to 300 seconds), then pause after five failures. A ten-minute lease fences stale workers; machines must keep synchronized clocks.

After inspecting backend logs, attach the **existing** upstream job to a local uncertain/paused/timed-out record:

```bash
build3d-admin reconcile-job --job-id LOCAL_ID --upstream-id EXISTING_UPSTREAM_ID
```

This resumes polling only. It does not regenerate. If investigation proves that upstream work is absent or stopped, explicitly release the slot:

```bash
build3d-admin reconcile-job --job-id LOCAL_ID --confirm-upstream-stopped
```

Do not run that command merely to bypass a full queue. It records a local failure and cannot stop the remote job. Running jobs cannot be canceled through this API. Additional leases, stale-worker fencing and atomic transitions prevent duplicate local completion/quota release.

## Storage, backups and rollback

Generated artifact ownership, checksum and size live in the database. The bytes are stored behind the `ArtifactStorage` interface.

The default filesystem backend publishes to deterministic owner-scoped paths beneath `ARTIFACT_DIR` using same-filesystem staging, fsync and atomic replace; it retains read compatibility with the earlier flat artifact layout. The optional S3-compatible backend writes a private deterministic key plus checksum/owner/job metadata, performs a HEAD size/SHA check before the job is committed completed, and never creates a bucket at startup.

Downloads do not trust storage metadata alone. The API materializes the owned object, runs the structural GLB verifier again, recomputes checksum/size against the database row, then serves it. S3-compatible materializations use bounded local temporary files that are removed after the response. Direct public/presigned object downloads are deliberately not exposed yet because they would bypass this revalidation boundary.

A process/network failure around publication can still leave a private orphan. A dropped database COMMIT acknowledgement intentionally retains the published bytes because the database may have committed the reference. Use `build3d-admin scan-artifacts --max-objects 10000` for a bounded read-only comparison of storage objects against artifact rows; the command never deletes.

Back up database and artifact bytes as one logical dataset and verify restore checksums. Filesystem deployments must back up the artifact directory; S3-compatible deployments need provider-side backup/versioning policy. Persistent per-user byte quotas are enforced at DB artifact completion. Automated retention and destructive orphan cleanup remain open. A copy-only filesystem→S3 migration command is available for a stopped deployment; it never deletes source data or switches configuration automatically. See [OBJECT_STORAGE.md](OBJECT_STORAGE.md).

## Docker / PostgreSQL packaging

`compose.product.yml` adds PostgreSQL, a loopback-bound API, and a separately selected worker profile. Set a strong URL-safe `POSTGRES_PASSWORD` in `.env`. The database has no host port. The API/worker run as a non-root account with read-only root filesystems; only the private artifact volume and temporary directory are writable. Model approval files must be explicitly mounted read-only at the configured path using an operator-owned Compose override.

```bash
docker compose -f compose.product.yml build
docker compose -f compose.product.yml run --rm api build3d-admin migrate
docker compose -f compose.product.yml run --rm api build3d-admin create-user --name "Owner"
docker compose -f compose.product.yml up -d api
```

After the separate GPU gates are satisfied, an explicit one-off worker command can use the same volume/database:

```bash
docker compose -f compose.product.yml run --rm worker build3d-worker --confirm-gpu-spend --max-steps 240
```

The original backend milestone supplied Docker packaging but did not run it on that development machine. Current image-build, PostgreSQL and startup outcomes belong in the [universal validation report](../AnalyseFuture/TEST_AND_VALIDATION_REPORT.txt); older CI results do not establish those current outcomes. CI runs PostgreSQL directly as a service. Local container validation is not an AWS deployment. Do not expose the API publicly before adding TLS, perimeter request limits, full identity/account lifecycle, security review, backups, metrics, retention and cost metering.

## Reproducible checks

```bash
python -m pytest -q apps/api/tests apps/gateway/tests
python -m compileall -q apps/api/src apps/gateway/src
build3d-admin --help
build3d-worker --help
python -m pip wheel --no-deps ./apps/gateway ./apps/api -w dist
python scripts/check_api_wheel.py
```

For an isolated PostgreSQL test instance, set `TEST_DATABASE_URL` to its `postgresql+psycopg://...` URL, then run `python -m pytest -q apps/api/tests`. Every test uses a fresh random schema; no existing application tables are dropped. The test user needs schema creation permissions. CI targets Python 3.11 and 3.12, SQLite and PostgreSQL 16. See the PR's actual Actions results before relying on a platform-specific claim.

Still open: self-service signup/login/reset/deletion and trusted browser-session→API assertion issuance, real S3/backup qualification, retention/deletion policy, global GPU scheduling, billing/credits, hosted deployment, actual inference, real generated-GLB browser+Blender proof, multi-view/mesh/rigging/facial/scene tools, training, full license clearance and real quality/cost benchmarks. Immutable identity mapping, optional API assertion validation, persistent byte quotas and copy-only migration already exist and should be reused. The broad Phase 1 checklist items stay open where their acceptance includes those features. The web studio exposes only the first 100 projects/jobs today; complete pagination and the known slow-polling navigation race remain UI debt, rather than missing database persistence.
