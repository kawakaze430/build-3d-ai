"""Operator commands. Never expose these over the tenant HTTP API."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from .config import Settings
from .db import check_schema, create_database, migrate
from .maintenance import scan_artifact_storage
from .migration import ArtifactMigrationError, migrate_filesystem_to_s3
from .storage import (
    ArtifactStorageError,
    FileSystemArtifactStorage,
    S3ArtifactStorage,
    create_artifact_storage,
)
from .store import Store, StoreError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate", help="Apply versioned database migrations")
    create = commands.add_parser("create-user", help="Print a new API key ONCE; store it privately")
    create.add_argument("--name", required=True)
    key = commands.add_parser("issue-key", help="Issue another key for an existing user")
    key.add_argument("--user-id", required=True)
    revoke = commands.add_parser("revoke-key")
    revoke.add_argument("--key-id", required=True)
    quota = commands.add_parser(
        "set-storage-quota",
        help="Set one user's persistent artifact-byte quota; existing artifacts are never deleted",
    )
    quota.add_argument("--user-id", required=True)
    quota.add_argument("--bytes", required=True, type=int, dest="limit_bytes")
    usage = commands.add_parser("storage-usage", help="Report persistent artifact bytes for one user")
    usage.add_argument("--user-id", required=True)
    scan = commands.add_parser(
        "scan-artifacts",
        help="Dry-run database/storage consistency scan; never deletes objects",
    )
    scan.add_argument("--max-objects", type=int, default=10000)
    migrate_artifacts = commands.add_parser(
        "migrate-filesystem-to-s3",
        help="Dry-run/copy DB-referenced filesystem artifacts to configured S3; never deletes source",
    )
    migrate_artifacts.add_argument("--source-dir", type=Path, required=True)
    migrate_artifacts.add_argument("--max-objects", type=int, default=10000)
    migrate_artifacts.add_argument(
        "--execute-copy",
        action="store_true",
        help="Actually PUT missing verified artifacts. Omit for read-only planning.",
    )
    link_identity = commands.add_parser(
        "link-identity",
        help="Operator-only: link one immutable external issuer/subject to a product user",
    )
    link_identity.add_argument("--user-id", required=True)
    link_identity.add_argument("--issuer", required=True)
    link_identity.add_argument("--subject", required=True)
    unlink_identity = commands.add_parser(
        "unlink-identity",
        help="Operator-only: remove an external identity link",
    )
    unlink_identity.add_argument("--issuer", required=True)
    unlink_identity.add_argument("--subject", required=True)
    list_identities = commands.add_parser(
        "list-identities",
        help="List external identity links for one product user",
    )
    list_identities.add_argument("--user-id", required=True)
    reconcile = commands.add_parser("reconcile-job", help="Resolve an uncertain job without resubmitting inference")
    reconcile.add_argument("--job-id", required=True)
    outcome = reconcile.add_mutually_exclusive_group(required=True)
    outcome.add_argument("--upstream-id")
    outcome.add_argument("--confirm-upstream-stopped", action="store_true")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    engine = create_database(settings.database_url)
    store = Store(engine, settings)
    try:
        if args.command == "migrate":
            migrate(engine)
            result = {"schema": "0004"}
        else:
            check_schema(engine)
            if args.command == "create-user":
                result = store.create_user(args.name)
            elif args.command == "issue-key":
                result = store.issue_key(args.user_id)
            elif args.command == "revoke-key":
                store.revoke_key(args.key_id)
                result = {"revoked": True}
            elif args.command == "set-storage-quota":
                result = store.set_storage_quota(args.user_id, args.limit_bytes)
            elif args.command == "storage-usage":
                result = store.storage_usage(args.user_id)
            elif args.command == "scan-artifacts":
                storage = create_artifact_storage(settings)
                storage.prepare()
                result = scan_artifact_storage(store, storage, max_objects=args.max_objects)
            elif args.command == "migrate-filesystem-to-s3":
                if settings.artifact_storage_backend != "s3":
                    raise RuntimeError(
                        "migrate-filesystem-to-s3 requires ARTIFACT_STORAGE_BACKEND=s3"
                    )
                target = create_artifact_storage(settings)
                if not isinstance(target, S3ArtifactStorage):
                    raise RuntimeError("Configured migration target is not S3-compatible storage")
                target.prepare()
                source = FileSystemArtifactStorage(
                    args.source_dir,
                    prefix=settings.artifact_storage_prefix,
                )
                result = migrate_filesystem_to_s3(
                    store,
                    source,
                    target,
                    max_objects=args.max_objects,
                    execute_copy=args.execute_copy,
                )
            elif args.command == "link-identity":
                result = store.link_external_identity(args.user_id, args.issuer, args.subject)
            elif args.command == "unlink-identity":
                store.unlink_external_identity(args.issuer, args.subject)
                result = {"unlinked": True}
            elif args.command == "list-identities":
                result = {"items": store.list_external_identities(args.user_id)}
            else:
                store.reconcile(args.job_id, args.upstream_id, confirm_stopped=args.confirm_upstream_stopped)
                result = {"reconciled": True}
        print(json.dumps(result))
        return 0
    except StoreError as exc:
        print(exc.detail, file=sys.stderr)
        return 1
    except (
        SQLAlchemyError,
        RuntimeError,
        ArtifactStorageError,
        ArtifactMigrationError,
        ValueError,
    ):
        print("Database operation failed; check configuration and migrations.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
