# Codex Handoff: Continue Phase 0 Without Wasting Credits

## What exists

The source PR at https://github.com/kawakaze430/build-3d-ai/pull/1 adds:
- 64-item prioritized checklist in `docs/IMPLEMENTATION_CHECKLIST.md`;
- an authenticated **real upstream** 3DAIGC-API connector in `apps/gateway`;
- Docker/Compose for the admin gateway;
- Python 3.11/3.12 GitHub Actions tests using isolated in-memory HTTP transport.

**NOT yet implemented:** GPU backend deployment, actual model weights/inference proof, frontend, customer database, multiuser auth, billing, model fine-tuning and full commercial license approvals. Never claim otherwise.

## First Codex Cloud task — audit before GPU

Copy these instructions to Codex connected to this repository:

> Read AGENTS.md, docs/IMPLEMENTATION_CHECKLIST.md, docs/OPEN_SOURCE_STRATEGY.md and the Phase 0 PR. Work first on GitHub issue #2 (legal/technical reuse audit).
>
> 1. Inspect upstream Open3DStudio, 3DAIGC-API, Step1X-3D, TRELLIS.2 and related model/dependency code at pinned commits. Determine what actually functions, which models require forks and which model checkpoints are available.
> 2. Write docs/REUSE_AUDIT.md and docs/LICENSE_MATRIX.md. For every candidate, record upstream SHA, source license, weight license, model/data conditions, transitive renderer/CUDA dependencies and commercial-SaaS verdict. Unknown rights = RESEARCH_ONLY, not APPROVED.
> 3. Do not start GPU instances, paid jobs, training, external deployments, modify account IAM, or upload datasets without explicit approval.
> 4. Review phase-0 gateway code for actual endpoint compatibility, image upload, authentication, timeouts, size limits and streaming tests. Improve any real bugs in a separate PR with tests.
> 5. Produce a **specific commercially permitted inference stack proposal**, requirements, expected GPU memory, approximate hourly cost by region and exact smoke-test commands.
> 6. After receiving GPU budget approval, begin issue #3: run real image→3D→GLB and report actual output quality, logs, VRAM, latency and cost. Keep the GPU private and stop when testing finishes.
> 7. Once #2/#3 are solved, proceed to issues #4 and #5 in order. Do not jump into billing or fine-tuning before a reliable core exists.
>
> For every PR: include what is truly implemented, what tests actually ran, any limitations, license status, the cheapest next test, and clear blockers. Avoid pointless rewrites of preexisting public technology.

## Required approvals before next spend

- Account owner: select permitted cloud provider and region, available credits, hourly and total spend cap, time limit, and instance access.
- Engineering/legal: model code, full dependency chain, weights and dataset commercial terms verified.
- Technical: signed-off exact base checkpoint + serving container, reproducible script and a stop command for GPU resources.

## Quick non-GPU reproduction

```bash
python -m pip install -e "./apps/gateway[test]"
python -m pytest -q apps/gateway/tests
```

Tests confirm contracts and authentication; not neural network execution. Only actual GPU inference can close the real-generation blocker.

## Branch and issue tracker

- PR: https://github.com/kawakaze430/build-3d-ai/pull/1
- Issue #2: https://github.com/kawakaze430/build-3d-ai/issues/2 (audit)
- Issue #3: https://github.com/kawakaze430/build-3d-ai/issues/3 (GPU/model)
- Issues #4–#10: subsequent deliverables, ordered
- Master checklist: [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)
