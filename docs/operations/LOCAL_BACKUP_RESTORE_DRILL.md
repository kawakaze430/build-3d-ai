# Local PostgreSQL and artifact restore drill

This procedure exercises a private deployment that uses PostgreSQL and
filesystem artifact storage. The database contains tenant ownership, job state,
quota and expected artifact checksums. The artifact directory contains the GLB
bytes. Treat the database dump and artifact archive as one recovery set.

## Capture a recovery set

Use a private scratch directory outside the checkout. Stop all source API,
worker and maintenance writers, including any reconciliation or migration
commands. Keep PostgreSQL available for the dump. Record the source application
revision, schema revision, PostgreSQL version, and time after writing has
stopped. For a local exercise, seed two disposable owners, a completed job with
a synthetic GLB, custom quota limits, one leased running job and one
interrupted dispatch. The real-API browser test fixture under
`apps/web/tests/real-api/run.py` provides the two-owner and completed-job setup.
Seed the lease states through the store in the disposable database.

The commands below use private libpq service definitions for the source and a
fresh isolated target. Keep database credentials in private connection
configuration. Set `SOURCE_ARTIFACTS` to the source directory and
`RESTORED_ARTIFACTS` to a separate new target directory. Run the commands in a
Bash shell from the scratch location and keep its permissions private.

```bash
set -euo pipefail
umask 077
backup_dir="$(mktemp -d)"
pg_dump --dbname=service=build3d_source --format=custom --no-owner \
  --no-privileges --file="$backup_dir/metadata.dump"
tar --create --file="$backup_dir/artifacts.tar" --directory="$SOURCE_ARTIFACTS" .
(cd "$backup_dir" && sha256sum metadata.dump artifacts.tar >SHA256SUMS)
```

Restore only from a recovery set obtained through a trusted private channel.
The checksum manifest detects changes to the pair. Keep the manifest with
the trusted backup metadata and protect the database and artifacts from
unauthorized access.

## Restore and validate

Provision a fresh target database and verify the service names and artifact
paths before restoring. Leave the target API and workers stopped during the
restore. Use a compatible PostgreSQL server and client and start with the
application revision that wrote the backup.

```bash
(cd "$backup_dir" && sha256sum --check SHA256SUMS)
pg_restore --dbname=service=build3d_restore --exit-on-error --single-transaction \
  --no-owner --no-privileges "$backup_dir/metadata.dump"
mkdir -m 700 "$RESTORED_ARTIFACTS"
tar --extract --file="$backup_dir/artifacts.tar" --directory="$RESTORED_ARTIFACTS" \
  --no-same-owner --no-same-permissions
```

Point the target at the restored database and new artifact directory.
Run `build3d-admin scan-artifacts` with a bound that fits the expected fixture
count. Require a complete scan and matching database/object counts with empty
missing, orphan, duplicate, mismatch and unrecognized lists. Independently
verify all artifacts in the small fixture through the authenticated download
route. Compare the returned bytes, size and SHA-256 to the source and require
a 404 from the other owner. Verify project/job history, both tenant
identities, and the restored per-owner used, limit and remaining byte totals.

Exercise the database-only and same-size corruption cases on isolated target
paths. A database-only restore can return 200 for health while inventory
reports a missing object and the authorized download returns 503. An
inventory scan can still match a same-size corrupt object. Require the
download's structure and checksum validation to reject it before treating a
recovery set as good.

Keep the worker off during initial validation. For a disposable job-recovery
check, advance past the saved lease expiry and confirm that a running job
retains its upstream ID and gets a new lease. Verify the old lease cannot
change it. A dispatch that died before storing an upstream ID must move to
`submission_unknown`. Reconciliation needs an independently verified existing
upstream ID or confirmation that the original job stopped. The drill uses
synthetic IDs and tests the state transitions with no upstream request.

If quality checks fail, leave the target isolated, retain source and backup
state, and repeat from a complete matched recovery set in a new target. Do not
resume workers or change the active service endpoint until validation succeeds.

## Recorded local result

On 18 November 2026, a local drill used separate disposable source and restore
containers, PostgreSQL 16.16, rootless Docker, and the CPU development runtime.
The official PostgreSQL image was already cached at
`postgres@sha256:dd2bf3ce2dc83a81674cf7f217fcfd8a5009a4b325dda5b843bfee82a06cff6f`.

The quiesced recovery point was `2026-11-17T22:23:43Z`. The archive pair
contained 16,757 bytes of PostgreSQL custom-format data and a 10,240-byte tar.
Both archive checksums matched before and after restore. Starting a fresh
PostgreSQL container, restoring the pair, and running the fault and recovery
checks took 10 seconds for this fixture.

| Check | Observed result |
| --- | --- |
| Application state | Two tenants, three jobs and one restored artifact. Custom quota usage and limits matched. |
| Artifact integrity | Source and restored bytes were identical. The authenticated download returned 1,384 bytes with SHA-256 `47642ed12f40ea347eee5af898e0b8e72c292e6350c1d78dbc494b67797d9a92`. |
| Tenant boundary | Both private keys retained their original identity. Cross-owner project and artifact reads returned 404. |
| Database-only recovery | Health returned 200. Inventory found one missing artifact and the owner's download returned 503. |
| Same-size corruption | Inventory matched the object by size. The owner's download returned 503. |
| Job recovery | Reclaimed a running lease under a new token, rejected both stale tokens, and reconciled the interrupted dispatch to a known synthetic upstream ID. |

Both containers, temporary credentials and the private recovery files were
removed after validation.

Real provider backup/versioning, access-denial and timeout behavior, production
recovery objectives, staged cutover and alerting remain open.
