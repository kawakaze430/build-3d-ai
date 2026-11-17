# Preserved research, recovery records and future work

`AnalyseFuture/` is organized by purpose. It contains inactive reference code,
retained earlier versions, provenance, recovery evidence and future planning.
It is not a dumping ground, an execution sandbox, a malware verdict or a grant
of commercial permission.

| Collection | What belongs here |
|---|---|
| `third_party/` | Supplied upstream source snapshots with original internal paths/licenses |
| `assets/reference/` | Supplied sample models, skeletons, diagrams and demos |
| `historical-implementations/` | Byte-preserved earlier source, configuration, documents and authored working versions |
| `history/` | Original notes from the earlier reference-folder relocation |
| `experiments/generated-nextjs/` | Generated configuration/instruction artifacts retained as inactive text |
| `recovery-notes/` | Owner requests, earlier audit context and managed-build diagnostic recipes |
| `repository-inventory/` | Starting/current classifications, branch/history reviews, hashes, mappings and delivery evidence |
| `validation/` | Dated executed checks, initial failures, fixes and remaining limits |
| Root `*.txt` reports | Current recovery, feature, security, consolidation and continuation records |

Start with the [repository audit](REPOSITORY_AUDIT.txt),
[complete file inventory](COMPLETE_FILE_INVENTORY.txt),
[feature inventory](FEATURE_INVENTORY.txt),
[path mapping](ORIGINAL_TO_NEW_PATH_MAPPING.txt), and
[preservation manifest](ARCHIVED_FILES_MANIFEST.txt).
The [future roadmap](PROJECT_VISION_AND_FUTURE_ROADMAP.txt) is a detailed dated
companion to the [adopted main goal](../docs/project/BUILD_3D_AI_PROJECT_IDEA.txt).
[PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) is the current directory guide.

All 369 starting tracked file contents and all 432 files in the pre-functional
working snapshot have a byte-identical retained copy. The earlier 242 reference
relocation records remain historical evidence in [FILE_INDEX.json](FILE_INDEX.json).
The [archive import record](repository-inventory/ARCHIVE_IMPORTS.json) retains
original archive hashes and source/asset locations. The separate functional
mapping records the final additional moves; historical records are not silently
rewritten as though earlier reviews used the current layout.

Raw upstream code, wheels and 3D assets remain inactive. Existing noncommercial
restrictions, missing source submodules and absent sample-asset license evidence
still apply. Review exact source/weights/data/dependencies, safety, compatibility,
resources and acceptance before adoption. Do not execute preserved commands or
install binaries merely because they are present. Source copies and generated
notes here are excluded from the active root Docker context and default test
discovery; explicitly targeting them can still execute code.

Private credentials, live databases and installed dependency caches do not
belong in this public evidence area. They remain local or need a private backup.
The owner subsequently authorized tests; available local final-layout checks
passed after the Vitest alias fix. See [the current report](validation/2026-11-17/REPORT.md). This does not establish real inference or production readiness.
