# Project structure and ownership

This is the current directory guide for **Build 3D AI**. Files are grouped by
what they do, not by extension. The complete path-by-path inventory is in
[AnalyseFuture/COMPLETE_FILE_INVENTORY.txt](AnalyseFuture/COMPLETE_FILE_INVENTORY.txt).
The [main goal](docs/project/BUILD_3D_AI_PROJECT_IDEA.txt) defines product direction;
research code and future plans do not establish implemented product features.

## Repository map

```text
build-3d-ai/
  apps/
    api/                         Private product API and durable worker package
      src/build3d_api/           Tenancy, projects/jobs, identity and artifact logic
        migrations/versions/    Versioned SQL migrations
      tests/                    API, identity, storage and recovery contracts
      pyproject.toml            Product package and CLI entry points
      Dockerfile                Product CPU image; root build context
    gateway/                     Private model-service boundary and reusable GLB tools
      src/build3d_gateway/       Approval policy, upstream client, validation and packaging
      tests/                    Gateway, GLB, packaging and smoke-runner contracts
      pyproject.toml            Reusable gateway package and CLI entry points
      Dockerfile                Gateway CPU image; same root dependency constraints
    web/
      src/app/                  Next.js pages, layouts and server route entry points
        api/session/            Private browser login/session boundary
        api/product/            Allowlisted tenant API proxy
      src/features/
        studio/components/      Private project/job workspace UI
        assets/components/      GLB inspection and viewer controls
        jobs/                   Job-state presentation and its colocated tests
      src/lib/
        client/                 Browser API client and its colocated tests
        server/                 Server-only API/session helpers and bounded request reads
        contracts.ts            Shared browser/API data shapes
      tests/                    Synthetic backend and browser workflow contracts
      package.json              Web dependency and command entry point
      playwright.config.ts      Authoritative browser-contract server configuration
      next.config.ts            Framework configuration, kept at the framework root
      tsconfig.json             TypeScript root and src alias
  services/generation/
    triposr_candidate/          Isolated first-party qualification preparation and audits
  infrastructure/compose/
    gateway.yml                 Private gateway deployment definition
    product.yml                 Product API, PostgreSQL and opt-in worker definitions
  config/identity/              Reviewed identity-provider configuration example
  scripts/
    cloud/                      Install/start/browser helpers for managed development
    packaging/                  Distribution and wheel verification helpers
  docs/
    project/                    Goal, scope, feature map, backlog, roadmap and benchmarks
    architecture/               Components, design decisions and identity boundaries
      adr/                      Focused architectural decision records
    development/                Environment setup and gateway development guidance
    operations/                 Backend/storage/security/model-approval/GPU runbooks
    research/                   Model/data/reuse/license studies and dependency evidence
    continuity/                 Master memory, handoff and implementation checklist
  AnalyseFuture/                Preserved references, historical work and recovery records
    third_party/                Unchanged supplied upstream source snapshots
    assets/reference/           Supplied example meshes, skeletons and demos
    historical-implementations/ Superseded/earlier source and document versions
    history/                    Original notes from the earlier archive relocation
    experiments/                Generated/uncertain artifacts preserved outside active code
    recovery-notes/             Owner requests, earlier audits and diagnostic recipes
    repository-inventory/       Baseline, history, feature, path and preservation evidence
    validation/                 Dated executed checks, fixes and remaining limits
    *.txt                       Complete audit, consolidation and continuation reports
  .github/workflows/            Active first-party GitHub Actions entry points
  requirements.lock             Common root CPU dependency constraints
  pytest.ini                    First-party test discovery policy; excludes AnalyseFuture
  .env.example                  Root runtime variable names and safe examples
  .gitignore                    Private state/generated dependency exclusions
  .dockerignore                 Root image-context exclusions, including AnalyseFuture
  AGENTS.md                     Repository-wide contributor/agent instructions
  CONTRIBUTING.md               Contribution entry point
  README.md                     Product entry point and essential navigation
  PROJECT_STRUCTURE.md          This authoritative structure/ownership guide
  PROJECT_STATUS_AND_TASKS.md   Current goal/status, implementation tasks and full file guide
  research.md                   Future model fine-tuning research and experiment plan
```

## Why these boundaries remain

The API and gateway are separate installable Python packages. Their package
roots, `src` layout, migrations, entry points, package data and tests remain
cohesive functional collections. Flattening them into a language-wide folder
would break imports, packaging and deployment responsibilities. The gateway
owns reusable upstream and GLB primitives; the API owns tenancy, persistence,
jobs, quotas and storage. Their shared code is imported rather than copied.

Next.js requires `src/app` routes and root framework configuration. Those stay
in their conventional locations. Feature-specific UI, state presentation,
browser calls and server-only logic now have explicit functional homes.
Colocated unit files move with the code they describe. No public HTTP route,
database schema or package entry point is renamed by these organizational moves.

The generation candidate stays isolated from product CPU dependencies. Raw
upstream code is preserved separately; its source tree is an integrity-preserved
research snapshot, so its internal relative paths and licenses stay intact.
The nested directories were inventoried rather than rearranged arbitrarily.

Root shared constraints, Git policies and GitHub workflow entry points stay at
the repository root because they govern the entire project or have mandatory
provider conventions. App-specific manifests and Dockerfiles stay with their
application. Deployment composition belongs in `infrastructure/compose/`.

## Working-directory and path rules

Run repository commands from the repository root unless a guide says otherwise.
Compose definitions now use `../..` build contexts and `../../.env` env-file
references relative to their own location. For example:

```bash
docker compose -f infrastructure/compose/product.yml config
docker compose -f infrastructure/compose/gateway.yml config
```

These are documentation examples, not commands executed during the final
no-tests restructuring. `.env` remains private and must be supplied locally.
Dockerfiles still copy package directories from the root context. Root
`requirements.lock`, `scripts/cloud/` and application CLI locations are stable.

Use `@/features/...` for cross-feature web imports and `@/lib/client/...` or
`@/lib/server/...` for boundary-specific helpers. Shared data contracts live at
`@/lib/contracts`. Existing root TypeScript aliases still point at `src`.

Use [docs/README.md](docs/README.md) to find functional documentation collections
and [the feature map](docs/project/FEATURE_MAP.md) to trace a feature across
browser, API, worker, tests, configuration and runbooks.

## Preservation and uncertain material

No original source, reference asset or historical implementation is discarded.
Moves and repaired references are recorded in
[ORIGINAL_TO_NEW_PATH_MAPPING.txt](AnalyseFuture/ORIGINAL_TO_NEW_PATH_MAPPING.txt)
and the machine-readable functional mapping. Earlier versions are preserved
in Git history and in `AnalyseFuture/historical-implementations/` when their
contents have been superseded or adapted. Source hashes record those decisions.

`AnalyseFuture` means inactive or retained for review, not proven malware and
not automatic commercial approval. It is not an execution sandbox. Raw scripts,
models, binary wheels, generated instructions and old deployment examples must
not be run simply because they are present. They are excluded from root build
context and default first-party test discovery. Existing license/data/runtime
limitations remain in force.

Local `.venv`, `node_modules`, `.next`, caches and `data/` are classified as
recreatable dependencies, generated output or private runtime state. They are
not project source and are not published to Git. Existing private values and
databases are retained locally; public reports include names/categories only.
Git internals and supplied credentials are not rearranged.

## Validation status for this reorganization

The owner subsequently requested **“pls test all”**, lifting the earlier pause.
Available local validation now passed: 136 SQLite/API/gateway tests, 83 PostgreSQL
API tests, 14 qualification tests, 14 web unit tests and six browser contracts.
TypeScript, production build, packaging/migrations, Compose configuration,
CPU containers and real API/studio flows also passed. One missing Vitest alias
was found and corrected; the original configuration is retained.

Read the [current report](AnalyseFuture/validation/2026-11-17/REPORT.md) for scope,
local versions, the initial failure and unavailable checks. GPU inference,
real S3, Blender and full production/hosted-CI acceptance remain unverified.
The earlier skip-CI commits record the owner's former pause; this validation
update no longer requests CI skipping. No history or protection is bypassed.
