# Real GPU Smoke Test and GLB Artifact Integrity

**Implementation status:** code and offline tests exist on the Phase 0 branch. **No paid GPU has been started and no real AI-generated GLB has been verified by this project.**

The owner-only gateway uses the actual [3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API) endpoints for text/image generation, polling and downloads. This PR adds:

- **GLB 2.0 preflight:** checks binary header, declared length, aligned chunks, JSON asset version, actual mesh primitives, embedded binary buffer lengths and rejection of external texture/buffer URIs.
- **Bounded downloading:** accepts at most 250 MiB from the upstream backend; stores in a private temporary file; rejects invalid results **before** sending an HTTP 200 response.
- **Artifact provenance:** completed gateway downloads return \`X-Artifact-SHA256\` and \`X-Artifact-Meshes\` headers.
- **Optional real GPU smoke tool:** makes a genuine model request (when explicitly authorized), polls until completed/failed, downloads GLB, re-verifies SHA256 and structure and prints a JSON timing/report record.

GLB structure checks are not full geometry validation: self-intersection, nonmanifold surfaces, missing/incorrect UV mappings, deformation fitness, material quality and Blender/Unity/Unreal round-trip still need GPU/visual/engine tests.

## Prerequisites before a live run

1. **Review and merge the foundational PRs in order:** [PR #1](https://github.com/kawakaze430/build-3d-ai/pull/1), then [PR #11](https://github.com/kawakaze430/build-3d-ai/pull/11), then the PR containing this file (PR base is #11's implementation branch).
2. Finish the commercial [license review](LICENSE_MATRIX.md) of the **exact** model and its dependencies. Restricted or unapproved research models cannot be silently enabled.
3. Start a private, authenticated GPU inference server from a pinned upstream commit with an exact approved checkpoint. Get explicit provider/region/instance price and a spending cap from the owner. **This repo does not create that instance.**
4. Configure \`MODEL_APPROVAL_FILE\` pointing to a signed-off JSON document with the exact installed model ID and SHA256 of downloaded weights. The repo's built-in policy has **zero approvals**.
5. Set unique \`CONTROL_API_KEY\` (24+ characters), private \`UPSTREAM_BASE_URL\` and \`UPSTREAM_BEARER_TOKEN\` as required in an uncommitted \`.env\`. Keep both services on loopback/private networks.

## Install CPU gateway + smoke command

From the repo root:

\`\`\`bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "./apps/gateway[test]"
python -m pytest -q apps/gateway/tests
\`\`\`

For PowerShell on Windows, activate via \`.venv\Scripts\Activate.ps1\` and set environment variables using PowerShell rather than \`source\`.

Start the gateway **only after** verifying that model policy, private upstream, credentials and budget are configured:

\`\`\`bash
# From a shell with CONTROL_API_KEY, MODEL_APPROVAL_FILE,
# UPSTREAM_BASE_URL and UPSTREAM_BEARER_TOKEN configured:
uvicorn build3d_gateway.main:app --host 127.0.0.1 --port 8080
\`\`\`

Run a **real, billable inference** only with owner authorization. The \`--confirm-gpu-spend\` flag is mandatory:

\`\`\`bash
# In a second terminal with CONTROL_API_KEY:
build3d-gpu-smoke \
  --gateway-url http://127.0.0.1:8080 \
  --model EXACT_APPROVED_BACKEND_MODEL_ID \
  --image /path/to/licensed-reference.png \
  --output ./artifacts/first-real-mesh.glb \
  --timeout-seconds 900 \
  --poll-seconds 5 \
  --confirm-gpu-spend > ./gpu-smoke-report.json
\`\`\`

For a text-conditioned backend:

\`\`\`bash
build3d-gpu-smoke \
  --model EXACT_APPROVED_BACKEND_MODEL_ID \
  --prompt "A stylized wooden chair with four legs" \
  --output ./artifacts/chair.glb \
  --confirm-gpu-spend
\`\`\`

**Do not run these commands yet** until the licensing and GPU approval blockers are resolved. A failing command may still incur compute costs on an already-running GPU.

## Measured result and completion criteria

The smoke tool reports the true job ID, model ID, elapsed wall-clock time, GLB SHA256, bytes, mesh primitives and materials. It intentionally sets \`gpu_hardware\`, \`gpu_vram_gb\` and \`gpu_cost_usd\` to \`null\` until measured from provider/runtime logs.

To close [Issue #3](https://github.com/kawakaze430/build-3d-ai/issues/3), attach:

- Full actual setup commands, exact upstream SHA and checkpoint hash, machine type, region and hourly price.
- Private (redacted) GPU server and model logs with peak VRAM and wall-clock timing.
- A valid output GLB SHA256 and at least two independent viewer/Blender import screenshots from front and back.
- PBR/UV/mesh quality notes; failures are part of the benchmark, not discarded.
- Total provider spend including startup, downloads, GPU idle time, inference, retries and storage.
- Cloud resource shutdown evidence and a deployment rollback procedure.

## Offline CI vs GPU validation

GitHub Actions tests use a tiny **synthetic triangle GLB** and mocked upstream HTTP transport. They cover truncation, invalid headers, external dependencies, fake "glTF" blobs, invalid models, missing approval, large downloads and intentional errors. They do **not** prove a model has been installed, generated meshes, or matches Meshy/Tripo quality.

## Operational limits

- This is still an **owner-controlled Phase 0 gateway**, not a secure multiuser SaaS. Do not make it publicly reachable.
- A 250 MiB on-disk temporary copy is used to validate large downloads; ensure private temporary storage and enough disk. It is removed after the response is served; operational cleanup monitoring is needed before public scale.
- The smoke command refuses non-loopback HTTP and credential-bearing URLs; use HTTPS for remote gateway connections.
- \`--confirm-gpu-spend\` is an acknowledgement, **not a GPU billing limit**. Enforce real budgets at the cloud provider and job scheduler before use.
