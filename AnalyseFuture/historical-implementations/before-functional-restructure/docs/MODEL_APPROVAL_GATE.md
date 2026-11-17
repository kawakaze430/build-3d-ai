# Model Approval Gate — Phase 0

This PR prevents the owner-only gateway from dispatching generation to a 3DAIGC-API model that was not explicitly reviewed. It is an **operational guard**, not an automated legal determination.

## Safe defaults

The shipped file `apps/gateway/src/build3d_gateway/model-approvals.json` contains **zero approved models**. Consequently:

- `GET /health` remains an API-process check, not a GPU health claim.
- Authenticated `GET /v1/models` shows upstream capabilities, not commercial permission.
- Authenticated `GET /v1/approved-models` shows only reviewed runtime IDs (empty initially).
- Missing `model_preference` results in HTTP 422; an unknown ID returns HTTP 403 if at least one approved model exists.
- With zero approvals, a valid model ID returns HTTP 503, and upstream generation is never called.
- Missing or malformed approval files also return HTTP 503 instead of enabling an implicit upstream default model.

The gateway is **not** an end-user SaaS. It must remain private with an unguessable owner control key, authorized upstream bearer token, and restricted network access.

## Production approval workflow

1. Complete the human-reviewed [license matrix](LICENSE_MATRIX.md) for the *exact* backend adapter, source revision, model weights, renderer, imported dependencies, and commercial/territorial rights.
2. Inspect the backend's real `/api/v1/system/models` response and choose the exact ID, not a guessed friendly name.
3. Hash the **real checkpoint bytes**, record the SHA-256 and upstream Git commit SHA, and obtain a signoff from the responsible reviewer.
4. Create a separate read-only JSON file with the approved entry. Set `MODEL_APPROVAL_FILE=/path/to/reviewed-file.json` in the gateway deployment.
5. Pass the exact `model_preference` to each text/image generation request and run a bounded real GPU smoke test after owner budget approval.

An entry must contain fields in this structure (all values below are placeholders, **not** approval):

```json
{
  "schema_version": 1,
  "approved_models": [{
    "model_id": "EXACT_APPROVED_BACKEND_ID",
    "commercial_saas_rights_verified": true,
    "license_review": "docs/LICENSE_MATRIX.md",
    "reviewed_by": "ACTUAL_REVIEWER",
    "reviewed_on": "2026-11-13",
    "upstream_commit_sha": "0000000000000000000000000000000000000000",
    "checkpoint_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  }]
}
```

The zero hashes are illustrative and **must never be used in deployment**. The parser checks formatting and required attestations, not cryptographic correctness against installed weights or legal validity. Actual weight verification and compliance signoff remain operator responsibilities.

## Verify locally (without GPU)

```bash
python -m pip install -e "./apps/gateway[test]"
python -m pytest -q apps/gateway/tests
```

The suite uses in-memory HTTP transport and synthetic reviewed-model fixture data. It checks denied and allowed dispatch, owner authorization, invalid policy, and upstream contract paths. It does **not** run inference, create actual GLB files, or approve any public model.

**Deployment caution:** `model-approvals.json` is packaged inside the gateway Python wheel. To change it in a running container, mount an explicitly reviewed JSON file at a read-only path and set `MODEL_APPROVAL_FILE`; do not edit generated container images or inject secrets in source control.
