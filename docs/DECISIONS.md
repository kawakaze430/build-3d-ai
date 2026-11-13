# Decision Register and Outstanding Questions

## Current proposed decisions (not yet implementation evidence)

| Topic | Present direction | Status |
|---|---|---|
| Ambition | Independent platform competitive with Meshy/Tripo | Strategic goal |
| Repository | One owner-controlled monorepo with modular services | Proposed |
| Coding | Codex/Astra in bounded, reviewable tasks | Proposed |
| Frontend candidate | Open3DStudio | Evaluation required |
| Backend candidate | 3DAIGC-API | Evaluation required |
| Fine-tuning candidate | Step1X-3D | Evaluation required |
| Alternative high-quality model | TRELLIS.2 | License/dependency gate |
| Rigging | UniRig / SkinTokens | Comparative test needed |
| UV/GLB | xatlas / glTF Transform | Test and audit needed |
| GPU hosting | AWS, owner-controlled infrastructure | Budget + quota approval |
| Priority focus | Broad 3D generation, then stylized animation-ready characters | Proposed |
| Scenes | Editable scene workflow; splats separate | R&D |
| Security | Auth, tenant isolation, private assets, audit trails | Required, not implemented |

## Major unresolved decisions

1. Which model + full dependencies are safe for a global commercial SaaS?
2. Which upstream frontend/backend revisions actually run together and are maintainable?
3. What GPUs and costs are available under the owner's credits and service quotas?
4. Which asset category wins the first verified quality benchmark?
5. How will Blender-compatible facial topology be produced reliably?
6. How will the product terms handle uploaded images, generated outputs and training rights?
7. What should be proprietary code versus a clearly documented imported OSS adapter?
8. Which export formats can be reliably round-tripped and supported?

## ADR policy

For every major implementation choice create an ADR noting date, problem, alternatives, verified evidence, licenses, expected cost, security, decision owner and rollback. Do not let an AI agent silently convert a research hypothesis into an accepted production dependency.
