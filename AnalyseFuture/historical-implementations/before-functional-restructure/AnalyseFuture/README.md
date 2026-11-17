# Preserved material for future review

This directory keeps upstream source snapshots and sample assets separate from
active first-party applications. The owner requested this preservation area
while reporting unwanted files and structure disruption on 17 November 2026.
The inspected local and remote `main` matched previously verified commit
`e4b05f4`; no post-baseline additions were found on that branch. Placement here
means **RESEARCH_ONLY**, not confirmed maliciousness or commercial approval.

```text
AnalyseFuture/
  README.md                       Classification and review rules
  FILE_INDEX.json                 Original/current paths and SHA256 inventory
  third_party/
    README.md                     Source provenance and license notes
    3daigc-api/                    Unchanged supplied upstream snapshot
    triposr/                      Unchanged supplied upstream snapshot
  assets/reference/
    README.md                     Sample asset provenance and limitations
    autorig/                      Models, skeletons, demos, prompts and diagrams
  history/
    third_party/README.md         Original source notes, byte-for-byte
    assets/reference/README.md    Original sample notes, byte-for-byte
```

All 242 previously tracked reference files are retained. The 240 supplied
source/asset files keep their exact bytes. Two explanatory README files have
updated navigation and additional byte-identical copies under `history/`.
Historical note links reflect the former layout; use the current README files
for navigation. Ignored local `.DS_Store` metadata, if present, was retained
with its directory but is not published.

The [file index](FILE_INDEX.json) records every original and current tracked
path, size, SHA256, classification and reason. The
[archive manifest](../docs/ARCHIVE_IMPORTS.json) retains extraction provenance
and records the relocation without changing original archive/file hashes.

This area is excluded from root Docker build context and default first-party
pytest discovery. No model, wheel, upstream script or 3D asset was executed
as part of the move. It is still normal repository storage, **not an execution
sandbox**. Do not run supplied commands or load arbitrary models merely to
inspect these files.

Before adopting anything here, review source and weight/data rights, bundled
libraries, security, exact revisions, runtime compatibility, supported outputs,
resource costs and meaningful acceptance checks. The bundled noncommercial
wheels, missing 3DAIGC submodules, and unlicensed sample-asset bundle retain
their existing restrictions and unknowns. Preserve licenses and useful context;
move newly identified questionable material here with a reason and provenance
instead of deleting it. Credentials and private customer content require a
private evidence location and must not be published here.

The [active structure](../docs/REPOSITORY_STRUCTURE.md),
[dated audit](../docs/REPOSITORY_AUDIT_2026-11-17.md), and
[main project goal](../docs/BUILD_3D_AI_PROJECT_IDEA.txt) explain current
boundaries and the separate future implementation plan.
