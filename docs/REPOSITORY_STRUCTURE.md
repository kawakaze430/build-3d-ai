# Repository structure and preservation

Prepared: 17 November 2026. Review baseline: `e4b05f4`.

The [owner-adopted main project goal](BUILD_3D_AI_PROJECT_IDEA.txt) remains the product direction: build on the existing first-party foundation, prove a focused real asset workflow, and develop reusable characters and environments through measured improvements. Organization changes preserve that foundation and separate deferred reference material from active development.

The owner reported disruption and requested recovery without deleting material. The review began with the expected local and remote `main` baseline and no post-baseline working-tree changes found. That observation does not independently confirm a hack, prove the absence of compromise, or establish GitHub account security. See the [dated repository audit](REPOSITORY_AUDIT_2026-11-17.md) for the scope, evidence and remaining uncertainties.

## Current layout

```text
build-3d-ai/
  apps/
    api/                         Private product API, durable jobs and storage
    gateway/                     Model policy, upstream contract and GLB checks
    web/                         Studio, private session boundary and GLB viewer
  services/
    generation/
      triposr_candidate/         First-party reviewed qualification preparation
  config/                        Configuration examples and policy-related inputs
  scripts/
    cloud/                       Reusable development install/start/test helpers
  docs/                          Main goal, evidence, decisions and runbooks
  .github/                       Active first-party workflows and templates
  AnalyseFuture/
    README.md                    Review status and reference navigation
    FILE_INDEX.json              Preservation inventory
    third_party/
      README.md                  Original source snapshot context and licenses
      3daigc-api/                 Supplied upstream source snapshot
      triposr/                   Supplied upstream source snapshot
    assets/
      reference/
        README.md                Original reference asset context and limitations
        autorig/                 Supplied models, demonstrations and diagrams
    history/                     Byte-identical original reference notes
  pytest.ini                     Default first-party test discovery
  .dockerignore                  Root build-context exclusions
  compose.gateway.yml            Gateway packaging entry point
  compose.product.yml            Product API/database packaging entry point
  requirements.lock              First-party CPU dependency constraints
  .env.example                   Configuration names/examples, without secrets
  AGENTS.md                      Coding-agent instructions and approval gates
  README.md                      Project entry point
```

## Active development and compatibility

`apps/` contains the first-party product code. Its package manifests, source, migrations and tests retain their existing paths. The web studio is not replaced by the upstream application snapshot.

`services/generation/triposr_candidate/` remains active first-party qualification work. It prepares and checks a separately pinned upstream Git checkout; it is distinct from the imported reference snapshot. Its existence does not establish that a model is approved, inference has run, or GPU spending is authorized.

`config/`, `scripts/`, root Compose files, `.env.example` and `requirements.lock` stay in place deliberately. Existing installation commands, Docker build contexts, migration commands, CI working directories and documented runtime paths depend on this layout. Moving files merely to make the root shorter would introduce unnecessary compatibility work.

Root `.github/` contains the repository's active workflows. Any upstream workflow examples nested inside `AnalyseFuture/` remain reference files rather than workflows installed at the repository root. Do not copy or enable them as part of organization work.

`docs/` retains the adopted goal, historical memory, architecture, audits, legal findings, benchmark plans and operating instructions. Older dated status paragraphs remain historical evidence; reconcile them against live code rather than treating every older claim as current. The [developer handoff](CODEX_HANDOFF.md) and [cloud development guide](CLOUD_DEVELOPMENT_ENVIRONMENT.md) describe how to resume work.

## Preserved research and reference material

The relocation map is:

| Previous location | Current location | Reason |
|---|---|---|
| `third_party/` | `AnalyseFuture/third_party/` | Keep supplied upstream snapshots and their context together for future review |
| `assets/reference/` | `AnalyseFuture/assets/reference/` | Keep supplied examples separate from private product artifacts |

These moves preserve the 242 previously tracked files in those trees: 240 archive content files plus two explanatory README files. The source snapshots, bundled binaries, assets and license files are retained; the explanatory README links can be adjusted for their new locations. The [archive inventory](ARCHIVE_IMPORTS.json) records the original supplied ZIP evidence, while the [preservation index](../AnalyseFuture/FILE_INDEX.json) records the current reference paths. Refer to the audit for verification actually completed.

`AnalyseFuture` means preserved material awaiting evaluation. It does not mean confirmed malicious code, approved product functionality or commercially cleared dependencies. A directory boundary does not prevent execution or isolate untrusted files; use an appropriately isolated runtime before any approved inspection that requires execution.

All imported content remains **RESEARCH_ONLY**. The 3DAIGC-API archive omits its declared submodule source, some bundled dependencies carry restrictions, and the example asset bundle has no supplied license. Preserve those facts and notices when considering selective reuse. Do not install bundled wheels, initialize upstream dependencies, download weights or start model services merely because the files are present.

Keep first-party checks explicit, for example `python -m pytest -q apps/api/tests apps/gateway/tests`. The root `pytest.ini` now defaults to the first-party suites and excludes `AnalyseFuture`; bypassing that configuration or explicitly targeting upstream files can still collect tests requiring separate runtimes or GPUs. Organization alone does not validate imported source or assets.

## What Git preserves

Committed files and their history are recoverable from Git. Running processes, installed dependencies, caches, private smoke-test credentials and private application state require separate restoration or regeneration. Ignored local files must not be mistaken for remotely preserved content. Do not add secrets or private application data to a public preservation inventory.

## Next development priority

Resume from the existing foundation and qualify one real generation-to-textured-GLB workflow, including browser inspection and Blender import, under the existing exact model/runtime rights, dependency verification and bounded spending gates. Use the [main project goal](BUILD_3D_AI_PROJECT_IDEA.txt) for the broader product direction; future features and one-/two-/later-year horizons remain conditional plans rather than delivery or budget commitments.
