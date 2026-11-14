"""Failure/restart tests use real DB transactions and synthetic HTTP responses."""
import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import httpx
import pytest
import sqlalchemy as sa

from build3d_api.db import create_database, jobs, users
from build3d_api.store import Store, StoreError
from build3d_api.worker import Worker, main
from build3d_gateway.upstream import UpstreamGateway


def make_worker(env, triangle, *, submit_result=None, remote_status="completed", body=None, settings=None):
    calls = []
    clock = [time.time() + 10]

    def handler(request):
        calls.append((request.method, request.url.path))
        assert request.headers["authorization"] == "Bearer private-upstream-token"
        if request.method == "POST":
            if request.url.path.endswith("/file-upload/image"):
                return httpx.Response(200, json={"file_id": "input_1"})
            if isinstance(submit_result, Exception):
                raise submit_result
            return httpx.Response(200, json=submit_result if submit_result is not None else {"job_id": "remote_1"})
        if request.url.path.endswith("/download"):
            return httpx.Response(200, content=triangle if body is None else body)
        if isinstance(remote_status, Exception):
            raise remote_status
        return httpx.Response(200, json={"status": remote_status})

    upstream = UpstreamGateway("http://fake-gpu", "private-upstream-token", transport=httpx.MockTransport(handler))
    store = Store(env.engine, settings or env.settings)
    worker = Worker(store, upstream, confirm_spend=True, clock=lambda: clock[0])
    return worker, calls, clock


def advance(worker, clock, seconds=10):
    clock[0] += seconds
    return asyncio.run(worker.step())


def row(env, job_id):
    return env.store.job(env.alice["user_id"], job_id)


def slots(env):
    with env.engine.connect() as conn:
        return conn.execute(sa.select(users.c.active_jobs).where(users.c.id == env.alice["user_id"])).scalar_one()


def test_text_flow_restart_validated_download_and_tenant_privacy(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle)
    assert advance(worker, clock)
    assert row(env, queued)["status"] == "running"
    # Simulate process replacement with a genuinely new connection pool.
    second_engine = create_database(env.settings.database_url)
    try:
        restarted = Worker(Store(second_engine, env.settings), worker.upstream,
                           confirm_spend=True, clock=lambda: clock[0])
        assert advance(restarted, clock)
    finally:
        second_engine.dispose()
    result = row(env, queued)
    assert result["status"] == "completed"
    assert result["model_approval"] == env.approval
    assert slots(env) == 0
    response = env.client.get(f"/v1/jobs/{queued}/download", headers=env.auth)
    assert response.status_code == 200 and response.content == triangle
    assert response.headers["x-artifact-sha256"] == hashlib.sha256(triangle).hexdigest()
    assert env.client.get(f"/v1/jobs/{queued}/download", headers=env.other).status_code == 404
    assert env.client.get(f"/v1/jobs/{queued}/artifact", headers=env.auth).json()["size_bytes"] == len(triangle)
    assert sum(method == "POST" for method, _ in calls) == 1
    assert not advance(worker, clock)


def test_image_flow_uses_persisted_validated_input(env, project, png, triangle):
    response = env.client.post(f"/v1/projects/{project}/jobs/image", headers={**env.auth, "Idempotency-Key": "img"},
                               data={"model_id": "test_model"}, files={"file": ("a.png", png, "image/png")})
    job_id = response.json()["id"]
    worker, calls, clock = make_worker(env, triangle)
    advance(worker, clock)
    advance(worker, clock)
    assert row(env, job_id)["status"] == "completed"
    assert row(env, job_id)["input_image"] is None
    assert ("POST", "/api/v1/file-upload/image") in calls
    assert ("POST", "/api/v1/mesh-generation/image-to-textured-mesh") in calls


def test_no_spend_acknowledgement_does_not_claim_or_contact_upstream(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle)
    worker.confirm_spend = False
    with pytest.raises(RuntimeError, match="confirm-gpu-spend"):
        advance(worker, clock)
    assert row(env, queued)["status"] == "queued" and calls == []
    with pytest.raises(SystemExit):
        main([])


@pytest.mark.parametrize("result", [httpx.ReadTimeout("SECRET MUST NOT LEAK"), {}, {"job_id": "../../bad"}, []])
def test_uncertain_submission_is_never_retried_and_keeps_quota(env, queued, triangle, result):
    worker, calls, clock = make_worker(env, triangle, submit_result=result)
    advance(worker, clock)
    assert row(env, queued)["status"] == "submission_unknown"
    assert slots(env) == 1
    advance(worker, clock, 10000)
    assert sum(method == "POST" for method, _ in calls) == 1
    response = env.client.get(f"/v1/jobs/{queued}", headers=env.auth)
    assert "SECRET" not in response.text and "private-upstream-token" not in response.text


def test_crash_after_claim_does_not_blindly_resubmit(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle)
    claimed = env.store.claim(now=clock[0])
    assert claimed["status"] == "dispatching"
    advance(worker, clock, env.settings.lease_seconds + 1)
    assert row(env, queued)["status"] == "submission_unknown"
    assert calls == []
    # A late original worker cannot overwrite the recovery decision.
    assert not env.store.transition(claimed, "running", now=clock[0], upstream_job_id="late")


def test_two_workers_cannot_claim_same_submission(env, queued):
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: Store(env.engine, env.settings).claim(), range(2)))
    assert sum(job is not None for job in claims) == 1
    assert row(env, queued)["status"] == "dispatching"


def test_queued_cancel_and_worker_claim_race_cannot_dispatch_canceled_job(env, queued):
    def cancel():
        try:
            return env.store.cancel(env.alice["user_id"], queued)["status"]
        except StoreError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        cancel_future = pool.submit(cancel)
        claim_future = pool.submit(env.store.claim)
        canceled, claimed = cancel_future.result(), claim_future.result()
    if canceled == "canceled":
        assert claimed is None and slots(env) == 0
    else:
        assert canceled == 409 and claimed["status"] == "dispatching" and slots(env) == 1


def test_revoked_or_changed_policy_blocks_pending_gpu_job(env, queued, triangle):
    changed = {**env.approval, "checkpoint_sha256": "c" * 64}
    env.policy.write_text(json.dumps({"schema_version": 1, "approved_models": [changed]}))
    worker, calls, clock = make_worker(env, triangle)
    advance(worker, clock)
    assert calls == []
    assert row(env, queued)["error_code"] == "model_approval_changed"
    assert row(env, queued)["status"] == "failed" and slots(env) == 0


def test_known_upstream_failure_releases_quota_and_does_not_download(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle, remote_status="failed")
    advance(worker, clock)
    advance(worker, clock)
    assert row(env, queued)["status"] == "failed" and slots(env) == 0
    assert not any(path.endswith("/download") for _, path in calls)


def test_read_failures_backoff_then_pause_without_resubmission(env, queued, triangle):
    settings = replace(env.settings, max_poll_failures=2)
    worker, calls, clock = make_worker(env, triangle, remote_status=httpx.ConnectError("failure"), settings=settings)
    advance(worker, clock)
    advance(worker, clock)
    assert row(env, queued)["status"] == "running"
    assert not advance(worker, clock, 1)
    advance(worker, clock, 20)
    assert row(env, queued)["status"] == "polling_paused"
    assert slots(env) == 1
    advance(worker, clock, 10000)
    assert sum(method == "POST" for method, _ in calls) == 1


def test_invalid_glb_never_becomes_completed_or_downloadable(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle, body=b"fake mesh", settings=replace(env.settings, max_poll_failures=1))
    advance(worker, clock)
    advance(worker, clock)
    assert row(env, queued)["status"] == "polling_paused"
    assert env.client.get(f"/v1/jobs/{queued}/download", headers=env.auth).status_code == 409
    assert list(env.settings.artifact_dir.iterdir()) == []


def test_tampered_or_missing_stored_glb_is_rejected(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle)
    advance(worker, clock)
    advance(worker, clock)
    path = next(env.settings.artifact_dir.glob("*.glb"))
    path.write_bytes(b"corrupt")
    assert env.client.get(f"/v1/jobs/{queued}/download", headers=env.auth).status_code == 503
    path.unlink()
    assert env.client.get(f"/v1/jobs/{queued}/download", headers=env.auth).status_code == 503


def test_disk_failure_never_publishes_complete_job(env, queued, triangle, monkeypatch):
    worker, calls, clock = make_worker(env, triangle)
    advance(worker, clock)

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr("build3d_api.worker.os.replace", fail)
    advance(worker, clock)
    assert row(env, queued)["status"] == "running"
    assert list(env.settings.artifact_dir.iterdir()) == []
    assert slots(env) == 1


def test_lost_poll_lease_is_reclaimable_and_stale_worker_cannot_finish(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle)
    advance(worker, clock)
    clock[0] += 10
    stale = env.store.claim(now=clock[0])
    assert stale["status"] == "running"
    clock[0] += env.settings.lease_seconds + 1
    fresh = env.store.claim(now=clock[0])
    assert fresh["lease_token"] != stale["lease_token"]
    assert not env.store.transition(stale, "failed", now=clock[0])
    assert env.store.transition(fresh, "failed", now=clock[0])
    assert slots(env) == 0


def test_timeout_keeps_quota_and_does_not_claim_gpu_was_canceled(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle, remote_status="running")
    advance(worker, clock)
    advance(worker, clock, env.settings.job_timeout_seconds + 1)
    assert row(env, queued)["status"] == "timed_out" and slots(env) == 1
    assert env.client.post(f"/v1/jobs/{queued}/cancel", headers=env.auth).status_code == 409


def test_reconcile_attaches_existing_job_and_never_repeats_inference(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle, submit_result={})
    advance(worker, clock)
    env.store.reconcile(queued, "recovered_2")
    advance(worker, clock)
    assert row(env, queued)["status"] == "completed"
    assert ("GET", "/api/v1/system/jobs/recovered_2") in calls
    assert sum(method == "POST" for method, _ in calls) == 1


def test_reconcile_releases_uncertain_slot_only_with_operator_acknowledgement(env, queued, triangle):
    worker, calls, clock = make_worker(env, triangle, submit_result={})
    advance(worker, clock)
    with pytest.raises(StoreError, match="Confirm"):
        env.store.reconcile(queued, None)
    assert slots(env) == 1
    env.store.reconcile(queued, None, confirm_stopped=True)
    assert slots(env) == 0 and row(env, queued)["status"] == "failed"
    with pytest.raises(StoreError):
        env.store.reconcile(queued, None, confirm_stopped=True)
    assert slots(env) == 0
