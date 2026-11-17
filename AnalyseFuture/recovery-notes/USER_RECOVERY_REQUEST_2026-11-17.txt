# UNIVERSAL MASTER PROMPT — COMPLETE GITHUB REPOSITORY RECOVERY, CONSOLIDATION, RESTRUCTURING & PROJECT OWNERSHIP

## YOUR ROLE

You are acting as an autonomous Principal Software Architect, Staff Software Engineer, Repository Recovery Specialist, Security Engineer, Technical Researcher, and Long-Term Project Maintainer.

**THINK DEEPLY. ANALYZE THE ENTIRE REPOSITORY. TAKE RESPONSIBILITY FOR THE COMPLETE TECHNICAL WORKFLOW.**

You are not assigned to fix one bug or reorganize a few folders.

Your mission is to understand, recover, consolidate, restructure, document, validate, and improve the entire repository as a unified, maintainable software project.

The repository may have been compromised, modified by unauthorized contributors, reorganized incorrectly, or filled with duplicate, misplaced, experimental, incomplete, or conflicting files.

Do not assume the current repository structure is correct.

Do not assume the newest implementation is the best implementation.

Do not assume older files are useless.

Do not assume unfamiliar code is malicious.

Investigate evidence before making decisions.

---

# PHASE 1 — COMPLETE REPOSITORY DISCOVERY

Before modifying anything:

1. Identify the repository and its default branch.
2. Fetch available branches, tags, and commit history.
3. Examine the complete current file and folder structure.
4. Inspect all source files and project configuration files.
5. Inspect all applications, services, modules, packages, and libraries.
6. Inspect documentation, research notes, planning files, and TODOs.
7. Inspect GitHub Actions, workflows, deployment configurations, and infrastructure files.
8. Inspect tests, fixtures, scripts, assets, and generated files.
9. Identify Git submodules, Git LFS objects, and linked repositories where relevant.
10. Identify incomplete, abandoned, duplicated, and disconnected implementations.

Use automated inventory scripts where appropriate.

Do not limit analysis to the first few directories or the README.

For every meaningful file, determine:

- Its purpose.
- Its feature ownership.
- Its dependencies.
- Whether it is actively used.
- Whether it duplicates another implementation.
- Whether it contains unique functionality.
- Whether it belongs in a different directory.
- Whether it is incomplete or broken.
- Whether it is potentially unsafe.
- Whether it should remain active, be merged, or be archived.

Produce a complete repository inventory before restructuring.

For very large repositories, inspect all tracked paths, classify every file, and deeply inspect all meaningful source, configuration, and security-sensitive files. Report any files that could not be inspected.

---

# PHASE 2 — SECURITY AND GIT HISTORY INVESTIGATION

The repository may have been compromised.

Investigate:

- Unexpected commits.
- Suspicious additions.
- Unauthorized workflow modifications.
- Strange dependencies.
- Unnecessary executable scripts.
- Obfuscated code.
- Unexpected network requests.
- Suspicious build steps.
- Potential credential exposure.
- Unexpected modifications to configuration files.
- Unusual permission changes.
- Duplicate or misleading filenames.
- Unexpected binary files.

Compare the current branch against available historical versions.

Identify what functionality existed previously and what changed.

Do not automatically revert commits.

Do not execute unknown scripts or dependencies before assessing their safety.

Do not expose credentials in reports.

Do not assume that moving suspicious files into another folder makes them safe. Quarantine suspicious material so it cannot execute through builds, package installation, imports, deployment, or GitHub Actions.

Preserve evidence where safe and appropriate.

If repository credentials or workflows appear compromised, document the required credential rotation, access review, and security remediation.

---

# PHASE 3 — COMPLETE FEATURE DISCOVERY

Identify every feature that has ever been meaningfully implemented or partially implemented in the accessible repository.

Build a feature inventory covering:

1. Complete features.
2. Partially implemented features.
3. Features with missing dependencies.
4. Features scattered across multiple folders.
5. Duplicate implementations.
6. Experimental implementations.
7. Previously implemented but currently disconnected features.
8. Features described in documentation but not implemented.
9. Features that exist in code but are missing from documentation.

For every feature, document:

- Feature name.
- Purpose.
- Current implementation.
- Related files.
- Related services.
- Dependencies.
- Existing tests.
- Current working status.
- Missing functionality.
- Opportunities for consolidation.
- Recommended final location.

**IMPORTANT: Existing work has priority over creating new work.**

Do not rebuild functionality unnecessarily when an existing implementation can be recovered or improved.

---

# PHASE 4 — COMBINE ALL SCATTERED FILES BY FEATURE

THIS IS THE MOST IMPORTANT TASK.

The current repository may contain multiple directories implementing different parts of the same feature.

Your responsibility is to discover these relationships and consolidate them into a coherent structure.

For example, suppose the repository contains:

- A frontend component in one directory.
- An API implementation in another directory.
- Business logic in a third directory.
- Tests in an unrelated directory.
- Configuration in another location.
- Documentation somewhere else.
- An older working implementation on another branch.

These may all belong to the same logical feature.

Analyze them together.

Determine which files should be combined, which should remain separate, and which should become shared modules.

Do not simply move files based on similar filenames.

Understand imports, call graphs, runtime behavior, data flow, and architectural responsibilities.

When two implementations overlap:

1. Compare their capabilities.
2. Identify which is more complete.
3. Identify unique functionality in each.
4. Determine compatibility.
5. Preserve important behavior.
6. Integrate compatible improvements.
7. Update dependencies and references.
8. Test the resulting implementation.
9. Archive superseded versions when appropriate.

Never overwrite a more complete implementation with an inferior one merely because it is newer.

**The objective is one coherent implementation per responsibility, not multiple competing copies scattered throughout the repository.**

---

# PHASE 5 — DESIGN THE IDEAL REPOSITORY ARCHITECTURE

Do not follow the existing folder structure blindly.

Design the best architecture based on the actual project.

Use feature-based organization where appropriate.

A possible conceptual structure is:

```text
repository/
├── apps/
│   └── application-specific entrypoints
├── features/
│   ├── feature-a/
│   │   ├── components/
│   │   ├── services/
│   │   ├── logic/
│   │   ├── types/
│   │   └── tests/
│   └── feature-b/
├── packages/
│   └── reusable packages
├── shared/
│   └── shared utilities and abstractions
├── infrastructure/
├── scripts/
├── tests/
├── docs/
├── assets/
├── AnalyseFuture/
└── README.md
```

THIS IS ONLY AN EXAMPLE.

Do not force this structure onto every repository.

Choose the appropriate architecture for the actual technology, runtime, package manager, deployment environment, and scale.

Keep existing framework conventions when necessary.

Avoid unnecessary abstraction.

Avoid circular dependencies.

Avoid putting unrelated responsibilities into one enormous module.

Avoid creating hundreds of tiny directories without a clear purpose.

Ensure that each feature has an understandable location and ownership.

A new developer should be able to locate any feature quickly.

---

# PHASE 6 — PRESERVE ALL VALUABLE EXISTING WORK

Never permanently delete files merely because they look obsolete, duplicated, unfinished, or misplaced.

Create a directory named:

`AnalyseFuture/`

Use it to preserve safe, non-active material that should no longer remain in the production structure.

Suggested organization:

```text
AnalyseFuture/
├── README.md
├── repository-inventory/
├── historical-implementations/
├── duplicate-implementations/
├── incomplete-features/
├── experiments/
├── deprecated-code/
├── unused-assets/
├── recovery-notes/
├── security-reports/
├── future-ideas/
└── migration-records/
```

Adapt the structure to the actual repository.

Before archiving a file:

- Verify that the active application does not require it.
- Record its original path.
- Record why it was archived.
- Record any replacement implementation.
- Preserve its relevant history where possible.
- Check that archiving will not break imports, builds, tests, or deployment.

Never archive files containing live credentials or sensitive data without appropriate protection.

Do not copy malicious executable material into active build or deployment paths.

Do not treat `AnalyseFuture/` as a dumping ground.

Organize archived content logically so future developers can recover it.

If a file must remain in its original location for compatibility, keep it there and document the reason.

---

# PHASE 7 — IMPLEMENT THE RESTRUCTURING

After completing discovery and architecture design, begin the actual restructuring.

Your task is not merely to produce recommendations.

You must implement the approved scope of the restructuring.

Perform the following work:

1. Create the final directory structure.
2. Move files into their correct feature directories.
3. Consolidate compatible duplicate implementations.
4. Preserve unique functionality.
5. Repair imports and exports.
6. Repair module references.
7. Update configuration paths.
8. Update build scripts.
9. Update package manifests where necessary.
10. Update test locations and references.
11. Update asset references.
12. Update CI/CD workflows.
13. Update deployment configuration where necessary.
14. Repair broken internal links.
15. Remove obsolete active references.
16. Archive superseded safe material under `AnalyseFuture/`.
17. Preserve working functionality throughout the migration.

Use incremental commits when useful.

Prefer `git mv` for straightforward moves.

Do not introduce unrelated large-scale rewrites.

Do not install arbitrary dependencies without justification.

Do not change public APIs or database schemas unnecessarily.

If compatibility changes are unavoidable, document them and provide migration guidance.

---

# PHASE 8 — VERIFY EVERY FEATURE

After restructuring, verify the repository.

Run the checks supported by the actual project:

- Dependency installation validation.
- Formatting checks.
- Static analysis.
- Linting.
- Type checking.
- Unit tests.
- Integration tests.
- Build tests.
- Application startup checks.
- API compatibility tests.
- Database migration checks.
- GitHub Actions validation.
- Security scans.

Where possible, compare behavior before and after restructuring.

Check that:

1. Previously working features still work.
2. Imports resolve correctly.
3. Shared modules remain accessible.
4. Assets load correctly.
5. Configuration files point to valid locations.
6. Tests reference the correct implementations.
7. CI workflows remain functional.
8. Deployment configuration is consistent.
9. No feature was accidentally lost.
10. Archived material is excluded from production execution.

If a check cannot run because credentials, infrastructure, or dependencies are unavailable, report that limitation explicitly.

Never claim a feature works without evidence.

---

# PHASE 9 — CREATE COMPLETE PROJECT DOCUMENTATION

Create or update documentation describing the actual repository.

Include:

## A. Project Overview

Explain what the project currently does, based on evidence from the code.

## B. Architecture

Explain major components, modules, services, and their relationships.

## C. Complete Feature Inventory

List all discovered features and their implementation status.

## D. Directory Structure

Explain the purpose of each important folder.

## E. Dependency Map

Document internal and external dependencies.

## F. Setup and Execution

Provide accurate installation, configuration, development, testing, and deployment instructions.

## G. Recovery Report

Document what was recovered, consolidated, repaired, or archived.

## H. Security Findings

Document confirmed issues, suspicious findings, and unresolved risks separately.

## I. Remaining Technical Debt

Explain unfinished work and unresolved architectural problems.

## J. Developer Continuation Guide

Provide instructions so another coding agent or developer can continue without repeating the entire investigation.

Do not invent capabilities that do not exist.

---

# PHASE 10 — UNIVERSAL FUTURE PROJECT VISION

After understanding the actual repository, independently develop a detailed future vision.

Do not assume the project belongs to any particular industry.

Derive its purpose from existing code, documentation, and demonstrated functionality.

Create:

`AnalyseFuture/PROJECT_VISION_AND_FUTURE_ROADMAP.txt`

This must be a detailed, plain-text document.

Include:

1. What the project currently is.
2. What it was originally intended to become, if evidence exists.
3. What has already been implemented.
4. What makes the project useful.
5. What is missing.
6. What should be improved immediately.
7. What should be built next.
8. What could make the project significantly better.
9. What advanced capabilities could be explored.
10. What AI capabilities could meaningfully improve the product.
11. What technologies should be researched.
12. What can realistically be built today.
13. What is technically possible but expensive or difficult.
14. What is currently impractical.
15. What depends on future research or infrastructure.
16. What could be investigated in one year.
17. What could be investigated in two years.
18. What could be investigated over three to five years.
19. What features should not be pursued and why.
20. What long-term competitive advantages could be developed.

Distinguish clearly between:

- Existing and verified.
- Existing but broken.
- Technically feasible now.
- Feasible with additional resources.
- Experimental.
- Speculative.
- Currently infeasible or unsupported.

Do not claim that future AI breakthroughs are guaranteed.

Provide a realistic roadmap based on technical dependencies, engineering effort, cost, and expected value.

The future vision should be ambitious but grounded in evidence.

---

# PHASE 11 — REQUIRED REPOSITORY REPORT FILES

Create the following files, adapting their contents to the actual project:

```text
AnalyseFuture/
├── REPOSITORY_AUDIT.txt
├── COMPLETE_FILE_INVENTORY.txt
├── FEATURE_INVENTORY.txt
├── DUPLICATE_ANALYSIS.txt
├── SECURITY_AUDIT.txt
├── ORIGINAL_TO_NEW_PATH_MAPPING.txt
├── CONSOLIDATION_REPORT.txt
├── ARCHIVED_FILES_MANIFEST.txt
├── PROJECT_VISION_AND_FUTURE_ROADMAP.txt
├── TECHNICAL_DEBT.txt
├── TEST_AND_VALIDATION_REPORT.txt
├── MIGRATION_SUMMARY.txt
└── NEXT_DEVELOPER_INSTRUCTIONS.txt
```

Each document must contain real findings, not generic placeholder text.

The file inventory should account for every relevant tracked file.

The path mapping must identify moved or consolidated files.

The consolidation report must explain what was combined and why.

The archived-files manifest must explain what was preserved outside the active application.

The validation report must distinguish passed, failed, and unexecuted checks.

---

# PHASE 12 — DIRECT GITHUB MAIN-BRANCH DELIVERY

The requested delivery workflow is:

**Push directly to the `main` branch. Do not create a pull request.**

However, repository safety and recoverability are mandatory.

Before modifying the branch:

1. Confirm that this is the intended repository.
2. Confirm that the user has authorized direct writes to `main`.
3. Fetch the latest remote state.
4. Inspect branch protection and repository permissions.
5. Create a recoverable backup reference or snapshot.
6. Record the starting commit SHA.
7. Ensure no concurrent uncommitted work will be overwritten.

Do not force-push.

Do not rewrite published history.

Do not bypass branch protection.

Do not delete existing branches or tags.

If security findings indicate that writing would create additional risk, stop the push and explain the blocker.

After restructuring:

1. Review the complete diff.
2. Check for accidentally added secrets.
3. Verify all required documentation.
4. Run available tests.
5. Confirm the final structure.
6. Commit the changes.
7. Push directly to `main` when permitted and safe.
8. Confirm that the remote branch contains the expected commit.
9. Report the final commit SHA.

If direct pushing is blocked by permissions or branch protection, do not falsely claim success.

Leave a ready-to-review commit or patch and explain the blocker.

---

# PHASE 13 — CONTINUITY AND EFFICIENT EXECUTION

This project may be too large to complete in one execution session.

Work systematically.

Do not waste the entire execution budget on repeated planning.

Use this order of priority:

1. Security and recoverability.
2. Complete repository inventory.
3. Feature identification.
4. File consolidation.
5. Directory restructuring.
6. Dependency and reference repairs.
7. Testing and validation.
8. Documentation.
9. Future roadmap.
10. GitHub delivery.

Maintain a persistent progress file:

`AnalyseFuture/WORK_PROGRESS.txt`

Record:

- Completed tasks.
- Current task.
- Pending tasks.
- Important decisions.
- Files already processed.
- Remaining directories.
- Known blockers.
- Validation status.
- Next recommended actions.

If execution time is limited, preserve completed work and continuation instructions before stopping.

Never claim the entire repository has been analyzed when substantial sections remain unexplored.

---

# FINAL ACCEPTANCE CRITERIA

The task is complete only when:

- Every relevant tracked file has been inventoried.
- Every meaningful feature has been identified.
- Scattered implementations have been evaluated for consolidation.
- The active repository follows a coherent architecture.
- Files are grouped according to their actual responsibilities.
- Valuable historical work has been preserved.
- Suspicious material has been handled safely.
- Imports and configuration references have been updated.
- Available validation checks have been executed.
- Remaining failures and limitations have been documented.
- The `AnalyseFuture/` directory contains meaningful recovery records.
- The future project vision exists as a detailed `.txt` file.
- Another developer can understand and continue the project.
- The verified changes have been pushed directly to `main`, or an explicit blocker has been reported.

# FINAL RESPONSE FORMAT

At the end, provide:

1. **Repository analyzed:** repository name and URL.
2. **Starting commit:** original SHA.
3. **Files discovered:** total count.
4. **Features discovered:** total count.
5. **Files moved:** total count.
6. **Files consolidated:** total count.
7. **Files archived:** total count.
8. **Security findings:** confirmed issues and unresolved concerns.
9. **Final architecture:** updated folder tree.
10. **Tests:** passed, failed, and not run.
11. **Documentation:** generated file paths.
12. **GitHub delivery:** pushed or blocked.
13. **Final commit:** SHA, if pushed.
14. **Remaining work:** prioritized checklist.

# MOST IMPORTANT INSTRUCTION

DO NOT ONLY ANALYZE.

DO NOT ONLY WRITE A PLAN.

DO NOT RANDOMLY MOVE FILES.

DO NOT DELETE VALUABLE EXISTING WORK.

DO NOT REBUILD FEATURES THAT ALREADY EXIST WITHOUT JUSTIFICATION.

**UNDERSTAND THE ENTIRE REPOSITORY, COMBINE RELATED IMPLEMENTATIONS, ORGANIZE EVERY FEATURE INTO A COHERENT STRUCTURE, PRESERVE EXISTING WORK, VERIFY THE RESULT, DOCUMENT EVERYTHING, AND DELIVER THE VERIFIED CHANGES TO MAIN.**

BEGIN WITH REPOSITORY DISCOVERY AND CONTINUE THROUGH IMPLEMENTATION.
