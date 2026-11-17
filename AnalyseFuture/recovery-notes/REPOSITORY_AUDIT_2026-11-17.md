# Repository structure and preservation audit — 17 November 2026

## Reported concern and observed evidence

The owner reported compromised GitHub access, unwanted files and a disrupted
folder structure, and requested direct `main` restructuring without deleting
questionable material. This report covers the connected
`kawakaze430/build-3d-ai` repository and its inspected `main` snapshot.

At inspection, local HEAD and remote `main` both resolved to
`e4b05f4b3fd6d18ccbccd59d3bbc6927191c5348`, the last commit verified in this
conversation. The index and tracked working tree were clean. There were
**362 tracked files**, no additional untracked project files, and no later
remote-main commits. Existing ignored local dependencies, generated output,
metadata and private smoke-test data were kept separate from publication.

These observations do not establish whether GitHub account or organization
access was compromised. No post-baseline additions were observed on this main
branch, and no file was classified as malicious merely because it was an
upstream reference. Other repositories, deleted/rewritten history, GitHub audit
logs, collaborators, sessions, installed apps, secrets and infrastructure are
outside the evidence available from this tree review. The owner was invited
to identify another affected branch/repository if applicable; this change
proceeds against the connected main branch.

## Inspection performed

- Compared local/main identity, index and working-tree state with the previously
  verified baseline; fetched and checked the remote main reference.
- Enumerated all tracked paths and top-level responsibilities, and inspected
  existing remote branch names without merging unrelated branches.
- Reviewed active CI workflows, package manifests, Compose files, Dockerfiles,
  configuration and cloud helpers; searched first-party execution/network
  paths for unexpected destinations or newly hooked installers.
- Confirmed no active application, service, script, Compose or CI reference
  depended on the two relocated imported roots.
- Verified all 240 imported source/asset content files against the existing
  SHA256 archive inventory. No imported script, model, wheel, Blender file or
  upstream test suite was executed for the structure audit.

No newly added opaque execution, credential-exfiltration destination or root
installer integration was identified relative to the verified baseline.
This is a bounded source/layout review, not a vulnerability assessment,
malware certificate or account-security clearance.

## Active project retained

The following 120 other tracked baseline files remain in their appropriate
project roles: first-party `apps/`, qualification code in `services/`,
configuration, development scripts, root workflows, operational files and
project documentation. Root Compose files and dependency declarations stay in
place to preserve documented commands. First-party application code, tests,
workflows, package manifests and lockfiles are not rewritten by this task.

The existing API, durable worker, private studio, GLB viewer, artifact storage,
quota/identity foundations, and model-approval boundaries are preserved.
Raw upstream source is distinct from the first-party qualification adapter.
The default model approval list remains empty.

## Preservation and relocation

| Before | Current location | Baseline tracked files |
|---|---|---:|
| `third_party/` | `AnalyseFuture/third_party/` | 226 |
| `assets/reference/` | `AnalyseFuture/assets/reference/` | 16 |
| Total | Preserved reference area | 242 |

All 240 source and asset content files keep their exact bytes, including
licenses, upstream code, example meshes, skeletons, diagrams, demos and bundled
wheels. The two explanatory READMEs have repaired navigation. Their original
bytes are additionally retained at:

- `AnalyseFuture/history/third_party/README.md`
- `AnalyseFuture/history/assets/reference/README.md`

[FILE_INDEX.json](../AnalyseFuture/FILE_INDEX.json) records original/current
paths, original size/hash, classification, review reason and original-note
copies. [ARCHIVE_IMPORTS.json](ARCHIVE_IMPORTS.json) retains source ZIP hashes,
file hashes and original extraction locations, plus explicit relocation records.
Ignored `.DS_Store` metadata was moved with the local sample tree and remains
ignored. No original reference file is discarded. Git history is retained;
this task does not reset or rewrite earlier commits.

`AnalyseFuture/` means inactive material preserved for later evaluation. It
is not a malware verdict, execution sandbox or approval to reuse dependencies.
Existing source/weight/data/license restrictions remain, including bundled
noncommercial libraries, missing 3DAIGC submodule source and the example
bundle's absent license evidence. Future imports should receive explicit
classification and provenance; private credentials/customer material belong
in private evidence storage rather than this public directory.

## Navigation and workflow changes

The root README, structure guide, main project goal TXT, agent instructions,
continuity documents and archive manifest now distinguish active code from
the preserved review area. The TXT keeps the substantial existing product
vision, difficult/impossible guarantees, one-/two-/longer-year planning horizons
and responsible roles, and adds a structure-review addendum.

A root `pytest.ini` selects the established first-party CPU suites and excludes
`AnalyseFuture/` from default traversal. `.dockerignore` excludes that review
area from the root Docker context. Existing explicit qualification test
commands and the existing application/service paths remain available.

## Validation

Executed in this workspace for the reorganized tree:

| Check | Observed result |
|---|---|
| `.venv/bin/python -m pytest -q` using the new root configuration | 136 first-party tests passed |
| Explicit `test_prepare_runtime.py` suite | 3 tests passed; no weights/GPU required |
| Web TypeScript check (`--incremental false`) | Passed |
| Web unit tests | 4 tests passed |
| Production web build | Passed |
| Browser contract suite with retained system Chromium | 6 tests passed |
| Product and gateway Compose `config` with no interpolation/env resolution | Both passed; no service started |
| Preservation/index/archive SHA256 comparison | All 242 original tracked references and all 241 extracted local files retained; only metadata remains ignored |

Next.js generated changes were restored by the existing wrapper. Active
first-party source, test, dependency and workflow paths/content remain
unchanged. Existing library/test-fixture warnings were emitted, with no failures
or skips in the executed suites. Source/manifest/link and staged-blob checks
complete the preservation review before committing.

These software/browser/storage contracts use fixtures where documented. No
real inference, Blender import, real S3 operation, Docker image build or GPU
marching-cubes runtime qualification was performed. Passing Compose config is
not a successful container deployment. See also the
[structure guide](REPOSITORY_STRUCTURE.md) and
[development workflow](CLOUD_DEVELOPMENT_ENVIRONMENT.md).

## Remaining work and account recovery boundary

No real inference, model training, paid resource, S3 bucket or Blender import
was initiated for this restructure. The next technical priority remains the
bounded real-generation qualification in [FIRST_REAL_GPU_RUNBOOK.md](FIRST_REAL_GPU_RUNBOOK.md),
subject to its existing rights/runtime/budget gates. Future capabilities are
still proposed and conditional; directory movement does not implement them.

If unauthorized access occurred, separately inspect GitHub account and
organization access, revoke unauthorized sessions/tokens/keys/apps/collaborators,
review Actions access and rotate exposed secrets. A commit cannot revoke
external credentials or prove account recovery. No credential values or
private incident logs should be committed as evidence.
