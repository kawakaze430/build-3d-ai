# Developer handoff — 14 November 2026

## Branch stack and current implementation

Review/merge the existing stack in order: **PR #1 → PR #11 → PR #12 → PR #13**. The newest branch is `implementation/durable-project-jobs`, based on PR #12 at `9759200b1ab9f769eadd54105579b26ed364d58a`. Retarget each dependent PR to `main` once its parent has landed; resolve against current main and rerun checks before merging. Do not merge the entire stack blindly.

- `apps/gateway`: private operator gateway, real 3DAIGC-API client, model approvals, bounded GLB validation and explicit-spend GPU smoke CLI.
- `apps/api`: separate private user-key API, projects, persistent text/image jobs, database-backed rate/admission limits, request idempotency, approval lineage and owned downloads.
- `build3d-worker`: fenced database claims, non-replayed generation submissions, restartable polling, private artifact storage and operator reconciliation.
- `build3d-admin`: migrations, user/key provisioning, revocation, reconciliation. No public admin endpoints.
- `requirements.lock`, CPU dependency/license inventory, Docker packaging, Python 3.11/3.12 and SQLite/PostgreSQL CI definitions.

Run instructions and exact limitations: [PRODUCT_BACKBONE.md](PRODUCT_BACKBONE.md). Canonical task statuses: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md). Broad items remain open when only a subpart is implemented.

## What was verified in the implementation workspace

The 95-test combined Python 3.12 SQLite/gateway suite passed. It exercises real database migrations/transactions/restarts, two-user isolation, simultaneous duplicate submissions, quotas, worker recovery, uncertain requests/commits, upload decoding and synthetic GLB downloads. CLI help, source compilation, distributable-wheel migration inclusion and a real Uvicorn process with authenticated project HTTP requests were also checked. Consult [PR #13](https://github.com/kawakaze430/build-3d-ai/pull/13) for final Python 3.11/3.12 and PostgreSQL Actions results.

**No AI generation, model load, GPU launch, cloud deployment or paid inference was performed.** HTTP and GLB fixtures are synthetic. Docker is unavailable on the implementation machine, so Compose packaging was not runtime-tested there. No claim of competitor-level output quality is supported yet.

## Next concrete development tasks

1. Review the stack and current CI. Pay special attention to approval policy handling, object ownership, upload limits, database concurrency, lease expiry, artifact integrity and uncertain-job quota retention.
2. Complete issue #2's exact code/weight/dataset/transitive-license audit. The current inventory is partial; keep unapproved models disabled. Review bundled CPU binary dependencies before commercial distribution too.
3. Prepare one specific private GPU deployment with exact model/runtime revision, checkpoint hash, provider region, quota, hourly price, total spend cap and shutdown plan. Get the missing budget/access before starting paid resources.
4. With approved resources, run one real image → textured mesh → verified GLB. Record hardware, VRAM, timing, all costs, backend logs and Blender/viewer import proof. Use the genuine [GPU smoke guide](GPU_SMOKE_AND_ARTIFACTS.md); never use a fixture as evidence.
5. While GPU access is pending, complete the pinned Open3DStudio build/maintenance audit and select the browser UI foundation. Integrate the tenant API with a real Three.js viewport only after reviewing the relevant dependencies. Add real browser and GLB import tests.
6. Add a maintained identity provider or thoroughly tested account lifecycle: signup/login, recovery, deletion, session security and user administration. Operator-issued API keys alone are not public customer onboarding.
7. Introduce private object storage, signed URLs, retention/cleanup, disk/storage quotas, backup-and-restore tests and metrics. Preserve all ownership checks. Current image inputs live in the database and output files require shared private disk.
8. Add global worker/GPU concurrency, provider budget enforcement and runtime model attestation. Do not replace uncertain-submission quarantine with blind POST retries; the upstream lacks a proven idempotency contract. SQS does not solve that automatically.
9. Proceed to billing, mesh tools, rigging, facial animation, scenes and training only with their independent acceptance tests and cleared dependencies. Do not label the full product complete until its release gates pass.

## Reproduce the CPU checks

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e "./apps/gateway[test]" -e "./apps/api[test]"
python -m pytest -q apps/api/tests apps/gateway/tests
python -m compileall -q apps/api/src apps/gateway/src
python -m pip wheel --no-deps ./apps/gateway ./apps/api -w dist
python scripts/check_api_wheel.py
```

Set `TEST_DATABASE_URL` only to a dedicated PostgreSQL test service to run the API tests there. Each test creates/drops its own random schema. Do not run real workers or `build3d-gpu-smoke --confirm-gpu-spend` as part of CPU validation.

## Blocking inputs for live inference

- Owner-approved GPU provider/account, region, quota, hourly/total budget and stop conditions.
- Full approval of one exact model/weight/runtime dependency chain for the intended commercial deployment.
- Private authenticated upstream endpoint and runtime evidence that it serves those approved weights.

These block live inference and deployment, not further bounded CPU implementation. Keep user/customer data and all credentials out of Git and public PR discussions.
