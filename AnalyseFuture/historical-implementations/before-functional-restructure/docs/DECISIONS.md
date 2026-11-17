# Decision Register and Outstanding Questions

Current implementation reconciliation: 17 November 2026. The [pre-review version](../AnalyseFuture/historical-implementations/documentation-before-universal/docs/DECISIONS.md) preserves the exact document from baseline `56f412f`; historical results remain scoped to their recorded runs.

## Current decisions and implementation evidence

| Topic | Present direction | Status |
|---|---|---|
| Ambition | Independent platform competitive with Meshy/Tripo | Strategic goal |
| Repository | One owner-controlled monorepo with modular services | Accepted; existing app/package boundaries retained |
| Coding | Codex/Astra in bounded, reviewable tasks | Accepted working method; current task authorization governs delivery |
| Frontend foundation | First-party Next.js + React Three Fiber/Three.js | Accepted + implemented in PR #15; Open3DStudio inspected but not vendored |
| Private serving contract | 3DAIGC-API behind the first-party product API/worker | Contract integration implemented; actual upstream/model deployment unverified |
| First inference candidate | TripoSR exact guarded qualification path | Source preparation and resolver-metadata audit exist; full runtime/rights/GPU qualification blocked |
| Fine-tuning | Model-specific permitted recipe after measured inference baseline | No training performed; stock Step1X runtime is rejected, any replacement requires exact-tree review |
| Alternative high-quality model | TRELLIS.2 | License/dependency gate |
| Rigging | UniRig / SkinTokens | Comparative test needed |
| UV/GLB | xatlas / glTF Transform | Test and audit needed |
| GPU hosting | Owner-controlled provider; AWS remains a candidate | Budget + quota approval; no GPU launched |
| Artifact storage | Filesystem default + optional private S3-compatible backend | Quotas, scanner and copy-only migration implemented; real remote provisioning/restore and retention/deletion open |
| Identity | Private API keys plus optional API JWT/JWKS validation; Better Auth preferred for browser lifecycle | Immutable mapping/assertion validation implemented and disabled by default; public BFF/session lifecycle not implemented |
| Priority focus | First real generation vertical slice, then broader asset/animation features | Accepted critical path |
| Scenes | Editable scene workflow; splats separate | R&D |
| Security | Tenant-scoped API keys + BFF key containment + private verified artifacts | Private slice implemented/tested; public account lifecycle/audit program remains open |

## Major unresolved decisions

1. Which model + full dependencies are safe for a global commercial SaaS?
2. Which exact approved model/runtime chain should power the first real generation benchmark?
3. What GPUs and costs are available under the owner's credits and service quotas?
4. Which asset category wins the first verified quality benchmark?
5. How will Blender-compatible facial topology be produced reliably?
6. How will the product terms handle uploaded images, generated outputs and training rights?
7. What should be proprietary code versus a clearly documented imported OSS adapter?
8. Which export formats can be reliably round-tripped and supported?

## ADR policy

For every major implementation choice create an ADR noting date, problem, alternatives, verified evidence, licenses, expected cost, security, decision owner and rollback. Do not let an AI agent silently convert a research hypothesis into an accepted production dependency.
