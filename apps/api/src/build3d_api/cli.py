"""Operator commands. Never expose these over the tenant HTTP API."""
from __future__ import annotations

import argparse
import json
import sys

from sqlalchemy.exc import SQLAlchemyError

from .config import Settings
from .db import check_schema, create_database, migrate
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
            result = {"schema": "0001"}
        else:
            check_schema(engine)
            if args.command == "create-user":
                result = store.create_user(args.name)
            elif args.command == "issue-key":
                result = store.issue_key(args.user_id)
            elif args.command == "revoke-key":
                store.revoke_key(args.key_id)
                result = {"revoked": True}
            else:
                store.reconcile(args.job_id, args.upstream_id, confirm_stopped=args.confirm_upstream_stopped)
                result = {"reconciled": True}
        print(json.dumps(result))
        return 0
    except StoreError as exc:
        print(exc.detail, file=sys.stderr)
        return 1
    except (SQLAlchemyError, RuntimeError):
        print("Database operation failed; check configuration and migrations.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
