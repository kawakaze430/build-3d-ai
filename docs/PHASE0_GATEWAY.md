# Phase 0: Real 3DAIGC Backend Integration Gateway

**Implemented in this branch:** protected FastAPI routes that speak the documented real upstream 3DAIGC-API endpoints. It does NOT host a GPU model, create customer accounts, or generate anything when no real upstream inference backend is installed.

**Real upstream source:** https://github.com/FishWoWater/3DAIGC-API at commit `9c5643f99cbfd8d47b81922790f0d0a36be57e81` inspected 2026-11-13. Validate compatibility again before production.

## Approval prerequisite

**Generation is disabled by default even when an upstream GPU model is running.**
Read [MODEL_APPROVAL_GATE.md](MODEL_APPROVAL_GATE.md): the administrator must pass a reviewed, exact model ID and mount an approved-model policy before dispatch. The shipped policy has zero approvals. `/v1/models` shows upstream inventory, not licensed/commercial availability.

## What exists now

- Readiness of gateway process (`GET /health`), explicitly not GPU readiness.
- Owner-key protected upstream status and model listing.
- Real `POST /v1/generations/text`: forwards to upstream `/api/v1/mesh-generation/text-to-textured-mesh`.
- Real `POST /v1/generations/image`: validates signature and upload size, calls upstream file upload then generation.
- Authenticated `GET /v1/jobs/{job_id}` polling and binary download proxy.
- Tests verify API paths, authentication and failure propagation with an in-memory HTTP transport; **tests do not prove real inference**.
- No anonymous public access: local machine is the intended first-run setting, all job operations need owner control key.

## Run the gateway locally (no GPU required to start process)

Use Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./apps/gateway[test]"
cp .env.example .env
# Set CONTROL_API_KEY to a new random 32+ character secret
# Optional UPSTREAM_BEARER_TOKEN is the upstream API login token
set -a; source .env; set +a
uvicorn build3d_gateway.main:app --host 127.0.0.1 --port 8080
```

Windows PowerShell: create venv with `py -m venv .venv`, activate `.venv\\Scripts\\Activate.ps1`, set environment variables in PowerShell; do not use `source`.

To run via Docker after filling `.env`: `docker compose -f compose.gateway.yml up --build`. The included Compose exposes the gateway only at localhost. **Do not publish this admin gateway directly to customers.**

## Bring your own real private GPU backend

1. Check the full license matrix for chosen 3D model, pretrained weights, render/texture dependencies and commercial service use.
2. Deploy the upstream project separately on a GPU at an approved cost and set `UPSTREAM_BASE_URL`; use `P3D_USER_AUTH_ENABLED=True` upstream with a service token where supported.
3. Use a private network or VPN. Do not put the upstream backend or control token in browser JavaScript.
4. Query real model availability and choose `model_preference` from the response. A model listed by README might not be installed.
5. Obtain verified weight hash and full commercial-use review, then configure the exact approved backend model ID in a read-only `MODEL_APPROVAL_FILE`.
6. Run actual inference and record output artifact hash, GPU hardware, VRAM, time and price.

Example using the gateway:

```bash
export CONTROL_API_KEY="<actual random owner secret>"
curl -H "X-Control-Key: $CONTROL_API_KEY" http://127.0.0.1:8080/v1/models
curl -X POST http://127.0.0.1:8080/v1/generations/text \
  -H "X-Control-Key: $CONTROL_API_KEY" -H "Content-Type: application/json" \
  -d '{"prompt":"A stylized robot cat","model_preference":"REPLACE_WITH_APPROVED_ID"}'
curl -X POST http://127.0.0.1:8080/v1/generations/image \
  -H "X-Control-Key: $CONTROL_API_KEY" \
  -F "file=@./reference.png;type=image/png" \
  -F "model_preference=REPLACE_WITH_APPROVED_ID"
curl -H "X-Control-Key: $CONTROL_API_KEY" http://127.0.0.1:8080/v1/jobs/REPLACE_JOB_ID
curl -H "X-Control-Key: $CONTROL_API_KEY" \
  http://127.0.0.1:8080/v1/jobs/REPLACE_JOB_ID/download -o output.glb
```

## Limitations / blockers: must fix before SaaS launch

- This is a **single-owner administrative integration gateway**, NOT user registration, a database, tenant isolation, quotas or billing. It must not be exposed as a public SaaS.
- No GPU instance has been launched, no weights downloaded, no paid credits used and no real mesh generated in this branch.
- The upstream project may change response schema or model endpoints; pin and integration-test.
- The maximum upload is 10 MiB and download is 250 MiB. Compressed/invalid image payload safety, downstream script execution, body lifetime limits and malware isolation need separate production hardening.
- No durability if the upstream job server crashes; future application must persist jobs/artifacts independently with audit and owner permissions.
- Download proxy currently treats output as a GLB by convention; verify magic bytes and format for production.
- Production must add isolated networking, mTLS or workload identities, rate limiting, customer-level auth, storage and abuse prevention.
- No commercial use of a weight or dependency until legal approval of its **complete** dependency chain.

## Execute tests

```bash
python -m pip install -e "./apps/gateway[test]"
python -m pytest -q apps/gateway/tests
```

Use `docs/IMPLEMENTATION_CHECKLIST.md` for the complete ordered tasks.
