# Private artifact storage design

Status: **filesystem and S3-compatible runtime implemented/tested; persistent per-user byte quotas and bounded dry-run inventory scanning added; no remote bucket provisioned**

## Goals

Generated GLBs stay private, owner-scoped and immutable from the product's point of view. The database remains the source of truth for ownership, checksum, byte size and mesh count. Storage backends are not trusted to prove GLB integrity.

The logical object key is deterministic and server-generated:

```text
build3d/v1/artifacts/<owner-id>/<artifact-id>.glb
```

User input is never interpolated into object keys.

## Backends

### Filesystem (default)

`ARTIFACT_STORAGE_BACKEND=filesystem`

New files are published under `ARTIFACT_DIR/build3d/v1/artifacts/<owner>/<artifact>.glb` using a same-filesystem temporary file, fsync, atomic replace and directory fsync. A read-only fallback supports the legacy `ARTIFACT_DIR/<artifact>.glb` layout so existing verified artifacts are not broken by this change.

### S3-compatible

`ARTIFACT_STORAGE_BACKEND=s3`

Requires the optional `build3d-api[s3]` dependency and `S3_ARTIFACT_BUCKET`. `S3_ENDPOINT_URL` may point to a compatible private service such as MinIO; omit it for AWS S3. The implementation uses boto3's standard credential chain. Access keys are never accepted by browser APIs and must not be committed.

Publication writes:
- private object key;
- `model/gltf-binary` content type;
- SHA-256, owner, job and artifact IDs as object metadata;
- exact content length.

After PUT, the worker performs a HEAD check for size and SHA metadata before committing the database job as completed.

## Verified downloads

The product API does **not** redirect users to a raw object URL yet. For S3-compatible storage it downloads the private object to a bounded local temporary file, validates stored size/metadata, runs the existing GLB structural validator again, recomputes SHA-256 and compares it with the database row, then serves the file. The temporary copy is removed after the response.

This keeps the existing security property that a storage compromise/tamper does not automatically become a trusted 3D download.

Short-lived presigned downloads remain a possible optimization, but should only be enabled after there is a design that preserves checksum/integrity guarantees and revocation semantics. Boto3 supports expiring presigned URLs; this implementation deliberately does not expose them yet.

## Configuration

```bash
ARTIFACT_STORAGE_BACKEND=filesystem
ARTIFACT_DIR=./data/artifacts
ARTIFACT_STORAGE_PREFIX=build3d/v1/artifacts
DEFAULT_STORAGE_LIMIT_BYTES=5368709120

# only when ARTIFACT_STORAGE_BACKEND=s3
S3_ARTIFACT_BUCKET=
S3_ENDPOINT_URL=
S3_REGION=
# Credentials come from the standard AWS SDK chain, for example workload/IAM
# identity or process environment. Never expose them to apps/web.
```

No code in this milestone creates a bucket or starts a paid cloud service.

## Migration

Do not flip a running deployment from filesystem to S3 until existing objects have been copied and verified. The logical key format is deterministic, but legacy flat filesystem objects need to be migrated into the owner-scoped S3 key. A migration tool should:

1. enumerate artifact rows from the database;
2. read and revalidate each legacy/current file;
3. upload it to the deterministic owner-scoped key;
4. HEAD-verify byte size and SHA metadata;
5. re-download a sample (or all objects for the first migration) and compare SHA;
6. record an operator audit log;
7. switch configuration only after every live artifact is present.

This milestone provides the runtime abstraction, not the destructive migration command.

## Retention, cleanup and orphan handling

A failed/stale worker transition attempts to delete the just-published object. An uncertain database commit intentionally retains the object because the database may already reference it. A network failure during object publication can still leave a private orphan.

The operator now has a **read-only bounded scanner**:

```bash
build3d-admin scan-artifacts --max-objects 10000
```

It compares the complete bounded database artifact set with the configured storage backend and reports missing DB-referenced objects, storage orphans, duplicate current/legacy filesystem copies, owner/size mismatches, malformed keys and byte totals. If either side exceeds `--max-objects`, the command refuses to classify a partial scan and asks the operator to rerun with a higher bound.

The scanner **never deletes anything**. It also does not download every object to recompute SHA-256; normal artifact downloads keep the stronger GLB/checksum revalidation boundary. For S3-compatible storage, this operator-only command needs list permission on the configured private prefix. The normal tenant API/worker does not require bucket-list permission.

No automatic retention/lifecycle deletion is enabled yet because product retention policy and billing are not decided. A future destructive cleanup workflow must consume a fresh complete scan, require explicit operator acknowledgement, preserve an audit record and never delete an object while its artifact row is live.

## Backup/restore

- PostgreSQL backup protects ownership/checksum metadata, not the GLB bytes.
- Object storage requires independent versioning/backup policy appropriate to the provider.
- Restore is successful only when database rows and exact object checksums agree.
- Filesystem deployments require the artifact directory in backups.

## Quotas

Migration `0003` adds persistent `users.storage_limit_bytes`. Existing users receive a 5 GiB migration default; newly created users receive `DEFAULT_STORAGE_LIMIT_BYTES` (5 GiB unless explicitly configured).

The artifact table remains the durable byte ledger. At artifact completion the store serializes completion for that owner, sums committed artifact bytes and accepts the new artifact only when it fits the persisted limit. This prevents concurrent workers from independently passing the same stale quota check.

A quota failure records the job as `failed` with `artifact_storage_quota_exceeded`, releases the active-job slot, creates no artifact row and tells the worker not to retain the already-private object. An uncertain database acknowledgement still favors preservation; any resulting private orphan is surfaced by the scanner above.

Operator controls:

```bash
build3d-admin storage-usage --user-id USER_ID
build3d-admin set-storage-quota --user-id USER_ID --bytes 10737418240
```

Reducing a quota below current usage never deletes existing artifacts; it only blocks future artifact completion until usage is reduced through a separately audited workflow. The owner-scoped tenant endpoint `GET /v1/storage` reports used, limit and remaining bytes.

Project-specific quotas, billing-tier policy, retention deletion and customer-initiated artifact deletion remain open.

## Deployment controls

For a real S3 deployment require:
- private bucket / public access blocked;
- encryption at rest according to provider policy;
- TLS for remote endpoints;
- least-privilege service identity limited to the artifact prefix;
- no bucket-list/public-write permissions unless an operational tool explicitly needs them;
- endpoint/network restrictions where supported.

These are engineering controls, not a claim that any particular cloud configuration has been deployed or audited.
