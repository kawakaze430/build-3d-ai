# Coding Agent Instructions — Build 3D AI

Applies to every coding agent (including Codex/Astra), engineer and PR in this repository.

## Mission and source of truth

Read `docs/continuity/PROJECT_MEMORY_MASTER.md` first when resuming from a new/compacted chat. Then read `docs/project/BUILD_3D_AI_PROJECT_IDEA.txt` (the owner-adopted main project goal), `README.md`, `docs/project/PRODUCT_VISION.md`, `docs/architecture/ARCHITECTURE.md`, `docs/project/FEATURE_MATRIX.md`, `docs/research/OPEN_SOURCE_STRATEGY.md` and `docs/project/ROADMAP.md` before implementation. The master memory links the 112-repo study catalog, original owner assignment, exact PR/source history, decisions, videos, architecture chart and next tasks; it is a dated context index, not a substitute for checking live code/CI. Objective: an independently controlled **commercial** 3D creation platform, competitive with leading systems through **measured** quality.

The [main project goal](docs/project/BUILD_3D_AI_PROJECT_IDEA.txt) defines product direction and release priorities. Treat its future capabilities and horizons as conditional plans; current implementation evidence, acceptance checks, license review and explicit spending authorization still govern execution.

The [repository structure guide](PROJECT_STRUCTURE.md) identifies active components. `AnalyseFuture/` preserves inactive research sources and reference assets; do not install, execute, or promote them into the product without a reviewed task. Its contents are not classified as malicious merely because they are deferred. Keep original material and provenance when reorganizing it.

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

Create `docs/research/LICENSE_MATRIX.md` (per-source, model, weight and dependency), `docs/research/REUSE_AUDIT.md` (candidate code audits) and initial working CI. Then implement one genuine, license-cleared, image-to-3D GPU smoke test using a documented model adapter.

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


## Long-conversation continuity

When starting after chat truncation, read `docs/continuity/PROJECT_MEMORY_MASTER.md`, current `docs/continuity/CODEX_HANDOFF.md` and open PRs first. After material architecture, license, budget, test or milestone decisions, update the master memory and handoff docs without copying secrets or private uploads into this public repository. Preserve historical evidence with dates; re-check live GitHub status instead of trusting old PR counts.

## Functional collections and current validation boundary

Use [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) and [the complete inventory](AnalyseFuture/COMPLETE_FILE_INVENTORY.txt) to locate every functional collection. The owner subsequently authorized testing after the structural migration. The available final-layout checks passed after a Vitest alias correction; see [the current validation report](AnalyseFuture/validation/2026-11-17/REPORT.md). Keep fixture/local-runtime evidence distinct from real inference and production readiness. Keep historical source bytes and uncertain material outside active code.
