# Coding Agent Instructions — Build 3D AI

Applies to every coding agent (including Codex/Astra), engineer and PR in this repository.

## Mission and source of truth

Read `README.md`, `docs/PRODUCT_VISION.md`, `docs/ARCHITECTURE.md`, `docs/FEATURE_MATRIX.md`, `docs/OPEN_SOURCE_STRATEGY.md` and `docs/ROADMAP.md` before implementation. Objective: an independently controlled **commercial** 3D creation platform, competitive with leading systems through **measured** quality.

## Required working method

1. **Inspect before coding.** Determine what is present, what works and what is missing. Preserve useful existing changes.
2. **Reuse first.** Before implementing a major feature, search for mature public implementations; document fit, tests, upstream commit, licenses, operational limits, and estimated effort. Do not rebuild a good UV library, GLB optimizer, viewer or rigging engine without justification.
3. **Legal gate first.** Audit upstream source license, model-weight license, data/training rights, all transitive dependencies, geographic/SaaS restrictions and attribution. If uncertain, mark RESEARCH_ONLY; do not connect it to commercial deployment.
4. **Independent architecture.** Prefer one product monorepo with adapters and isolated model containers. Do not mix incompatible CUDA/PyTorch environments or blindly vendor entire repos.
5. **No fake completeness.** Never claim mocked generation, static screenshots, placeholder mesh files or an unverified README claim as a deployed feature. Label actual tests and limitations.
6. **Small verified deliveries.** Each PR should have a testable vertical slice, acceptance criteria, docs, reproducible commands, dependency/credit impact and rollback instructions.
7. **Financial guardrails.** Never start paid GPU instances, training jobs, services, domains, billing or large data downloads without explicit project-owner approval and a budget limit. Cloud credits must be checked for expiry and eligibility.
8. **Security first.** No secrets in Git; isolate untrusted 3D files and Blender execution; require authentication and object-level authorization; rate limit requests.
9. **Benchmarks.** Record hardware, model revision, seed/config, sample inputs, output artifacts, failures, VRAM, latency and cost. Don't optimize from anecdotes.
10. **Honest reporting.** Explicitly mark what was implemented, actually tested, untested for lack of GPU, blocked by license, and blocked by external permissions.
11. **Protect the product.** Preserve original license notices, keep our original brand and first-party business logic independent; do not claim exclusive ownership of imported open-source components.
12. **No autonomous indefinite loops.** Work in bounded reviewable tasks; stop at acceptance criteria, failing dependencies, spend approvals or blocked permissions.

## First developer/Codex assignment

Create `docs/LICENSE_MATRIX.md` (per-source, model, weight and dependency), `docs/REUSE_AUDIT.md` (candidate code audits) and initial working CI. Then implement one genuine, license-cleared, image-to-3D GPU smoke test using a documented model adapter.

Deliver real command output, valid GLB proof, recorded VRAM/latency, and a summary of what remains unverified. **Do not initiate paid GPU resources without explicit approval.**

## Pull request template

- Problem / customer outcome
- Existing solution search and reuse decision
- License and commercial-use status
- Architecture change / interface contract
- Tests actually executed and results
- Screenshots or artifact links only if real
- Estimated compute, credits and operating costs
- Security and privacy impact
- Rollback/feature flag and remaining risks

If a feature has no reliable acceptance test, write the test specification before asserting completion.
