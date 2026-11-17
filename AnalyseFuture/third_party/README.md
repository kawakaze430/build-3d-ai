# Upstream source snapshots

Relocated under `AnalyseFuture/` on 17 November 2026 for inactive reference review. The original notes are preserved in [history](../history/third_party/README.md); see the [review area guide](../README.md).

These are reference copies extracted from the owner's existing ZIP files on
17 November 2026. Product applications remain under `apps/`; the reviewed
TripoSR qualification adapter remains under `services/generation/triposr_candidate/`.
Neither source snapshot is installed or enabled by this import.

| Directory | Supplied archive | Source license | Revision evidence |
|---|---|---|---|
| `3daigc-api/` | `3DAIGC-API-main (2).zip` | Apache-2.0 in `LICENSE` | No commit recorded in the supplied ZIP |
| `triposr/` | `TripoSR-main.zip` | MIT in `LICENSE` | ZIP comment: `107cefdc244c39106fa830359024f6a2f1c78871` |

Upstream projects: [FishWoWater/3DAIGC-API](https://github.com/FishWoWater/3DAIGC-API)
and [VAST-AI-Research/TripoSR](https://github.com/VAST-AI-Research/TripoSR).
ZIP comments are provenance clues, not independent commit verification.
The [import inventory](../repository-inventory/ARCHIVE_IMPORTS.json) records the supplied ZIP
hashes, original paths, destination paths, sizes and SHA256 of every file.

Only the archives' outer `*-main/` wrappers were removed. Source files, internal
paths, bundled assets, wheels, licenses and notices are otherwise unchanged.
The original ZIPs were deleted after verifying extracted bytes. Git history
retains the original archives. Git does not retain empty directories.

## Research status and dependencies

All imported content is **RESEARCH_ONLY**. The top-level source licenses do not
clear models, datasets, bundled binaries or sample assets for commercial use.
The existing [license matrix](../../docs/research/LICENSE_MATRIX.md) and
[approval gate](../../docs/operations/MODEL_APPROVAL_GATE.md) still govern product integration.

The 3DAIGC snapshot's `.gitmodules` declares 11 dependencies whose source is
absent from the ZIP. This copy is not a complete submodule checkout; no
dependencies or model weights were downloaded during extraction. Its bundled
wheels are preserved as archive contents and were not installed:

| Wheel in `3daigc-api/assets/wheels/` | Included license evidence |
|---|---|
| `diso-0.1.4-cp310-cp310-linux_x86_64.whl` | CC BY-NC 4.0; noncommercial restriction |
| `kaolin-0.17.0-cp310-cp310-linux_x86_64.whl` | Apache license plus NVIDIA `LICENSE.NSCL`; covered work restricted to noncommercial research/evaluation |
| `utils3d-0.0.2-py3-none-any.whl` | MIT |

Preserving these files does not verify binary provenance or approve their use.
Keep upstream runtimes isolated from the product's Python environment.
Run first-party tests with their explicit paths, for example
`python -m pytest -q apps/api/tests apps/gateway/tests`; upstream test files
may require separate runtimes or GPUs. Nested `.github/` files are retained
reference files, not workflows installed in this repository's root `.github/`.

The [example asset bundle](../assets/reference/README.md) is stored separately.
