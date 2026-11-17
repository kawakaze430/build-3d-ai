# Build 3D AI — Future Model Research and Fine-Tuning Program

**Research plan · 17 November 2026 · status: proposed, not executed.** The owner wants to develop specialized model capability for image/text/multi-image → 3D assets and environments, alongside the broader creation studio. This file records how to research, select, evaluate and, when justified, fine-tune a model. It does not report a trained model, launch a job or approve resources.

**Current delivery policy:** Fetch/record current `main`; preserve existing work; verify each bounded milestone; commit and push directly to `origin/main`; verify the remote SHA before continuing. No default branch or PR is required. Never force-push or bypass protections. The prior 28-card handoff is published at `7992107b613c680dee2a750045b6b7e1ff42e581`; current delivery is discoverable from Git refs. The expanded-goal/research checkpoint was pushed and verified at `e878e8ff4ef06f68b7a06648b8ad887ead882411`. The following documentation checkpoint integrates the capability/structure/test plan and cross-links these15research tasks. No runtime tests or training ran for either documentation milestone.

Start with the [current project status and task handoff](PROJECT_STATUS_AND_TASKS.md), [adopted main goal](docs/project/BUILD_3D_AI_PROJECT_IDEA.txt), [existing model/data strategy](docs/research/AI_MODELS_AND_DATA.md), [license matrix](docs/research/LICENSE_MATRIX.md) and [benchmark protocol](docs/project/BENCHMARKS.md). Keep these documents consistent rather than replacing existing work. Implement research infrastructure through focused verified commits pushed directly to `origin/main`; preserve originals, notices, results and failed experiments.

## Research objective and first decision

Build useful, independently controlled specializations on legally usable base models, with measurable gains in supported 3D workflows. A fine-tuned checkpoint should help users obtain accepted assets with less correction, adequate control and sustainable total cost. It should not merely produce a more attractive reference-facing render.

**First choose one bounded research task, one qualified base and one evaluation protocol.** For example, investigate a constrained stylized-prop geometry failure observed in the first real baseline, or a supported adult-character proportion/style failure. Do not begin by training a foundation model from scratch, tuning every module at once, or assuming one checkpoint will solve objects, face rigs, motion, editable worlds and an AI assistant.

Image-conditioned geometry, text conditioning, multi-view consistency, material generation, rig prediction, motion and world representation may need different models and deterministic tools. A system can own its product orchestration and permitted adaptations without owning upstream weights exclusively. Choosing a base, claiming model ownership and approving commercial deployment are separate decisions.

## What already exists and what is missing

| Area | Existing foundation | Remaining research/execution gap |
|---|---|---|
| Product execution and provenance | Tenant API, durable fenced worker, model-approval snapshots, private artifacts, checksums, job inputs and browser viewer | No genuine model generation result or trained custom checkpoint has been established by the existing software tests |
| Candidate preparation | [TripoSR candidate](services/generation/triposr_candidate/): exact source/blob guards, local configs, checkpoint size/hash guard, offline intent and source preparation tests | Inference qualification only; complete runtime/rights review, built GPU runtime, real inference and training recipe remain unverified |
| Dependency evidence | Offline pip-resolution auditor, pinned direct requirements and partial license/dependency inventory | Index metadata is not independently inspected artifact bytes; full transitive/native/OS/weight/data evidence remains open |
| Software acceptance | [Dated 253-execution validation](AnalyseFuture/validation/2026-11-17/REPORT.md), GLB parser/packager, API/storage/browser contracts | Fixtures do not prove model quality, training stability, GPU feasibility, real S3, real generated output or Blender deformation |
| Product/data research | [AI model/data strategy](docs/research/AI_MODELS_AND_DATA.md), [reuse findings](docs/research/REUSE_AUDIT.md), [benchmark plan](docs/project/BENCHMARKS.md) | No accepted first-party training dataset, end-to-end fine-tuning harness or measured adaptation gain is claimed |
| Preservation | Inactive upstream source, diagrams, samples and earlier work in `AnalyseFuture/` | A bundled model, training script, wheel or sample is not automatically usable data/code or a qualified training environment |

The immediate engineering dependencies remain the main handoff's BE-01–BE-04 qualification chain, OPS-01 artifact reproducibility, OPS-02 isolated operations, OPS-03 evaluation and OPS-06 resource controls. CPU research specifications and harmless fixture tests can progress before GPU approval. Real training follows the relevant evidence/resource gates.

## Hypotheses to investigate

These are candidate studies, not commitments that fine-tuning will work or that an external vendor provides an equivalent open model. Choose one study before collecting data or reserving compute.

| Track | Testable hypothesis | Necessary comparison and limits |
|---|---|---|
| Geometry specialization | A permitted model-specific adaptation reduces a known class of thin-part, shape or rear-view errors for a constrained object category | Compare untouched base, controlled preprocessing/postprocessing and adaptation on unseen assets; distinguish reconstruction accuracy from plausible invented geometry |
| Text conditioning | A supported native text model or clearly labeled text→image→3D chain improves prompt/style adherence without harming geometry | Retain prompt/intermediate image lineage; compare the same pipeline and inputs; tuning a 2D stage alone does not establish a trained 3D model |
| Multi-image consistency | A base with genuine multi-view conditioning uses added views to improve geometry/identity consistency | Require model support and camera/input policy; compare one versus several views on the same held-out assets; more rendered views in training do not by themselves create multi-input inference |
| Materials and appearance | A supported texture/material adaptation improves seams, map consistency or style on a constrained asset class | Hold geometry/view/render conditions controlled; evaluate albedo/normal/roughness/metalness as individually supported; prettier lighting is not better PBR data |
| Stylized adult characters | Licensed, identity-grouped examples improve adult proportions, clothing/style consistency or supported facial geometry | Score front/side/back, repeated generations and unseen identities; facial rigging, eye mechanics, visemes and corrective deformation remain separate downstream pipelines |
| Environment assets and layouts | A suitable asset/layout/scene representation improves coherent reusable props or editable spatial layout | Evaluate physical scale, object separation, collisions and scene editability; a splat/radiance world is a different representation from a polygon scene and may require a different model |
| Rig/skin assistance | A separately qualified rigging model or geometric method reduces manual fitting/skin correction | Compare against reviewed deterministic/template methods, measure deformation/retarget/import; generic geometry LoRA is not an auto-rigging training recipe |
| Agent assistance | A qualified language/vision model may help explain inputs, plan bounded operations or assess outputs | First use reviewed prompting/tool contracts and evaluation; fine-tune an agent only if a measured deficiency and licensed traces justify it. The agent cannot authorize its own spending, training, deletion or publication |

Often a template, better input preparation, deterministic mesh/UV operation, retrieval or a more appropriate base will be cheaper and more reliable than training. Record those baselines before selecting an adaptation method.

## Base-model selection matrix

The following entries summarize **dated repository research**, primarily [LICENSE_MATRIX.md](docs/research/LICENSE_MATRIX.md), [REUSE_AUDIT.md](docs/research/REUSE_AUDIT.md) and the [candidate manifest](services/generation/triposr_candidate/runtime_manifest.json). They are not a new live model survey or approval. Recheck exact source, checkpoint, training recipe and terms when a study starts.

| Candidate/family | Existing evidence | Training/adaptation evidence | Rights/runtime decision today | Compute/quality evidence |
|---|---|---|---|---|
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR) | Source `107cefdc244c39106fa830359024f6a2f1c78871`; model revision `2ba2f5591f8eb0821784764ab9ab99a12e1abb08`; guarded inference candidate | A usable model-specific fine-tuning recipe, target modules, losses and data representation have **not** been qualified here | Top-level source/model MIT labels are promising; transitive runtime/data decision remains open. Candidate is research-only | Real inference quality/VRAM and training memory/time are unmeasured here; no training estimate inferred from checkpoint size |
| [Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) | Dated reuse review records `train.py` and `system.use_lora=True` | Documented command is a lead, not proof it trains correctly in our permitted environment | Stock runtime includes noncommercial nvdiffrast and is rejected for the intended commercial path; a replacement runtime needs a new exact-tree audit | No project training run or measured fit/quality/cost; do not adopt just because LoRA is mentioned |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | Dated source-level study identifies generation and renderer dependencies | Official recipe, model/data rights and supported adaptation still need exact-revision research | Standard NVIDIA renderer path is not cleared commercially; any permitted replacement requires separate review | No accepted project training/benchmark result |
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | MIT-labeled main source/weights, separately licensed derived components and default preprocessing documented in the audit | Research separately; no accepted fine-tuning recipe in this project | Default worldwide runtime rejected in the dated audit because of restricted dependencies/terms; do not select it without resolving the exact affected tree | Training feasibility and output gains unknown |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) / [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) | Specialist rigging/skin research candidates in existing matrix | Investigate only for a separate rig/skin study, not as a general geometry base | Source labels do not settle pretrained-weight, data and dependency rights; research-only | No qualified training/runtime/Blender deformation evidence here |
| Other future maintained base | Identify through a dated official source/paper/model card and reproducible exact artifacts | Require supported training code, representation/loss details, parameter-efficient compatibility and evaluation access | Must fit source/weights/data/derivative/SaaS/geography/distribution requirements | Measure a controlled inference baseline and memory profile before proposing a training budget |

For every candidate, fill: exact code/model revisions and byte hashes; model type/input/output representation; real single/text/multi-input support; training recipe/reproducibility; source/weight/data/dependency/derivative terms; notices and redistribution rights; security/loading format; required hardware; observed quality/failures; integration effort and maintenance. Unknown fields stay **unknown**. Reject or defer a candidate whose prerequisites do not fit the intended product.

Do not scrape proprietary model weights, bypass service access or harvest competitor/customer outputs for training without explicit applicable rights and terms. Product feature inspiration is not a training-data license. Use paid external evaluation only under an authorized account, current terms and a separate spend cap.

## Dataset contract and preparation

### Per-asset provenance before inclusion

Keep a versioned manifest with a stable asset/family/identity ID, source, original file hashes, creator/rightsholder, source/license evidence and date, commercial training and derivative permissions, attribution, consent where needed, data version, transforms and split. Record rights for **textures, source images, meshes, motions and annotations separately** when they differ. Publicly downloadable does not mean licensed for training or redistribution.

Example schema outline below uses explicit unknown values; it is not a permission record or data already collected:

```json
{
  "asset_id": "example-placeholder",
  "family_id": "same-underlying-asset-and-derivatives",
  "identity_id": null,
  "source_url": null,
  "source_revision": null,
  "original_sha256": null,
  "rights": {
    "license_id": "UNKNOWN",
    "evidence_reference": null,
    "commercial_training": false,
    "derivative_weights_distribution": false,
    "asset_redistribution": false,
    "attribution": null,
    "consent_reference": null,
    "expiry_or_revocation_policy": null
  },
  "representation": null,
  "units_and_axes": null,
  "parent_assets": [],
  "transform_config_sha256": null,
  "split": "quarantine",
  "review_state": "NOT_APPROVED"
}
```

Customer uploads are **not training data by default**. A future opt-in must distinguish service processing, public sharing, research, training, retention and withdrawal consequences. Do not place private customer files, consent records, personal identifiers, credentials or raw proprietary datasets in public Git. Version public manifest schemas and permitted aggregate evidence; keep restricted artifacts in approved private storage.

### Quality and representation rules

- Define supported formats, finite geometry, scale/axes, topology/material requirements, texture resolution, camera intrinsics/extrinsics and missing-data policy for the selected model. Test normalization and reconstruction/export round trips on small controlled fixtures.
- Bound file and decoded resources; sandbox converters/renderers. Do not run embedded `.blend` scripts, untrusted Python installers or arbitrary checkpoint pickles during ingestion. Preserve raw originals separately from derived training representations.
- Identify corrupt, mislabeled, empty, duplicate and near-duplicate assets. Keep exclusion reasons. Hash preprocessing code/config and intermediate outputs so a new pipeline version cannot silently change the dataset.
- Split by underlying **3D asset, derivative family and character identity before creating views/augmentations**. All cameras, material variants, remeshes, LODs, animation frames and near-duplicate derivatives of one family stay in one split. Keep a locked test set independent of training/validation/hyperparameter decisions.
- Balance categories and intended styles using documented sampling, not a convenient heap of views. Measure data coverage and rights coverage separately; a million renders of a few assets are not a million independent examples.

## Evaluation and success criteria

Freeze the protocol before training. Select a primary product metric and guardrails appropriate to the study; numerical thresholds are proposed and accepted in its experiment plan, not invented as observed scores. The existing [benchmark document](docs/project/BENCHMARKS.md) proposes a 100-item evaluation and 95%+ valid-job aspiration; neither is an achieved model result.

| Dimension | Record/compare |
|---|---|
| Accepted-asset utility | Blind human rubric where possible, category breakdown, downstream usability and artist correction minutes; include failures in the denominator |
| Geometry | Import success, finite/valid representation, rear/side consistency, thin parts, disconnected pieces, normals, triangle counts and measured shape error only where licensed ground truth supports it |
| Appearance | UV seams, texture alignment/resolution, supported PBR maps, material consistency across several controlled views; separate lighting from albedo quality |
| Character support | Adult proportions, identity/style stability, clothing/hair/face detail; separate body/face deformation and speech-rig acceptance |
| Multi-view/environment support | True input-view use, camera/scale consistency, object/layout separation and editable scene/representation limits |
| Reliability | All attempts, failures, invalid outputs, timeouts, determinism limits, regression by category and safety/trust boundary failures |
| Economics/performance | Preprocess/render/training/evaluation/storage/transfer cost, GPU-hours, wall time, peak VRAM, inference P50/P95 where sample size permits and total cost per accepted asset |
| Reproducibility | Source/data/config/environment/base/checkpoint/output hashes, seed, hardware/driver, exact command and known nondeterminism |

Compare at least the untouched base and the adaptation using the same held-out inputs and evaluation policy. Where useful, compare a no-training preparation/postprocessing or template baseline. Do not tune on the locked test set, cherry-pick successful renders, reuse leaked identities, silently remove failed samples or claim improvement from a changed renderer alone. An improvement must exceed the protocol's stated uncertainty and preserve agreed quality/cost/privacy guardrails.

## Method and resource decision

| Method | When it might fit | Evidence needed before a real experiment |
|---|---|---|
| No training: preprocessing, prompting, retrieval, templates or postprocessing | Baseline errors are input/control/topology/rig integration issues rather than missing learned capability | Controlled comparison showing whether the cheaper intervention solves the measured problem |
| LoRA/adapters or partial freezing | The chosen architecture/training code actually supports useful trainable targets and losses | Exact target modules, parameter count, forward/backward/merge/reload behavior, model-specific preprocessing and measured memory profile; generic image-LoRA commands are insufficient |
| Full fine-tune | Small adaptation underfits a justified capability and supported data/compute fit the plan | Optimizer/state/activation memory, training stability, base-regression risk, reproducible resume and a larger separately approved budget |
| Distillation or synthetic supervision | A permitted teacher/dataset provides suitable targets and rights allow training/derivatives | Teacher/output terms, lineage, quality filtering, independent held-out evaluation and no prohibited competitor-output harvesting |
| Preference/reward or reinforcement learning | A reliable reward/preference dataset and a genuine measured failure justify the added complexity | Reward validity/leakage/gaming tests, safety/cost bounds and comparison against simpler supervised adaptation; not the first training step |
| Training from scratch | Only if much later evidence, rights, team, data and economics justify a separate program | A separate feasibility/research decision; not part of the initial project plan |

Training memory is not inference memory. Profile parameters, gradients, optimizer state, activations, precision, geometry/view/texture resolution, batch size and effective accumulation on the exact model/environment. Quantization, offloading, distributed sharding and checkpointing are optional design choices whose correctness and cost must be tested; they are not guarantees that an unknown model fits a small GPU.

Before a run, estimate and approve:

```text
total envelope = data/preprocessing/rendering + artifact transfer/storage
               + training GPU hours × current all-in provider rate
               + evaluation/failed-attempt allowance + shutdown/idle overhead

maximum trials: <approved bounded count>
maximum wall time/GPU-hours/total spend: <explicit approved values>
provider/account/region/GPU/storage/quota: <verified values>
checkpoint interval and recovery storage: <measured design>
stop/termination authority and cleanup: <named owner/procedure>
```

Record assumptions/rate date and distinguish estimate, provider-authorized ceiling and observed charge. No numeric hardware, quality, timeline or cost claim is supplied here because the training task/base/recipe are not yet selected and measured. Existing cloud credits or an inference budget proposal do not authorize a training run. No indefinite agent-driven sweeps are permitted.

## Bounded experiment ladder

1. **CPU specification and harness:** Resolve the study question, rights/matrix, schemas, split/leakage tests, evaluator contracts and reproducible environment plan using harmless fixtures. No weights or paid compute required.
2. **Qualified untouched inference baseline:** After exact runtime/rights and bounded resource authorization, run permitted unseen inputs through the existing product acceptance path. Keep failed outcomes and real artifacts. If no base works, fix/reject the base before training.
3. **Training feasibility:** Review a genuine model-specific recipe, profile one approved bounded forward/backward/resume path and verify target/optimizer/checkpoint behavior. A synthetic loss decreasing proves plumbing only, not production learning.
4. **Small approved adaptation experiment:** Use a predeclared subset/trial count, fixed validation protocol and stop conditions. Save source/data/config/checkpoint/cost lineage. Record a negative result honestly.
5. **Controlled comparison and ablation:** Compare base versus adaptation and the relevant simpler baseline; vary one useful factor at a time within the approved trial budget. Lock selection before testing once on the held-out set.
6. **Independent downstream acceptance:** Inspect real textured outputs in the private viewer and Blender; run support-specific geometry/material/rig or scene checks. Review category failures, artist correction effort and full inference cost.
7. **Private pilot, registry and rollback:** Only after rights/security/quality/cost acceptance, register the adaptation alongside its exact base, stage a small approved pilot and retain the known-good version/disable path. Public release or larger training is a separate decision.

Stop on rights ambiguity, unsafe artifact drift, unexpected downloads, repeated corrupt/invalid outputs, uncontrolled VRAM/storage/cost, nonfinite loss, checkpoint inconsistency, leakage or a predeclared no-improvement condition. Preserve diagnosis and recoverable authorized artifacts; stopping a client process is not proof that remote compute stopped.

## Research task register

Every card below is **open**. IDs are proposed research work units, not existing issues or claims of implementation. Each should produce a focused commit/evidence record; real runs remain gated as specified.

| Task | Research outcome |
|---|---|
| [RES-01](#res-01) | Choose one research question and supported user outcome |
| [RES-02](#res-02) | Audit base models and real training recipes |
| [RES-03](#res-03) | Clear the exact source, weights, data and derivative-use chain |
| [RES-04](#res-04) | Implement a versioned dataset rights/provenance manifest |
| [RES-05](#res-05) | Build deterministic, bounded model-specific preprocessing |
| [RES-06](#res-06) | Lock asset/identity-disjoint splits and leakage checks |
| [RES-07](#res-07) | Record the untouched real baseline and evaluation protocol |
| [RES-08](#res-08) | Select adaptation targets and measure the resource envelope |
| [RES-09](#res-09) | Implement the reproducible training-run and resume contract |
| [RES-10](#res-10) | Run one small explicitly approved adaptation experiment |
| [RES-11](#res-11) | Evaluate controlled ablations and one locked held-out comparison |
| [RES-12](#res-12) | Validate the real downstream asset and supported domain |
| [RES-13](#res-13) | Review model/data privacy, loading safety and release rights |
| [RES-14](#res-14) | Register the qualified adaptation and prove rollback |
| [RES-15](#res-15) | Maintain the research log, re-evaluation and next-study decision |

<a id="res-01"></a>

### RES-01 — Choose one research question and supported user outcome

- **Owner/scope:** ML engineer, product owner and technical artist; select one hypothesis/asset family and failure mode from a genuine baseline or clearly mark the baseline pending.
- **Deliverable:** Study charter with task/input/output envelope, one primary metric, quality/cost guardrails, non-goals, comparator, owner and stop/exit decision.
- **Acceptance/tests:** Another reviewer can determine what would falsify the hypothesis and distinguish a geometry/material/rig/agent result. No universal “all features” checkpoint or unmeasured quality claim.
- **Dependencies/gates:** CPU design ready; measured baseline belongs to RES-07 and BE-04/OPS-03 before a training benefit can be claimed.

<a id="res-02"></a>

### RES-02 — Audit base models and real training recipes

- **Owner/scope:** ML/release engineer; compare exact permitted candidates using the matrix above and official code/model/paper evidence, including maintainability and supported target representation.
- **Deliverable:** Dated candidate matrix, exact revisions/hashes, verified recipe paths, data/loss/target-module contract, unsupported/unknown fields and selection/rejection rationale.
- **Acceptance/tests:** A training entrypoint and data contract are actually inspected; inference-only support or a LoRA option is not asserted to be a working training recipe. TripoSR's existing qualification does not auto-select it for training.
- **Dependencies/gates:** RES-01; source/doc review can start now. Artifact/large download and runtime probes need their resource/rights approval.

<a id="res-03"></a>

### RES-03 — Clear the exact source, weights, data and derivative-use chain

- **Owner/scope:** Release/licensing reviewer with the owner; extend existing `LICENSE_MATRIX.md` and `REUSE_AUDIT.md` for the selected experiment, rather than relabeling all candidates approved.
- **Deliverable:** Exact source/weights/model-card/training-data/dependency/runtime notices and terms, commercial/SaaS/geographic/redistribution/derivative obligations, unresolved questions and explicit disposition.
- **Acceptance/tests:** Required permissions can be evidenced for the intended experiment and deployment/distribution mode; unknown or incompatible terms block that dependent action. Top-level permissive code does not clear weights/data/native libraries.
- **Dependencies/gates:** RES-02 and BE-02/OPS-01; research-only status remains until the appropriate review decision.

<a id="res-04"></a>

### RES-04 — Implement a versioned dataset rights/provenance manifest

- **Owner/scope:** Data/ML engineer; define per-asset/family/identity provenance, separate component rights, lineage, consent reference, permitted uses and quarantine state.
- **Deliverable:** Schema, manifest validator, harmless sample fixtures and approved private/public evidence storage policy. Actual dataset storage is separately scoped.
- **Acceptance/tests:** Unknown/missing rights and invalid/missing hashes cannot enter an approved training manifest; derived assets retain parents and restrictions. Tests cover mixed mesh/texture rights, duplicates, revocation/expiry and private fields excluded from public evidence.
- **Dependencies/gates:** RES-01/03; no customer uploads or external bulk dataset collection authorized by the schema PR.

<a id="res-05"></a>

### RES-05 — Build deterministic, bounded model-specific preprocessing

- **Owner/scope:** Graphics/data engineer; implement only the selected representation's validation, units/axes, geometry/material normalization, camera/view generation and annotations.
- **Deliverable:** Versioned transform configs, bounded/sandboxed conversion plan, hash-linked derived manifest and exclusion report; retain permitted originals unchanged.
- **Acceptance/tests:** Controlled fixtures round-trip the declared geometry/material/camera convention; corrupt/empty/unsupported/over-budget inputs fail clearly; reprocessing the same version gives the declared deterministic result or records nondeterminism. No embedded script or arbitrary pickle executes.
- **Dependencies/gates:** RES-02/04; CPU fixtures ready. GPU rendering, Blender runtime and large derived datasets need separate reviewed execution/resources.

<a id="res-06"></a>

### RES-06 — Lock asset/identity-disjoint splits and leakage checks

- **Owner/scope:** Data/QA engineer; group original assets, derivatives, viewpoints, LODs, frames, styles and identities before rendering/augmentation.
- **Deliverable:** Frozen train/validation/test manifests, grouping/dedup algorithm and contamination report; a private held-out test set inaccessible to training selection.
- **Acceptance/tests:** A fixture with different views, filenames, remeshes or animation frames of one family cannot leak across splits; near-duplicate candidates are reviewed and logged. Split seed/version and test-access policy are recorded.
- **Dependencies/gates:** RES-04/05; no live training needed to validate split logic.

<a id="res-07"></a>

### RES-07 — Record the untouched real baseline and evaluation protocol

- **Owner/scope:** QA/ML engineer and artist; use OPS-03's versioned evaluator and BE-04's actual product artifact path. Include base failure/category/cost evidence.
- **Deliverable:** Locked rubric, representative permitted input manifest, raw attempt/output records and baseline report with several views/downstream checks.
- **Acceptance/tests:** Results are reproducible within stated limits; failures stay counted; user utility and technical import are separate. Protocol/aggregation tests use CPU fixtures; real model quality requires genuine approved output.
- **Dependencies/gates:** RES-01–03/06, qualified runtime and explicit bounded inference resources. No baseline or benchmark success is fabricated while blocked.

<a id="res-08"></a>

### RES-08 — Select adaptation targets and measure the resource envelope

- **Owner/scope:** ML/platform engineer; compare no-training controls, supported adapters/partial freeze and full tuning for the chosen architecture.
- **Deliverable:** Exact trainable modules/parameter count, loss/optimizer/precision plan, artifact/environment lock, memory accounting and bounded feasibility experiment/budget proposal.
- **Acceptance/tests:** Forward/backward and adapter merge/reload or full-checkpoint behavior are meaningful for the target model; measured training memory—not inference claims—supports the proposal. A generic image-LoRA command cannot close the task.
- **Dependencies/gates:** RES-02/03/07; source/design ready. GPU profiling and large artifacts require explicit scope and resource authorization.

<a id="res-09"></a>

### RES-09 — Implement the reproducible training-run and resume contract

- **Owner/scope:** ML/release engineer; propose a separately owned training environment/module, not another production queue or auth system. First deliver configuration/schema/fixture behavior.
- **Deliverable:** Run manifest, seed/environment/data/config/base references, bounded logging/checkpointing, optimizer/scheduler/RNG resume state as applicable, stop policy and artifact integrity checks.
- **Acceptance/tests:** CPU/small synthetic harness tests reject mismatched base/data/config/checkpoints, preserve a previous valid checkpoint across interruption, and resume the intended step/state. Passing harness tests is explicitly not evidence of trained 3D quality.
- **Dependencies/gates:** RES-04–08; any real model forward/backward follows the approved isolated model-specific plan.

<a id="res-10"></a>

### RES-10 — Run one small explicitly approved adaptation experiment

- **Owner/scope:** ML engineer and resource owner; execute only the predeclared bounded study/subset/trial count after prerequisite acceptance.
- **Deliverable:** Exact commands/config/data/base/runtime identifiers, checkpoints/hashes, complete loss/validation/failure records, actual resource/cost and termination evidence.
- **Acceptance/tests:** Safe load/save/resume and finite numerical behavior are demonstrated; budget/stop controls work. No gain is claimed merely because training finishes or loss decreases. A failed/no-improvement run remains a valid documented research outcome.
- **Dependencies/gates:** RES-03/06–09; written owner-approved provider/GPU/time/spend/cleanup envelope. No training is started by this task register itself.

<a id="res-11"></a>

### RES-11 — Evaluate controlled ablations and one locked held-out comparison

- **Owner/scope:** Independent QA/artist reviewer with ML owner; compare the selected adaptation, untouched base and relevant simpler control using the frozen protocol.
- **Deliverable:** Full non-cherry-picked results, category/uncertainty/regression analysis, artist correction evidence and accepted-asset/inference-cost comparison; log all trials.
- **Acceptance/tests:** No asset/identity leakage or test-set selection; changes in rendering/resolution/hardware are controlled or disclosed. Success requires the predeclared improvement and guardrails, not a single attractive output. Negative results can reject the adaptation.
- **Dependencies/gates:** RES-07/10; additional trial/evaluation spend must fit the approved envelope, otherwise remain blocked rather than expanding an automatic sweep.

<a id="res-12"></a>

### RES-12 — Validate the real downstream asset and supported domain

- **Owner/scope:** Graphics/animation artist and QA engineer; reuse GLB/package/private-download/viewer boundaries and test supported Blender imports. Select geometry, PBR, rig or environment criteria according to RES-01.
- **Deliverable:** Real held-out output/import artifacts, multi-angle renders, material/scale/geometry checks, correction time and support limits; rig/scene demonstrations only where genuinely implemented.
- **Acceptance/tests:** Exported bytes are the claimed format, materials/axes/units survive import and applicable artist tasks succeed. A fine-tuned geometry model does not automatically receive facial rig, animation, editable scene or arbitrary exporter credit.
- **Dependencies/gates:** RES-11 and the corresponding ART/ANIM/environment tasks in the main handoff; controlled Blender/render execution must be separately reviewed.

<a id="res-13"></a>

### RES-13 — Review model/data privacy, loading safety and release rights

- **Owner/scope:** Security/privacy/licensing reviewer; evaluate selected inputs/checkpoints, opt-in data flow, memorization/extraction risks appropriate to the model and obligations on derived weights.
- **Deliverable:** Threat/privacy assessment, consent/retention policy, allowed artifact formats/loaders, private-data exposure checks and a release rights/notices disposition.
- **Acceptance/tests:** Untrusted/user checkpoints cannot be loaded through a training/inference upload route; controlled negative fixtures fail closed; data/model publication excludes private uploads/credentials and honors applicable permissions. Research-only artifacts cannot silently become commercial serving defaults.
- **Dependencies/gates:** RES-03/04/09 and evidence from RES-10–12. This is a scoped review, not a claim of universal security, ownership or legal clearance.

<a id="res-14"></a>

### RES-14 — Register the qualified adaptation and prove rollback

- **Owner/scope:** ML/release/platform engineer; extend the existing exact model-policy and artifact-provenance boundaries for a qualified base+adaptation pair.
- **Deliverable:** Model card and registry record with source/base/adapter/merged-checkpoint/runtime/data/config hashes, notices/SBOM, supported inputs, observed metrics, cost, limitations, approval status and rollback target.
- **Acceptance/tests:** Wrong base/adapter/runtime combinations or corrupted bytes fail; generated assets record exact model lineage; a permitted private canary can be disabled or rolled back without losing old artifacts. A registry row alone does not approve deployment.
- **Dependencies/gates:** RES-11–13, current product/API/worker tests and separate owner-approved pilot/deployment/resources. Keep known-good models and failed experiment provenance.

<a id="res-15"></a>

### RES-15 — Maintain the research log, re-evaluation and next-study decision

- **Owner/scope:** Project/research maintainer; reconcile results with `research.md`, the root task handoff, model/data strategy, license matrix, benchmark and continuity docs.
- **Deliverable:** Dated decisions, exact PR/commit/result references, changed hypotheses, rejected alternatives, current blockers and one bounded next assignment.
- **Acceptance/tests:** Every “tested,” “improved,” “approved” or “released” status links to actual evidence and the responsible decision; missing/no-result fields remain unknown. Existing files/history are preserved, links/IDs resolve and no calendar milestone is treated as proof.
- **Dependencies/gates:** Can start now as documentation. Review after each material experiment/base/data/rights/cost change, and before any larger study. Future one-/two-year reviews reassess available evidence rather than promise another researcher will deliver a breakthrough.

## Proposed research artifact layout

These paths are **proposals, not existing implemented training modules**. Create them only in a scoped accepted infrastructure milestone, and align names with the live repository before adding files:

```text
research.md                         Current research questions, cards and decisions
docs/research/experiments/           Public non-secret protocol/model-card/report metadata
services/training/<selected-task>/   Isolated model-specific harness/configuration, if justified
tests owned beside that harness      CPU schema/split/resume/contract fixtures
approved private artifact storage    Restricted datasets, renders, logs and weight checkpoints
```

Keep inference qualification in its existing `services/generation/triposr_candidate/` boundary. Do not move raw `AnalyseFuture` trees into an active training package, copy every upstream environment into one interpreter or store large datasets/weights in Git merely to make the proposed tree real. Reuse API/worker/storage ownership and the release inventory instead of creating competing registries without a clear interface decision.

## Experiment and decision templates

### Before a run

```text
Study/task ID and hypothesis:
Owner/reviewer; base main and implementation commit/head:
Exact code/base/model/runtime revisions and independent byte hashes:
Training method, target modules/loss/config and effective batch:
Dataset version, rights evidence, family/identity split and exclusions:
Primary metric, guardrails, untouched/control baseline and fixed test policy:
Hardware/driver; estimated memory/time/storage/transfer/cost assumptions:
Authorized account/region/resources; maximum trials/runtime/total spend:
Checkpoint/resume/stop/termination and cleanup procedure:
Publication/privacy/rights decision and remaining blockers:
```

### After a run

```text
Actual command, tested commit/config/data/environment identifiers:
Started/ended; hardware; actual GPU-hours/storage/transfer/provider charge:
All outcomes/failures; checkpoints and output artifact hashes:
Validation and held-out results; uncertainty/category regressions:
Several-view/Blender/artist evidence; correction time; inference cost:
Safety/privacy/rights issues and exact actions taken:
Resources terminated; checkpoints/logs recoverable at approved location:
Decision: reject / revise hypothesis / repeat within cap / qualify private pilot:
Reviewer/date; next bounded task and unresolved approvals:
```

### Living research ledger

| Entry/date | Study/task | Evidence | Decision | Next action |
|---|---|---|---|---|
| 17 November 2026 | Future program defined; RES-01–RES-15 open | Existing source/license/model-strategy documents and dated software validation linked above | No training/base/dataset/budget selected or approved by this file | Write RES-01 charter and RES-02 exact-recipe comparison; continue the established first-real-inference qualification independently |

## Evidence and research leads

- [Main project idea](docs/project/BUILD_3D_AI_PROJECT_IDEA.txt): existing work, conditional ambitions, technical limits, data and ownership direction.
- [AI models and data](docs/research/AI_MODELS_AND_DATA.md): inference-first sequence and asset/identity split requirement.
- [License matrix](docs/research/LICENSE_MATRIX.md) and [reuse audit](docs/research/REUSE_AUDIT.md): dated exact-source/runtime/model findings and Step1X training/LoRA lead; recheck current exact terms before adoption.
- [TripoSR candidate notes](services/generation/triposr_candidate/README.md) and [manifest](services/generation/triposr_candidate/runtime_manifest.json): inference-only qualification evidence, not training suitability.
- [First real GPU runbook](docs/operations/FIRST_REAL_GPU_RUNBOOK.md), [model approval gate](docs/operations/MODEL_APPROVAL_GATE.md) and [benchmark protocol](docs/project/BENCHMARKS.md): resource/release/evaluation prerequisites.
- [Latest local software validation](AnalyseFuture/validation/2026-11-17/REPORT.md): what was actually tested; no trained model or real inference result follows from it.

New papers, official training recipes and candidate model cards should be entered with URL, access date, exact revision/artifact, reproduced result or explicit unverified status, relevance and rights limitations. Do not copy a paper's score, hardware claim or promotional example into the project's measured-results column. This program starts from existing work, keeps unknowns visible and advances only through evidence.
